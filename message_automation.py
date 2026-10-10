"""Programación persistente de plantillas, con confirmación y ejecución conservadora."""
import json
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import tasks


CONFIG_KEY = 'message_schedules'


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

    def jobs(self, guild_id):
        try:
            value = json.loads(self.host['guild_config_get'](guild_id, CONFIG_KEY) or '[]')
            return value if isinstance(value, list) else []
        except (TypeError, ValueError):
            return []

    def initialize(self):
        conn = self.host['db_connect']()
        try:
            conn.execute('''CREATE TABLE IF NOT EXISTS message_schedule_state (
                guild_id INTEGER NOT NULL, job_id TEXT NOT NULL, next_run TEXT,
                status TEXT NOT NULL DEFAULT 'pending', message_id INTEGER,
                detail TEXT, PRIMARY KEY(guild_id, job_id))''')
            # Un envío interrumpido podría haber llegado a Discord. No repetir a ciegas.
            conn.execute("UPDATE message_schedule_state SET status='uncertain', detail=? WHERE status='sending'",
                         ('Envío interrumpido. Revise el canal y cree una nueva programación si corresponde.',))
        finally:
            conn.close()

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
            conn.execute('UPDATE message_schedule_state SET status=?,next_run=?,message_id=?,detail=? WHERE guild_id=? AND job_id=?',
                         (status, next_run, message_id, detail, guild_id, job['id']))
        finally:
            conn.close()

    async def execute(self, guild, job, now):
        due, status, _ = self.state(guild.id, job)
        if status != 'pending' or not due or datetime.fromisoformat(due) > now:
            return
        conn = self.host['db_connect']()
        try:
            claimed = conn.execute("UPDATE message_schedule_state SET status='sending' WHERE guild_id=? AND job_id=? AND status='pending' AND next_run=?",
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
            payload = self.host['heraldo_template_payload'](template, guild, member, channel)
            if not any(x['id'] == job['id'] for x in self.jobs(guild.id)):
                self.finish(guild.id, job, 'cancelled')
                return
            sending = True
            sent = await channel.send(**payload)
            next_run = next_occurrence(job, datetime.now(timezone.utc))
            self.finish(guild.id, job, 'pending' if next_run else 'done',
                        next_run=next_run, message_id=sent.id)
        except Exception as exc:
            # No copiar contenido, URLs sensibles ni excepciones de HTTP a la configuración.
            status = 'uncertain' if sending else 'error'
            detail = str(exc) if isinstance(exc, ValueError) else 'Fallo de conexión o permisos. Revise el canal antes de volver a programar.'
            self.finish(guild.id, job, status, message_id=getattr(sent, 'id', None), detail=detail)

    @tasks.loop(seconds=30)
    async def worker(self):
        for guild in self.host['bot'].guilds:
            for job in self.jobs(guild.id):
                try:
                    await self.execute(guild, job, datetime.now(timezone.utc))
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
        await interaction.response.send_message('\n'.join(lines)[:1900] or 'No hay programaciones.',
                                                ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

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
    return engine
