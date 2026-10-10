"""Programación persistente de plantillas, con confirmación y ejecución conservadora."""
import json
import copy
import io
import re
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import tasks


CONFIG_KEY = 'message_schedules'
AUTORESPONSE_KEY = 'message_autoresponses'
STICKY_KEY = 'message_stickies'


async def send_report(interaction, lines, empty):
    text = '\n'.join(lines) or empty
    if len(text) <= 1900:
        await interaction.response.send_message(text, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        return
    report = discord.File(io.BytesIO(text.encode('utf-8')), filename='automatizaciones.txt')
    try:
        await interaction.response.send_message('El listado completo se encuentra en el archivo adjunto.',
                                                file=report, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
    finally:
        report.close()


def keyword_matches(content, keyword, mode):
    content, keyword = content.casefold().strip(), keyword.casefold().strip()
    if not keyword:
        return False
    if mode == 'exacta':
        return content == keyword
    return re.search(r'(?<!\w)' + re.escape(keyword) + r'(?!\w)', content) is not None


def parse_local(value, zone):
    try:
        tz = ZoneInfo(zone)
        local = datetime.fromisoformat(value)
        if local.tzinfo is not None:
            raise ValueError('Indique la fecha local sin desplazamiento; la zona se indica por separado.')
        candidate = local.replace(tzinfo=tz)
        if candidate.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != local:
            raise ValueError('Esa hora no existe en la zona indicada por el cambio de horario.')
        if candidate.utcoffset() != local.replace(tzinfo=tz, fold=1).utcoffset():
            raise ValueError('Esa hora es ambigua por el cambio de horario. Elija otra hora.')
        return candidate.astimezone(timezone.utc)
    except ZoneInfoNotFoundError:
        raise ValueError('Zona horaria IANA desconocida; puede usar UTC o America/Santo_Domingo.') from None


def next_occurrence(job, now):
    if job['repeat'] in ('trigger', 'sticky'):
        return (now + timedelta(seconds=job['cooldown'])).isoformat()
    if job['repeat'] == 'ninguna':
        return None
    tz = ZoneInfo(job['zone'])
    origin = datetime.fromisoformat(job['start']).astimezone(tz)
    days = 1 if job['repeat'] == 'diaria' else 7
    elapsed = max(0, (now.astimezone(tz).date() - origin.date()).days // days)
    candidate = origin + timedelta(days=elapsed * days)
    while candidate.astimezone(timezone.utc) <= now:
        candidate += timedelta(days=days)
    # En el salto de primavera, normaliza a la hora real posterior al salto.
    return candidate.astimezone(timezone.utc).isoformat()


class ScheduledMessages:
    def __init__(self, host):
        self.host = host
        self.ready = False

    def jobs(self, guild_id, key=CONFIG_KEY):
        try:
            value = json.loads(self.host['guild_config_get'](guild_id, key) or '[]')
            return value if isinstance(value, list) else []
        except (TypeError, ValueError):
            return []

    def initialize(self):
        conn = self.host['db_connect']()
        try:
            conn.execute('''CREATE TABLE IF NOT EXISTS message_schedule_state (
                guild_id INTEGER NOT NULL, job_id TEXT NOT NULL, next_run TEXT,
                status TEXT NOT NULL DEFAULT 'pending', message_id INTEGER,
                detail TEXT, dirty INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(guild_id, job_id))''')
            if 'dirty' not in {row[1] for row in conn.execute('PRAGMA table_info(message_schedule_state)')}:
                conn.execute('ALTER TABLE message_schedule_state ADD COLUMN dirty INTEGER NOT NULL DEFAULT 0')
            conn.execute('''CREATE TABLE IF NOT EXISTS message_autoresponse_rate (
                guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL, until_at TEXT NOT NULL,
                PRIMARY KEY(guild_id, channel_id))''')
            # Un envío interrumpido podría haber llegado a Discord. No repetir a ciegas.
            conn.execute("UPDATE message_schedule_state SET status='uncertain', detail=? WHERE status='sending'",
                         ('Envío interrumpido. Revise el canal y cree una nueva programación si corresponde.',))
        finally:
            conn.close()
        self.ready = True

    def start(self):
        if not self.worker.is_running():
            self.initialize()
            self.worker.start()

    def state(self, guild_id, job):
        conn = self.host['db_connect']()
        try:
            conn.execute('INSERT OR IGNORE INTO message_schedule_state (guild_id,job_id,next_run) VALUES (?,?,?)',
                         (guild_id, job['id'], job['start']))
            return conn.execute('SELECT next_run,status,detail FROM message_schedule_state WHERE guild_id=? AND job_id=?',
                                (guild_id, job['id'])).fetchone()
        finally:
            conn.close()

    def finish(self, guild_id, job, status, *, next_run=None, message_id=None, detail=None):
        conn = self.host['db_connect']()
        try:
            conn.execute("""UPDATE message_schedule_state SET
                status=CASE WHEN ?='waiting' AND dirty=1 THEN 'pending' ELSE ? END,
                next_run=?,message_id=?,detail=?,dirty=0 WHERE guild_id=? AND job_id=?""",
                         (status, status, next_run, message_id, detail, guild_id, job['id']))
        finally:
            conn.close()

    async def execute(self, guild, job, now, *, context_member=None, config_key=CONFIG_KEY):
        due, status, _ = self.state(guild.id, job)
        if status != 'pending' or not due or datetime.fromisoformat(due) > now:
            return
        conn = self.host['db_connect']()
        try:
            claimed = conn.execute("UPDATE message_schedule_state SET status='sending',dirty=0 WHERE guild_id=? AND job_id=? AND status='pending' AND next_run=?",
                                   (guild.id, job['id'], due)).rowcount
        finally:
            conn.close()
        if not claimed:
            return
        sent = None
        sending = False
        try:
            channel = guild.get_channel(job['channel'])
            if not isinstance(channel, discord.TextChannel):
                raise ValueError('El canal ya no está disponible.')
            member = await guild.fetch_member(job['author'])
            user_perms = channel.permissions_for(member)
            bot_perms = channel.permissions_for(guild.me) if guild.me else discord.Permissions.none()
            if not member.guild_permissions.manage_guild or not user_perms.view_channel or not user_perms.send_messages:
                raise ValueError('El autor ya no tiene permisos para esta programación.')
            if not bot_perms.view_channel or not bot_perms.send_messages or not bot_perms.embed_links:
                raise ValueError('El bot no tiene permisos suficientes en el canal.')
            template = next((x for x in self.host['heraldo_template_list'](guild.id) if x['name'] == job['template']), None)
            if template is None:
                raise ValueError('La plantilla ya no existe.')
            payload = self.host['heraldo_template_payload'](template, guild, context_member or member, channel)
            if not any(x['id'] == job['id'] for x in self.jobs(guild.id, config_key)):
                self.finish(guild.id, job, 'cancelled')
                return
            if job['repeat'] == 'sticky':
                if not bot_perms.read_message_history:
                    raise ValueError('Sticky requiere Leer historial de mensajes.')
                conn = self.host['db_connect']()
                try:
                    previous = conn.execute('SELECT message_id FROM message_schedule_state WHERE guild_id=? AND job_id=?',
                                            (guild.id, job['id'])).fetchone()[0]
                finally:
                    conn.close()
                if previous:
                    try:
                        old = await channel.fetch_message(previous)
                        if old.author.id != guild.me.id:
                            raise ValueError('La publicación anterior no pertenece al bot; no se modificó.')
                        await old.delete()
                    except discord.NotFound:
                        pass
            sending = True
            sent = await channel.send(**payload)
            next_run = next_occurrence(job, datetime.now(timezone.utc))
            final_status = 'waiting' if job['repeat'] == 'sticky' else 'pending' if next_run else 'done'
            self.finish(guild.id, job, final_status,
                        next_run=next_run, message_id=sent.id)
        except Exception as exc:
            # No copiar contenido, URLs sensibles ni excepciones de HTTP a la configuración.
            status = 'uncertain' if sending else 'error'
            detail = str(exc) if isinstance(exc, ValueError) else 'Fallo de conexión o permisos. Revise el canal antes de volver a programar.'
            self.finish(guild.id, job, status, message_id=getattr(sent, 'id', None), detail=detail)

    async def on_message(self, message):
        if (not self.ready or message.guild is None or message.author.bot
                or message.webhook_id is not None):
            return
        now = datetime.now(timezone.utc)
        for job in self.jobs(message.guild.id, STICKY_KEY):
            if job['channel'] != message.channel.id:
                continue
            self.state(message.guild.id, job)
            conn = self.host['db_connect']()
            try:
                conn.execute("""UPDATE message_schedule_state SET
                    status=CASE WHEN status='waiting' THEN 'pending' ELSE status END,
                    next_run=MAX(next_run,?),dirty=1
                    WHERE guild_id=? AND job_id=? AND status IN ('waiting','sending')""",
                    ((now + timedelta(seconds=5)).isoformat(), message.guild.id, job['id']))
            finally:
                conn.close()
        if not message.content:
            return
        if self.host['condemnation_get'](message.guild.id, message.author.id):
            return
        now = datetime.now(timezone.utc)
        for job in self.jobs(message.guild.id, AUTORESPONSE_KEY):
            if job['channel'] != message.channel.id or not keyword_matches(message.content, job['keyword'], job['match']):
                continue
            due, status, _ = self.state(message.guild.id, job)
            if status != 'pending' or not due or datetime.fromisoformat(due) > now:
                continue
            conn = self.host['db_connect']()
            try:
                # Límite común al canal, incluso si se activan reglas diferentes.
                claimed = conn.execute('''INSERT INTO message_autoresponse_rate VALUES (?,?,?)
                    ON CONFLICT(guild_id,channel_id) DO UPDATE SET until_at=excluded.until_at
                    WHERE message_autoresponse_rate.until_at <= ?''',
                    (message.guild.id, message.channel.id, (now + timedelta(seconds=30)).isoformat(), now.isoformat())).rowcount
            finally:
                conn.close()
            if not claimed:
                return
            await self.execute(message.guild, job, now, context_member=message.author, config_key=AUTORESPONSE_KEY)
            return  # Como máximo una respuesta por mensaje recibido.

    @tasks.loop(seconds=30)
    async def worker(self):
        for guild in self.host['bot'].guilds:
            for config_key in (CONFIG_KEY, STICKY_KEY):
                for job in self.jobs(guild.id, config_key):
                    try:
                        await self.execute(guild, job, datetime.now(timezone.utc), config_key=config_key)
                    except Exception:
                        # Una fila dañada no impide atender los demás servidores.
                        self.host['traceback'].print_exc()


def install(host):
    engine = ScheduledMessages(host)
    group = app_commands.Group(name='programar_mensaje', description='Programación persistente de plantillas.',
                               default_permissions=discord.Permissions(manage_guild=True), guild_only=True)

    @group.command(name='crear', description='Propone publicar una plantilla en una fecha y zona horaria.')
    @app_commands.describe(fecha='Fecha local: AAAA-MM-DD HH:MM', zona='Zona IANA, por ejemplo America/Santo_Domingo')
    @app_commands.choices(repeticion=[app_commands.Choice(name=x, value=x) for x in ('ninguna', 'diaria', 'semanal')])
    async def create(interaction: discord.Interaction, canal: discord.TextChannel, plantilla: str,
                     fecha: str, zona: str = 'America/Santo_Domingo', repeticion: str = 'ninguna'):
        if not await host['configuration_access'](interaction):
            return
        try:
            start = parse_local(fecha, zona)
            if start <= datetime.now(timezone.utc):
                raise ValueError('La fecha debe estar en el futuro.')
            if repeticion not in ('ninguna', 'diaria', 'semanal'):
                raise ValueError('Repetición no admitida.')
            permissions = canal.permissions_for(interaction.user)
            if canal.guild.id != interaction.guild.id or not permissions.view_channel or not permissions.send_messages:
                raise ValueError('No tiene permisos para publicar en ese canal.')
            item = next((x for x in host['heraldo_template_list'](interaction.guild.id)
                         if x['name'].casefold() == plantilla.strip().casefold()), None)
            if item is None:
                raise ValueError('La plantilla no existe.')
            jobs = engine.jobs(interaction.guild.id)
            if len(jobs) >= 25:
                raise ValueError('Máximo de 25 programaciones; retire las que ya no necesite.')
            jobs.append(dict(id=uuid.uuid4().hex[:12], channel=canal.id, template=item['name'],
                             author=interaction.user.id, start=start.isoformat(), zone=zona, repeat=repeticion))
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {CONFIG_KEY: json.dumps(jobs, ensure_ascii=False)})

    @group.command(name='listar', description='Consulta próximas ejecuciones y errores de las programaciones.')
    async def listing(interaction: discord.Interaction):
        if not await host['configuration_access'](interaction):
            return
        lines = []
        labels = {'pending': 'Pendiente', 'done': 'Completada', 'error': 'Error',
                  'uncertain': 'Requiere revisión', 'sending': 'Enviando', 'cancelled': 'Cancelada'}
        for job in engine.jobs(interaction.guild.id):
            due, status, detail = engine.state(interaction.guild.id, job)
            lines.append(f"{job['id']} · {job['template']} · {labels.get(status, status)} · {due or 'Sin próxima ejecución'}"
                         + (f" · {detail}" if detail else ''))
        await send_report(interaction, lines, 'No hay programaciones.')

    @group.command(name='retirar', description='Retira una programación tras confirmación; conserva mensajes enviados.')
    async def remove(interaction: discord.Interaction, identificador: str):
        if not await host['configuration_access'](interaction):
            return
        jobs = engine.jobs(interaction.guild.id)
        remaining = [x for x in jobs if x['id'] != identificador.strip()]
        if len(remaining) == len(jobs):
            await interaction.response.send_message('No se encontró la programación.', ephemeral=True)
            return
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {CONFIG_KEY: json.dumps(remaining, ensure_ascii=False)})

    host['bot'].tree.add_command(group)
    install_autoresponses(host, engine)
    install_sticky(host, engine)
    install_webhook(host)
    return engine


def install_autoresponses(host, engine):
    group = app_commands.Group(name='autorespuesta', description='Respuestas por palabras o frases con límites de frecuencia.',
                               default_permissions=discord.Permissions(manage_guild=True), guild_only=True)

    @group.command(name='crear', description='Propone una respuesta con plantilla, canal y palabra o frase.')
    @app_commands.choices(coincidencia=[app_commands.Choice(name='Mensaje exacto', value='exacta'),
                                     app_commands.Choice(name='Palabra o frase incluida', value='incluida')])
    async def create(interaction: discord.Interaction, canal: discord.TextChannel, plantilla: str,
                     palabra: str, coincidencia: str = 'exacta', espera: app_commands.Range[int, 30, 86400] = 60):
        if not await host['configuration_access'](interaction):
            return
        if not host['bot'].intents.message_content:
            await interaction.response.send_message('Las autorespuestas requieren el intent Message Content habilitado en el bot de laboratorio.', ephemeral=True)
            return
        keyword = palabra.strip()
        permissions = canal.permissions_for(interaction.user)
        if (canal.guild.id != interaction.guild.id or not permissions.view_channel or not permissions.send_messages
                or not 1 <= len(keyword) <= 100 or coincidencia not in ('exacta', 'incluida')):
            await interaction.response.send_message('Revise los permisos del canal y una palabra o frase de hasta 100 caracteres.', ephemeral=True)
            return
        item = next((x for x in host['heraldo_template_list'](interaction.guild.id)
                     if x['name'].casefold() == plantilla.strip().casefold()), None)
        if item is None:
            await interaction.response.send_message('La plantilla no existe.', ephemeral=True)
            return
        jobs = engine.jobs(interaction.guild.id, AUTORESPONSE_KEY)
        if len(jobs) >= 25 or any(x['channel'] == canal.id and x['keyword'].casefold() == keyword.casefold() for x in jobs):
            await interaction.response.send_message('Ya existe esa palabra en el canal o se alcanzaron 25 reglas.', ephemeral=True)
            return
        jobs.append(dict(id=uuid.uuid4().hex[:12], channel=canal.id, template=item['name'],
                         author=interaction.user.id, start=datetime.now(timezone.utc).isoformat(),
                         repeat='trigger', cooldown=espera, keyword=keyword, match=coincidencia))
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {AUTORESPONSE_KEY: json.dumps(jobs, ensure_ascii=False)})

    @group.command(name='listar', description='Consulta las reglas de autorespuesta y su estado.')
    async def listing(interaction: discord.Interaction):
        if not await host['configuration_access'](interaction):
            return
        lines = []
        for job in engine.jobs(interaction.guild.id, AUTORESPONSE_KEY):
            _, status, detail = engine.state(interaction.guild.id, job)
            label = 'Activa' if status == 'pending' else 'Requiere revisión'
            lines.append(f"{job['id']} · {job['keyword']} · {job['template']} · {label}" + (f" · {detail}" if detail else ''))
        await send_report(interaction, lines, 'No hay autorespuestas configuradas.')

    @group.command(name='retirar', description='Retira una regla tras confirmar; conserva las respuestas publicadas.')
    async def remove(interaction: discord.Interaction, identificador: str):
        if not await host['configuration_access'](interaction):
            return
        jobs = engine.jobs(interaction.guild.id, AUTORESPONSE_KEY)
        remaining = [x for x in jobs if x['id'] != identificador.strip()]
        if len(remaining) == len(jobs):
            await interaction.response.send_message('No se encontró la regla.', ephemeral=True)
            return
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {AUTORESPONSE_KEY: json.dumps(remaining, ensure_ascii=False)})

    host['bot'].tree.add_command(group)
    host['bot'].add_listener(engine.on_message, 'on_message')


def install_sticky(host, engine):
    group = app_commands.Group(name='sticky', description='Mantiene una plantilla al final de un canal.',
                               default_permissions=discord.Permissions(manage_guild=True), guild_only=True)

    @group.command(name='crear', description='Propone una publicación sticky; confirmar habilita su publicación.')
    async def create(interaction: discord.Interaction, canal: discord.TextChannel, plantilla: str,
                     espera: app_commands.Range[int, 30, 3600] = 60):
        if not await host['configuration_access'](interaction):
            return
        permissions = canal.permissions_for(interaction.user)
        if canal.guild.id != interaction.guild.id or not permissions.view_channel or not permissions.send_messages:
            await interaction.response.send_message('No tiene acceso para publicar en ese canal.', ephemeral=True)
            return
        item = next((x for x in host['heraldo_template_list'](interaction.guild.id)
                     if x['name'].casefold() == plantilla.strip().casefold()), None)
        if item is None:
            await interaction.response.send_message('La plantilla no existe.', ephemeral=True)
            return
        jobs = engine.jobs(interaction.guild.id, STICKY_KEY)
        if len(jobs) >= 25 or any(x['channel'] == canal.id for x in jobs):
            await interaction.response.send_message('El canal ya tiene un sticky o se alcanzaron 25 canales.', ephemeral=True)
            return
        jobs.append(dict(id=uuid.uuid4().hex[:12], channel=canal.id, template=item['name'],
                         author=interaction.user.id, start=datetime.now(timezone.utc).isoformat(),
                         repeat='sticky', cooldown=espera))
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {STICKY_KEY: json.dumps(jobs, ensure_ascii=False)})

    @group.command(name='listar', description='Consulta los mensajes sticky y errores que requieren revisión.')
    async def listing(interaction: discord.Interaction):
        if not await host['configuration_access'](interaction):
            return
        lines = []
        for job in engine.jobs(interaction.guild.id, STICKY_KEY):
            _, status, detail = engine.state(interaction.guild.id, job)
            label = 'Activo' if status in ('waiting', 'pending') else 'Requiere revisión'
            lines.append(f"{job['id']} · <#{job['channel']}> · {job['template']} · {label}" + (f" · {detail}" if detail else ''))
        await send_report(interaction, lines, 'No hay mensajes sticky.')

    @group.command(name='retirar', description='Detiene el sticky previa confirmación; conserva la última publicación.')
    async def remove(interaction: discord.Interaction, canal: discord.TextChannel):
        if not await host['configuration_access'](interaction):
            return
        jobs = engine.jobs(interaction.guild.id, STICKY_KEY)
        remaining = [x for x in jobs if x['channel'] != canal.id]
        if len(remaining) == len(jobs):
            await interaction.response.send_message('Ese canal no tiene un sticky.', ephemeral=True)
            return
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {STICKY_KEY: json.dumps(remaining, ensure_ascii=False)})

    host['bot'].tree.add_command(group)


class WebhookTemplateConfirmView(discord.ui.View):
    def __init__(self, host, guild_id, owner_id, channel_id, template):
        super().__init__(timeout=300)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.channel_id, self.template = channel_id, copy.deepcopy(template)
        self.finished = False

    async def interaction_check(self, interaction):
        return await self.host['configuration_access'](interaction, self.guild_id, self.owner_id)

    @discord.ui.button(label='Publicar por webhook', style=discord.ButtonStyle.primary)
    async def publish(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if self.finished:
            await interaction.response.send_message('Esta propuesta ya fue resuelta.', ephemeral=True)
            return
        guild = interaction.guild
        channel = guild.get_channel(self.channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message('El canal ya no está disponible.', ephemeral=True)
            return
        user_perms = channel.permissions_for(interaction.user)
        bot_perms = channel.permissions_for(guild.me) if guild.me else discord.Permissions.none()
        if not (user_perms.view_channel and user_perms.send_messages and user_perms.manage_webhooks
                and bot_perms.view_channel and bot_perms.send_messages and bot_perms.manage_webhooks):
            await interaction.response.send_message('El administrador y el bot necesitan acceso, envío y gestión de webhooks en el canal.', ephemeral=True)
            return
        current = next((x for x in self.host['heraldo_template_list'](guild.id) if x['name'] == self.template['name']), None)
        if current != self.template:
            await interaction.response.send_message('La plantilla cambió; abra una nueva propuesta antes de publicar.', ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.response.defer(ephemeral=True)
        try:
            payload = self.host['heraldo_template_payload'](self.template, guild, interaction.user, channel)
            view = payload.get('view')
            if view and any(getattr(child, 'custom_id', None) for child in view.children):
                raise ValueError('Los webhooks admiten enlaces, pero los componentes de roles deben publicarse con el bot.')
            if view is None:
                payload.pop('view', None)
            hooks = await channel.webhooks()
            webhook = next((x for x in hooks if getattr(x.user, 'id', None) == guild.me.id
                            and x.name == 'El Heraldo - Mensajes' and x.channel_id == channel.id), None)
            if webhook is None:
                webhook = await channel.create_webhook(name='El Heraldo - Mensajes', reason='Publicación confirmada desde Mensajes')
            sent = await webhook.send(**payload, wait=True)
            result = f'Publicación confirmada: https://discord.com/channels/{guild.id}/{channel.id}/{sent.id}'
        except ValueError as exc:
            result = str(exc)
        except (discord.HTTPException, TimeoutError):
            result = 'No se pudo confirmar la publicación. Revise el canal antes de reintentar; el mensaje podría haberse enviado.'
        await interaction.edit_original_response(content=result, embeds=[], view=None)

    @discord.ui.button(label='Cancelar', style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if self.finished:
            await interaction.response.send_message('Esta propuesta ya fue resuelta.', ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content='Publicación cancelada; no se creó ni utilizó ningún webhook.', embeds=[], view=None)


def install_webhook(host):
    @host['bot'].tree.command(name='webhook_mensaje', description='Publica una plantilla mediante un webhook del propio bot, previa confirmación.')
    @app_commands.default_permissions(manage_guild=True, manage_webhooks=True)
    @app_commands.guild_only()
    async def publish(interaction: discord.Interaction, canal: discord.TextChannel, plantilla: str):
        if not await host['configuration_access'](interaction):
            return
        permissions = canal.permissions_for(interaction.user)
        if (canal.guild.id != interaction.guild.id or not permissions.view_channel
                or not permissions.send_messages or not permissions.manage_webhooks):
            await interaction.response.send_message('Necesita acceso, envío y gestión de webhooks en ese canal.', ephemeral=True)
            return
        item = next((x for x in host['heraldo_template_list'](interaction.guild.id)
                     if x['name'].casefold() == plantilla.strip().casefold()), None)
        if item is None:
            await interaction.response.send_message('La plantilla no existe.', ephemeral=True)
            return
        try:
            payload = host['heraldo_template_payload'](item, interaction.guild, interaction.user, canal)
            view = payload.get('view')
            if view and any(getattr(child, 'custom_id', None) for child in view.children):
                raise ValueError('Los componentes de roles requieren publicación mediante el bot; seleccione una plantilla visual.')
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        payload['view'] = WebhookTemplateConfirmView(host, interaction.guild.id, interaction.user.id, canal.id, item)
        await interaction.response.send_message(**payload, ephemeral=True)
