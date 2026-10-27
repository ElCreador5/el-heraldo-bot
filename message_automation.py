"""Programación persistente de plantillas, con confirmación y ejecución conservadora."""
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
from heraldo_i18n import join_text as _i18n_join
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


@_i18n_context
async def send_report(interaction, lines, empty):
    text = _i18n_join('\n', lines) or empty
    if len(text) <= 1900:
        await interaction.response.send_message(text, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        return
    report = discord.File(io.BytesIO(text.encode('utf-8')), filename='automatizaciones.txt')
    try:
        await interaction.response.send_message(_t('text.36f6dd8405b286'),
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
            raise ValueError(_t('text.aea2f127d87951'))
        candidate = local.replace(tzinfo=tz)
        if candidate.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != local:
            raise ValueError(_t('text.72fb50a1c9d473'))
        if candidate.utcoffset() != local.replace(tzinfo=tz, fold=1).utcoffset():
            raise ValueError(_t('text.895927fb169cee'))
        return candidate.astimezone(timezone.utc)
    except ZoneInfoNotFoundError:
        raise ValueError(_t('text.5bde67d5dc66f7')) from None


def next_occurrence(job, now):
    if job['repeat'] in ('trigger', 'sticky'):
        return (now + timedelta(seconds=job['cooldown'])).isoformat()
    if job['repeat'] == 'ninguna':
        return None
    if job['repeat'] == 'intervalo':
        from message_autofeeds import interval_seconds
        period = interval_seconds(job['interval'])
        origin = datetime.fromisoformat(job['start']).astimezone(timezone.utc)
        steps = max(1, int((now - origin).total_seconds() // period) + 1)
        return (origin + timedelta(seconds=steps * period)).isoformat()
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
    @_i18n_context
    def __init__(self, host):
        self.host = host
        self.ready = False

    @_i18n_context
    def jobs(self, guild_id, key=CONFIG_KEY):
        try:
            value = json.loads(self.host['guild_config_get'](guild_id, key) or '[]')
            return value if isinstance(value, list) else []
        except (TypeError, ValueError):
            return []

    @_i18n_context
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
            interrupted = conn.execute(
                "SELECT DISTINCT guild_id FROM message_schedule_state WHERE status='sending'"
            ).fetchall()
            for (guild_id,) in interrupted:
                with _i18n_guild(int(guild_id)):
                    conn.execute("UPDATE message_schedule_state SET status='uncertain', detail=? "
                                 "WHERE status='sending' AND guild_id=?",
                                 (_t('text.310350050c4757'), guild_id))
        finally:
            conn.close()
        self.ready = True

    @_i18n_context
    def start(self):
        if not self.worker.is_running():
            self.initialize()
            self.worker.start()

    @_i18n_context
    def state(self, guild_id, job):
        conn = self.host['db_connect']()
        try:
            conn.execute('INSERT OR IGNORE INTO message_schedule_state (guild_id,job_id,next_run) VALUES (?,?,?)',
                         (guild_id, job['id'], job['start']))
            return conn.execute('SELECT next_run,status,detail FROM message_schedule_state WHERE guild_id=? AND job_id=?',
                                (guild_id, job['id'])).fetchone()
        finally:
            conn.close()

    @_i18n_context
    def finish(self, guild_id, job, status, *, next_run=None, message_id=None, detail=None):
        conn = self.host['db_connect']()
        try:
            conn.execute("""UPDATE message_schedule_state SET
                status=CASE WHEN status='paused' THEN 'paused'
                            WHEN ?='waiting' AND dirty=1 THEN 'pending' ELSE ? END,
                next_run=CASE WHEN status='paused' THEN next_run ELSE ? END,
                message_id=?,detail=?,dirty=0 WHERE guild_id=? AND job_id=?""",
                         (status, status, next_run, message_id, detail, guild_id, job['id']))
        finally:
            conn.close()

    @_i18n_context
    async def execute(self, guild, job, now, *, context_member=None, config_key=CONFIG_KEY):
        due, status, _ = self.state(guild.id, job)
        if status != 'pending' or not due or datetime.fromisoformat(due) > now or job.get('paused'):
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
                raise ValueError(_t('text.7a3072bf51b38b'))
            member = await guild.fetch_member(job['author'])
            user_perms = channel.permissions_for(member)
            bot_perms = channel.permissions_for(guild.me) if guild.me else discord.Permissions.none()
            if job.get('autofeed'):
                from message_autofeeds import can_deliver
                if not can_deliver(self.host, guild, job, member, channel):
                    raise ValueError(_t('text.fd79243eaf7cd5'))
            elif not member.guild_permissions.manage_guild or not user_perms.view_channel or not user_perms.send_messages:
                raise ValueError(_t('text.fd79243eaf7cd5'))
            if not bot_perms.view_channel or not bot_perms.send_messages or not bot_perms.embed_links:
                raise ValueError(_t('text.a0250ca7797377'))
            if job.get('autofeed') and job.get('text'):
                payload = {'content': job['text'], 'allowed_mentions': discord.AllowedMentions.none()}
            else:
                template = next((x for x in self.host['heraldo_template_list'](guild.id) if x['name'] == job['template']), None)
                if template is None:
                    raise ValueError(_t('text.e751ce97a2b7f0'))
                payload = self.host['heraldo_template_payload'](template, guild, context_member or member, channel)
            if job.get('autofeed'):
                role = guild.get_role(job['role']) if job.get('role') else None
                if job.get('role') and (role is None or not role.mentionable):
                    raise ValueError('Rol de mención no disponible.')
                if role:
                    payload = {**payload,
                               'content': ((payload.get('content') or '') + '\n' + role.mention).strip(),
                               'allowed_mentions': discord.AllowedMentions(everyone=False, users=False, roles=[role])}
                else:
                    payload = {**payload, 'allowed_mentions': discord.AllowedMentions.none()}
            if not any(x['id'] == job['id'] for x in self.jobs(guild.id, config_key)):
                self.finish(guild.id, job, 'cancelled')
                return
            if job['repeat'] == 'sticky':
                if not bot_perms.read_message_history:
                    raise ValueError(_t('text.1331a60fbca152'))
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
                            raise ValueError(_t('text.4fdbf2e471fdf5'))
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
            detail = str(exc) if isinstance(exc, ValueError) else _t('text.741a22e573a4d5')
            self.finish(guild.id, job, status, message_id=getattr(sent, 'id', None), detail=detail)

    @_i18n_context
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
    @_i18n_context
    async def worker(self):
        for guild in self.host['bot'].guilds:
            with _i18n_guild(guild.id):
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
    @app_commands.describe(fecha=_t('text.5b617234bc1705'), zona=_t('text.7288daf3b35948'))
    @app_commands.choices(repeticion=[app_commands.Choice(name=x, value=x) for x in ('ninguna', 'diaria', 'semanal')])
    @_i18n_context
    async def create(interaction: discord.Interaction, canal: discord.TextChannel, plantilla: str,
                     fecha: str, zona: str = 'America/Santo_Domingo', repeticion: str = 'ninguna'):
        if not await host['configuration_access'](interaction):
            return
        try:
            start = parse_local(fecha, zona)
            if start <= datetime.now(timezone.utc):
                raise ValueError(_t('text.be9dfe88b977e9'))
            if repeticion not in ('ninguna', 'diaria', 'semanal'):
                raise ValueError(_t('text.3028c431ef8600'))
            permissions = canal.permissions_for(interaction.user)
            if canal.guild.id != interaction.guild.id or not permissions.view_channel or not permissions.send_messages:
                raise ValueError(_t('text.7b2064ceab41f6'))
            item = next((x for x in host['heraldo_template_list'](interaction.guild.id)
                         if x['name'].casefold() == plantilla.strip().casefold()), None)
            if item is None:
                raise ValueError(_t('text.14ab3a6c676705'))
            jobs = engine.jobs(interaction.guild.id)
            if len(jobs) >= 25:
                raise ValueError(_t('text.8cb0d25b5bc5d2'))
            jobs.append(dict(id=uuid.uuid4().hex[:12], channel=canal.id, template=item['name'],
                             author=interaction.user.id, start=start.isoformat(), zone=zona, repeat=repeticion))
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {CONFIG_KEY: json.dumps(jobs, ensure_ascii=False)})

    @group.command(name='listar', description='Consulta próximas ejecuciones y errores de las programaciones.')
    @_i18n_context
    async def listing(interaction: discord.Interaction):
        if not await host['configuration_access'](interaction):
            return
        lines = []
        labels = {'pending': _t('text.2ef68536d8e212'), 'done': _t('text.b148590c0b0b8f'), 'error': _t('text.54a0e8c17ebb21'),
                  'uncertain': _t('text.0970a2881d7e5a'), 'sending': _t('text.6840b96b4cdc5e'), 'cancelled': _t('text.3d15e61f2ccd51')}
        for job in engine.jobs(interaction.guild.id):
            due, status, detail = engine.state(interaction.guild.id, job)
            lines.append(f"{job['id']} · {job['template']} · {labels.get(status, status)} · {due or _t('text.f2529211f904d6')}"
                         + (f" · {detail}" if detail else ''))
        await send_report(interaction, lines, _t('text.ed1e365f2adee8'))

    @group.command(name='retirar', description='Retira una programación tras confirmación; conserva mensajes enviados.')
    @_i18n_context
    async def remove(interaction: discord.Interaction, identificador: str):
        if not await host['configuration_access'](interaction):
            return
        jobs = engine.jobs(interaction.guild.id)
        remaining = [x for x in jobs if x['id'] != identificador.strip()]
        if len(remaining) == len(jobs):
            await interaction.response.send_message(_t('text.4fd44ed3b90c7e'), ephemeral=True)
            return
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {CONFIG_KEY: json.dumps(remaining, ensure_ascii=False)})

    host['bot'].tree.add_command(group)
    install_autoresponses(host, engine)
    install_sticky(host, engine)
    install_webhook(host)
    import message_autofeeds
    message_autofeeds.install(host)
    return engine


def install_autoresponses(host, engine):
    group = app_commands.Group(name='autorespuesta', description='Respuestas por palabras o frases con límites de frecuencia.',
                               default_permissions=discord.Permissions(manage_guild=True), guild_only=True)

    @group.command(name='crear', description='Propone una respuesta con plantilla, canal y palabra o frase.')
    @app_commands.choices(coincidencia=[app_commands.Choice(name='Mensaje exacto', value='exacta'),
                                     app_commands.Choice(name='Palabra o frase incluida', value='incluida')])
    @_i18n_context
    async def create(interaction: discord.Interaction, canal: discord.TextChannel, plantilla: str,
                     palabra: str, coincidencia: str = 'exacta', espera: app_commands.Range[int, 30, 86400] = 60):
        if not await host['configuration_access'](interaction):
            return
        if not host['bot'].intents.message_content:
            await interaction.response.send_message(_t('text.a80c48cf580c36'), ephemeral=True)
            return
        keyword = palabra.strip()
        permissions = canal.permissions_for(interaction.user)
        if (canal.guild.id != interaction.guild.id or not permissions.view_channel or not permissions.send_messages
                or not 1 <= len(keyword) <= 100 or coincidencia not in ('exacta', 'incluida')):
            await interaction.response.send_message(_t('text.5becbad6f622f4'), ephemeral=True)
            return
        item = next((x for x in host['heraldo_template_list'](interaction.guild.id)
                     if x['name'].casefold() == plantilla.strip().casefold()), None)
        if item is None:
            await interaction.response.send_message(_t('text.14ab3a6c676705'), ephemeral=True)
            return
        jobs = engine.jobs(interaction.guild.id, AUTORESPONSE_KEY)
        if len(jobs) >= 25 or any(x['channel'] == canal.id and x['keyword'].casefold() == keyword.casefold() for x in jobs):
            await interaction.response.send_message(_t('text.4a358b2b8a4d8f'), ephemeral=True)
            return
        jobs.append(dict(id=uuid.uuid4().hex[:12], channel=canal.id, template=item['name'],
                         author=interaction.user.id, start=datetime.now(timezone.utc).isoformat(),
                         repeat='trigger', cooldown=espera, keyword=keyword, match=coincidencia))
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {AUTORESPONSE_KEY: json.dumps(jobs, ensure_ascii=False)})

    @group.command(name='listar', description='Consulta las reglas de autorespuesta y su estado.')
    @_i18n_context
    async def listing(interaction: discord.Interaction):
        if not await host['configuration_access'](interaction):
            return
        lines = []
        for job in engine.jobs(interaction.guild.id, AUTORESPONSE_KEY):
            _, status, detail = engine.state(interaction.guild.id, job)
            label = _t('text.69d17ca1683468') if status == 'pending' else _t('text.0970a2881d7e5a')
            lines.append(f"{job['id']} · {job['keyword']} · {job['template']} · {label}" + (f" · {detail}" if detail else ''))
        await send_report(interaction, lines, _t('text.fd1e47db8b642b'))

    @group.command(name='retirar', description='Retira una regla tras confirmar; conserva las respuestas publicadas.')
    @_i18n_context
    async def remove(interaction: discord.Interaction, identificador: str):
        if not await host['configuration_access'](interaction):
            return
        jobs = engine.jobs(interaction.guild.id, AUTORESPONSE_KEY)
        remaining = [x for x in jobs if x['id'] != identificador.strip()]
        if len(remaining) == len(jobs):
            await interaction.response.send_message(_t('text.1caddd30a67250'), ephemeral=True)
            return
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {AUTORESPONSE_KEY: json.dumps(remaining, ensure_ascii=False)})

    host['bot'].tree.add_command(group)
    host['bot'].add_listener(engine.on_message, 'on_message')


def install_sticky(host, engine):
    group = app_commands.Group(name='sticky', description='Mantiene una plantilla al final de un canal.',
                               default_permissions=discord.Permissions(manage_guild=True), guild_only=True)

    @group.command(name='crear', description='Propone una publicación sticky; confirmar habilita su publicación.')
    @_i18n_context
    async def create(interaction: discord.Interaction, canal: discord.TextChannel, plantilla: str,
                     espera: app_commands.Range[int, 30, 3600] = 60):
        if not await host['configuration_access'](interaction):
            return
        permissions = canal.permissions_for(interaction.user)
        if canal.guild.id != interaction.guild.id or not permissions.view_channel or not permissions.send_messages:
            await interaction.response.send_message(_t('text.88f2e207b5d040'), ephemeral=True)
            return
        item = next((x for x in host['heraldo_template_list'](interaction.guild.id)
                     if x['name'].casefold() == plantilla.strip().casefold()), None)
        if item is None:
            await interaction.response.send_message(_t('text.14ab3a6c676705'), ephemeral=True)
            return
        jobs = engine.jobs(interaction.guild.id, STICKY_KEY)
        if len(jobs) >= 25 or any(x['channel'] == canal.id for x in jobs):
            await interaction.response.send_message(_t('text.46145d087500b5'), ephemeral=True)
            return
        jobs.append(dict(id=uuid.uuid4().hex[:12], channel=canal.id, template=item['name'],
                         author=interaction.user.id, start=datetime.now(timezone.utc).isoformat(),
                         repeat='sticky', cooldown=espera))
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {STICKY_KEY: json.dumps(jobs, ensure_ascii=False)})

    @group.command(name='listar', description='Consulta los mensajes sticky y errores que requieren revisión.')
    @_i18n_context
    async def listing(interaction: discord.Interaction):
        if not await host['configuration_access'](interaction):
            return
        lines = []
        for job in engine.jobs(interaction.guild.id, STICKY_KEY):
            _, status, detail = engine.state(interaction.guild.id, job)
            label = _t('text.723858144bd548') if status in ('waiting', 'pending') else _t('text.0970a2881d7e5a')
            lines.append(f"{job['id']} · <#{job['channel']}> · {job['template']} · {label}" + (f" · {detail}" if detail else ''))
        await send_report(interaction, lines, _t('text.a81cb4ff334037'))

    @group.command(name='retirar', description='Detiene el sticky previa confirmación; conserva la última publicación.')
    @_i18n_context
    async def remove(interaction: discord.Interaction, canal: discord.TextChannel):
        if not await host['configuration_access'](interaction):
            return
        jobs = engine.jobs(interaction.guild.id, STICKY_KEY)
        remaining = [x for x in jobs if x['channel'] != canal.id]
        if len(remaining) == len(jobs):
            await interaction.response.send_message(_t('text.784a802a4ee8bf'), ephemeral=True)
            return
        await host['confirm_configuration'](interaction, interaction.guild.id,
                                             {STICKY_KEY: json.dumps(remaining, ensure_ascii=False)})

    host['bot'].tree.add_command(group)


class WebhookTemplateConfirmView(discord.ui.View):
    @_i18n_context
    def __init__(self, host, guild_id, owner_id, channel_id, template):
        super().__init__(timeout=300)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.channel_id, self.template = channel_id, copy.deepcopy(template)
        self.finished = False

    @_i18n_context
    async def interaction_check(self, interaction):
        return await self.host['configuration_access'](interaction, self.guild_id, self.owner_id)

    @discord.ui.button(label=_t('text.d45721b4af97cd'), style=discord.ButtonStyle.success)
    @_i18n_context
    async def publish(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if self.finished:
            await interaction.response.send_message(_t('text.6f5c8804bdb7ae'), ephemeral=True)
            return
        guild = interaction.guild
        channel = guild.get_channel(self.channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(_t('text.7a3072bf51b38b'), ephemeral=True)
            return
        user_perms = channel.permissions_for(interaction.user)
        bot_perms = channel.permissions_for(guild.me) if guild.me else discord.Permissions.none()
        if not (user_perms.view_channel and user_perms.send_messages and user_perms.manage_webhooks
                and bot_perms.view_channel and bot_perms.send_messages and bot_perms.manage_webhooks):
            await interaction.response.send_message(_t('text.5ba905cb3a32ad'), ephemeral=True)
            return
        current = next((x for x in self.host['heraldo_template_list'](guild.id) if x['name'] == self.template['name']), None)
        if current != self.template:
            await interaction.response.send_message(_t('text.1f6ca00d620b7b'), ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.response.defer(ephemeral=True)
        try:
            payload = self.host['heraldo_template_payload'](self.template, guild, interaction.user, channel)
            view = payload.get('view')
            if view and any(getattr(child, 'custom_id', None) for child in view.children):
                raise ValueError(_t('text.a0474f39f6f61d'))
            if view is None:
                payload.pop('view', None)
            hooks = await channel.webhooks()
            webhook = next((x for x in hooks if getattr(x.user, 'id', None) == guild.me.id
                            and x.name == 'El Heraldo - Mensajes' and x.channel_id == channel.id), None)
            if webhook is None:
                webhook = await channel.create_webhook(name='El Heraldo - Mensajes', reason=_t('text.a4ed427adb8db3'))
            sent = await webhook.send(**payload, wait=True)
            result = _t('text.38787c477a079b', p0=f'{guild.id}', p1=f'{channel.id}', p2=f'{sent.id}')
        except ValueError as exc:
            result = str(exc)
        except (discord.HTTPException, TimeoutError):
            result = _t('text.bd37c0c7497884')
        await interaction.edit_original_response(content=result, embeds=[], view=None)

    @discord.ui.button(label=_t('text.bb9dbb406dcbd5'), style=discord.ButtonStyle.danger)
    @_i18n_context
    async def cancel(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if self.finished:
            await interaction.response.send_message(_t('text.6f5c8804bdb7ae'), ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content=_t('text.15ed27052e318c'), embeds=[], view=None)


def install_webhook(host):
    @host['bot'].tree.command(name='webhook_mensaje', description='Publica una plantilla mediante un webhook del propio bot, previa confirmación.')
    @app_commands.default_permissions(manage_guild=True, manage_webhooks=True)
    @app_commands.guild_only()
    @_i18n_context
    async def publish(interaction: discord.Interaction, canal: discord.TextChannel, plantilla: str):
        if not await host['configuration_access'](interaction):
            return
        permissions = canal.permissions_for(interaction.user)
        if (canal.guild.id != interaction.guild.id or not permissions.view_channel
                or not permissions.send_messages or not permissions.manage_webhooks):
            await interaction.response.send_message(_t('text.6a9401c16dab60'), ephemeral=True)
            return
        item = next((x for x in host['heraldo_template_list'](interaction.guild.id)
                     if x['name'].casefold() == plantilla.strip().casefold()), None)
        if item is None:
            await interaction.response.send_message(_t('text.14ab3a6c676705'), ephemeral=True)
            return
        try:
            payload = host['heraldo_template_payload'](item, interaction.guild, interaction.user, canal)
            view = payload.get('view')
            if view and any(getattr(child, 'custom_id', None) for child in view.children):
                raise ValueError(_t('text.a4f8be88ae396d'))
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        payload['view'] = WebhookTemplateConfirmView(host, interaction.guild.id, interaction.user.id, canal.id, item)
        await interaction.response.send_message(**payload, ephemeral=True)
