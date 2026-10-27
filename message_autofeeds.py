"""AutoFeeds: interfaz unificada sobre las programaciones persistentes de Mensajes.

Las rutas heredadas permanecen para no alterar programaciones existentes.
Ningun contenido se publica al escoger selectores ni antes de Guardar cambios.
"""
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from heraldo_i18n import current_locale, guild_context, use_guild

POLICY_KEY = "autofeed_policy"
CONFIG_KEY = "message_schedules"
MAX_SERVER = 25
STRINGS = {
    "es-419": {
        "denied": "No tienes permiso para programar en ese canal.",
        "no_jobs": "No hay programaciones disponibles.",
        "invalid": "Revisa la fecha, la frecuencia y el contenido.",
        "changed": "La programación cambió en otra sesión. Vuelve a abrirla.",
        "missing": "No se encontró la programación o no puedes administrarla.",
        "saved": "Programación guardada.",
        "removed": "Programación eliminada. Los mensajes ya publicados se conservan.",
        "paused": "Programación pausada.",
        "resumed": "Programación reanudada.",
        "discarded": "Cambios descartados.",
        "choose": "Selecciona una programación",
        "save": "Guardar cambios",
        "discard": "Descartar cambios",
        "back": "Volver",
        "preview": "Vista previa de la programación",
        "settings": "Acceso a programaciones",
        "policy_saved": "Permisos guardados.",
        "policy_on": "Programación de miembros activada.",
        "policy_off": "Programación de miembros pausada.",
        "policy_needs": "Configura primero al menos un canal autorizado.",
        "role": "El rol seleccionado debe poder mencionarse.",
        "quota": "Se alcanzó el límite de programaciones.",
        "content": "Escribe un mensaje o selecciona una plantilla existente.",
        "past": "Selecciona una fecha futura.",
        "legacy": "Esta programación se administra con el comando anterior /programar_mensaje.",
        "channels": "Canales permitidos para miembros",
        "roles_ui": "Roles que pueden programar",
        "edit": "Editar",
        "pause": "Pausar",
        "resume": "Reanudar",
        "silence": "Silenciar",
        "delete": "Eliminar",
        "modal": "Programar mensaje",
        "msg": "Mensaje",
        "date": "Fecha y hora local (AAAA-MM-DD HH:MM)",
        "interval_ui": "Intervalo (ej. 6h, 2d)",
        "channel_label": "Canal",
        "frequency_label": "Frecuencia",
        "start_label": "Inicio",
        "mention_label": "Mención",
        "content_label": "Contenido",
        "no_role": "Sin rol",
        "template_label": "Plantilla",
        "status_label": "Estado",
        "activate": "Activar",
        "enabled_label": "Activo",
        "disabled_label": "Pausado",
        "limit_label": "Límite por miembro",
        "policy_help": "Las listas se guardan con Guardar cambios. Activar/Pausar solo cambia el estado guardado.",
    },
    "en-US": {
        "denied": "You cannot schedule messages in that channel.",
        "no_jobs": "No schedules are available.",
        "invalid": "Check the date, frequency, and content.",
        "changed": "This schedule changed in another session. Open it again.",
        "missing": "Schedule not found or you cannot manage it.",
        "saved": "Schedule saved.",
        "removed": "Schedule deleted. Previously posted messages remain.",
        "paused": "Schedule paused.",
        "resumed": "Schedule resumed.",
        "discarded": "Changes discarded.",
        "choose": "Select a schedule",
        "save": "Save changes",
        "discard": "Discard changes",
        "back": "Back",
        "preview": "Schedule preview",
        "settings": "Scheduling access",
        "policy_saved": "Permissions saved.",
        "policy_on": "Member scheduling enabled.",
        "policy_off": "Member scheduling paused.",
        "policy_needs": "Configure at least one permitted channel first.",
        "role": "The selected role must be mentionable.",
        "quota": "The scheduling limit has been reached.",
        "content": "Enter a message or select an existing template.",
        "past": "Select a future date.",
        "legacy": "Manage this legacy schedule using /programar_mensaje.",
        "channels": "Channels members may post in",
        "roles_ui": "Roles allowed to schedule",
        "edit": "Edit",
        "pause": "Pause",
        "resume": "Resume",
        "silence": "Mute",
        "delete": "Delete",
        "modal": "Schedule a message",
        "msg": "Message",
        "date": "Local date and time (YYYY-MM-DD HH:MM)",
        "interval_ui": "Interval (e.g. 6h, 2d)",
        "channel_label": "Channel",
        "frequency_label": "Frequency",
        "start_label": "Start",
        "mention_label": "Mention",
        "content_label": "Content",
        "no_role": "No role",
        "template_label": "Template",
        "status_label": "Status",
        "activate": "Enable",
        "enabled_label": "Enabled",
        "disabled_label": "Paused",
        "limit_label": "Per-member limit",
        "policy_help": "Save lists with Save changes. Enable/Pause only updates the saved state.",
    },
    "pt-BR": {
        "denied": "Você não pode programar mensagens nesse canal.",
        "no_jobs": "Não há programações disponíveis.",
        "invalid": "Confira a data, a frequência e o conteúdo.",
        "changed": "Esta programação mudou em outra sessão. Abra-a novamente.",
        "missing": "Programação não encontrada ou sem permissão para administrá-la.",
        "saved": "Programação salva.",
        "removed": "Programação excluída. Mensagens já publicadas são preservadas.",
        "paused": "Programação pausada.",
        "resumed": "Programação retomada.",
        "discarded": "Alterações descartadas.",
        "choose": "Selecione uma programação",
        "save": "Salvar alterações",
        "discard": "Descartar alterações",
        "back": "Voltar",
        "preview": "Prévia da programação",
        "settings": "Acesso às programações",
        "policy_saved": "Permissões salvas.",
        "policy_on": "Programação dos membros ativada.",
        "policy_off": "Programação dos membros pausada.",
        "policy_needs": "Configure pelo menos um canal permitido primeiro.",
        "role": "O cargo selecionado deve permitir menções.",
        "quota": "O limite de programações foi atingido.",
        "content": "Digite uma mensagem ou selecione um modelo existente.",
        "past": "Selecione uma data futura.",
        "legacy": "Gerencie esta programação antiga usando /programar_mensaje.",
        "channels": "Canais permitidos aos membros",
        "roles_ui": "Cargos autorizados a programar",
        "edit": "Editar",
        "pause": "Pausar",
        "resume": "Retomar",
        "silence": "Silenciar",
        "delete": "Excluir",
        "modal": "Programar mensagem",
        "msg": "Mensagem",
        "date": "Data e hora local (AAAA-MM-DD HH:MM)",
        "interval_ui": "Intervalo (ex. 6h, 2d)",
        "channel_label": "Canal",
        "frequency_label": "Frequência",
        "start_label": "Início",
        "mention_label": "Menção",
        "content_label": "Conteúdo",
        "no_role": "Sem cargo",
        "template_label": "Modelo",
        "status_label": "Estado",
        "activate": "Ativar",
        "enabled_label": "Ativo",
        "disabled_label": "Pausado",
        "limit_label": "Limite por membro",
        "policy_help": "Salve listas com Salvar alterações. Ativar/Pausar altera somente o estado salvo.",
    },
}


def tr(key):
    return STRINGS.get(current_locale(), STRINGS["es-419"])[key]


def policy(host, guild_id):
    try:
        obj = json.loads(host["guild_config_get"](guild_id, POLICY_KEY) or "{}")
        if isinstance(obj, dict):
            return {"enabled": bool(obj.get("enabled", False)),
                    "channels": [int(x) for x in obj.get("channels", [])][:25],
                    "roles": [int(x) for x in obj.get("roles", [])][:25],
                    "max_per_member": min(10, max(1, int(obj.get("max_per_member", 3))))}
    except (ValueError, TypeError, KeyError):
        pass
    return {"enabled": False, "channels": [], "roles": [], "max_per_member": 3}


def can_create(host, member, channel):
    perms = channel.permissions_for(member)
    if not (perms.view_channel and perms.send_messages):
        return False
    if member.guild_permissions.manage_guild:
        return True
    p = policy(host, member.guild.id)
    return (p["enabled"] and channel.id in p["channels"]
            and any(role.id in p["roles"] for role in member.roles))


def can_manage(member, job):
    return member.guild_permissions.manage_guild or job.get("author") == member.id


def referenced_mentions(guild, job):
    """Resolve only roles/channels belonging to this guild, with a hard ping limit.

    Channel mentions display as links but do not generate notifications. Role
    references in embed text are visible; only roles in message content can ping.
    """
    body = (job.get("text") or "")
    visual = job.get("embed") or {}
    display = body + "\n" + (visual.get("description") or "") + "\n" + (visual.get("title") or "")
    role_ids = {int(value) for value in re.findall(r"<@&(\d{1,20})>", display)}
    channel_ids = {int(value) for value in re.findall(r"<#(\d{1,20})>", display)}
    explicit = job.get("role")
    if explicit:
        role_ids.add(int(explicit))
    if len(role_ids) > 5 or len(channel_ids) > 15:
        raise ValueError("invalid")
    for channel_id in channel_ids:
        if guild.get_channel(channel_id) is None:
            raise ValueError("invalid")
    roles = {}
    for role_id in role_ids:
        role = guild.get_role(role_id)
        if role is None:
            raise ValueError("role")
        roles[role_id] = role
    # Embed text displays mentions but cannot fire a notification; only
    # content-level tokens and the optional dedicated role produce role pings.
    ping_ids = {int(value) for value in re.findall(r"<@&(\d{1,20})>", body)}
    if explicit:
        ping_ids.add(int(explicit))
    return [roles[role_id] for role_id in sorted(ping_ids)
            if roles[role_id].mentionable]


def can_deliver(host, guild, job, member, channel):
    if job.get("autofeed") is not True:
        return member.guild_permissions.manage_guild
    if not can_create(host, member, channel):
        return False
    try:
        referenced_mentions(guild, job)
    except (ValueError, TypeError):
        return False
    return True


def get_jobs(host, guild_id):
    try:
        data = json.loads(host["guild_config_get"](guild_id, CONFIG_KEY) or "[]")
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


def atomic_change(host, guild_id, transform, expected=None):
    """Serialize multi-user edits; do not overwrite another administrator's writes."""
    conn = host["db_connect"]()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT value FROM guild_settings WHERE guild_id=? AND key=?",
                           (guild_id, CONFIG_KEY)).fetchone()
        raw = row[0] if row else None
        if expected is not None and raw != expected:
            raise ValueError("conflict")
        jobs = json.loads(raw or "[]")
        if not isinstance(jobs, list):
            raise ValueError("invalid")
        new_jobs, operation = transform(jobs, conn)
        if len(new_jobs) > MAX_SERVER:
            raise ValueError("quota")
        content = json.dumps(new_jobs, ensure_ascii=False, separators=(",", ":"))
        conn.execute("""INSERT INTO guild_settings(guild_id,key,value) VALUES(?,?,?)
                     ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value""",
                     (guild_id, CONFIG_KEY, content))
        conn.execute("UPDATE guild_config SET updated_at=? WHERE guild_id=?",
                     (datetime.now(timezone.utc).isoformat(), guild_id))
        conn.commit()
        return operation
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()




def persist_schedule(host, guild_id, actor, job, *, snapshot=None, editing=False):
    """Save both /programar and /setup drafts atomically, without duplicating rows."""
    def apply(jobs, conn):
        if editing:
            original = next((old for old in jobs if old.get("id") == job["id"]), None)
            if not original or not can_manage(actor, original):
                raise ValueError("missing")
            if original.get("autofeed") is not True:
                raise ValueError("missing")
            row = conn.execute(
                "SELECT status FROM message_schedule_state WHERE guild_id=? AND job_id=?",
                (guild_id, job["id"])).fetchone()
            if row and row[0] == "sending":
                raise ValueError("conflict")
            jobs = [{k: v for k, v in job.items() if k not in ("guild", "requester")}
                    if old.get("id") == job["id"] else old for old in jobs]
            conn.execute(
                "UPDATE message_schedule_state SET status=?,next_run=?,detail=NULL "
                "WHERE guild_id=? AND job_id=?",
                ("paused" if job.get("paused") else "pending",
                 job["start"], guild_id, job["id"]))
        else:
            if any(old.get("id") == job["id"] for old in jobs):
                raise ValueError("conflict")
            limit = (MAX_SERVER if actor.guild_permissions.manage_guild
                     else policy(host, guild_id)["max_per_member"])
            if sum(old.get("author") == job["author"] for old in jobs) >= limit:
                raise ValueError("quota")
            jobs.append({k: v for k, v in job.items()
                         if k not in ("guild", "requester")})
        return jobs, job["id"]
    return atomic_change(host, guild_id, apply, expected=snapshot)

def start_from_form(value, zone):
    try:
        local = datetime.fromisoformat(value.strip().replace(" ", "T"))
        if local.tzinfo is not None:
            raise ValueError("timezone")
        tz = ZoneInfo(zone)
        check = local.replace(tzinfo=tz)
        if check.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != local:
            raise ValueError("time")
        if check.utcoffset() != local.replace(tzinfo=tz, fold=1).utcoffset():
            raise ValueError("ambiguous")
        start = check.astimezone(timezone.utc)
        if start <= datetime.now(timezone.utc) + timedelta(minutes=1):
            raise ValueError("past")
        return start
    except Exception as exc:
        raise ValueError("invalid") from exc


def interval_seconds(value):
    match = re.fullmatch(r"([1-9]\d{0,4})([mhd])", value.strip().lower())
    if not match:
        raise ValueError("invalid")
    seconds = int(match.group(1)) * {"m": 60, "h": 3600, "d": 86400}[match.group(2)]
    if not 3600 <= seconds <= 365 * 86400:
        raise ValueError("invalid")
    return seconds


def show_job(job, *, detail=True):
    rid = job.get("role")
    frequency = job.get("repeat", "ninguna")
    if frequency == "intervalo":
        frequency += " · " + job.get("interval", "")
    if frequency == "custom":
        parts = job.get("repeat_parts") or {}
        frequency += " · " + ", ".join(f"{value} {key}" for key, value in parts.items() if value)
    when = job.get("start", "")
    try:
        when = f"<t:{int(datetime.fromisoformat(when).timestamp())}:F>"
    except (ValueError, TypeError):
        pass
    lines = [f"ID: {job['id']}", f"{tr('channel_label')}: <#{job['channel']}>",
             f"{tr('frequency_label')}: {frequency}", f"{tr('start_label')}: {when}",
             f"{tr('mention_label')}: {('<@&' + str(rid) + '>') if rid else tr('no_role')}"]
    if detail:
        message = job.get("text") or ((job.get("embed") or {}).get("description") if job.get("embed") else None) or (
            tr("template_label") + ": " + str(job.get("template") or ""))
        lines.append(tr("content_label") + ": " + message[:700])
    return "\n".join(lines)


def is_ready(interaction, host, channel, role=None):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        return False
    me = interaction.guild.me
    bot_perms = channel.permissions_for(me) if me else discord.Permissions.none()
    if not can_create(host, interaction.user, channel):
        return False
    if not (bot_perms.view_channel and bot_perms.send_messages and bot_perms.embed_links):
        return False
    if role and (role.guild.id != interaction.guild.id or not role.mentionable):
        return False
    return True


async def respond_error(interaction, key):
    message = tr(key)
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


class DraftConfirm(discord.ui.View):
    def __init__(self, host, job, *, prior=None):
        super().__init__(timeout=300)
        self.host, self.job, self.prior = host, job, prior
        self.owner_id = job["requester"]
        self.save.label, self.discard.label = tr("save"), tr("discard")
        self.guild_id = job["guild"]
        self.done = False

    @guild_context
    async def interaction_check(self, interaction):
        if (self.done or interaction.guild is None or interaction.guild.id != self.guild_id
                or interaction.user.id != self.owner_id):
            await respond_error(interaction, "denied")
            return False
        return True

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success)
    @guild_context
    async def save(self, interaction, button):
        job = self.job
        guild = interaction.guild
        channel = guild.get_channel(job["channel"])
        role = guild.get_role(job.get("role")) if job.get("role") else None
        if not isinstance(channel, discord.TextChannel) or not is_ready(interaction, self.host, channel, role):
            return await respond_error(interaction, "denied")
        if job.get("role") and role is None:
            return await respond_error(interaction, "role")
        try:
            referenced_mentions(guild, job)
        except ValueError:
            return await respond_error(interaction, "role")
        if not job.get("text") and not job.get("embed") and not any(
            item["name"] == job.get("template") for item in self.host["heraldo_template_list"](guild.id)
        ):
            return await respond_error(interaction, "content")
        try:
            persist_schedule(self.host, guild.id, interaction.user, job,
                             snapshot=self.prior, editing=self.prior is not None)
        except ValueError as exc:
            return await respond_error(interaction, ("changed" if str(exc) == "conflict" else str(exc)) if str(exc) in ("quota", "missing", "conflict") else "invalid")
        self.done = True
        self.stop()
        await interaction.response.edit_message(content=tr("saved") + "\n" + show_job(job), embed=None, view=None)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger)
    @guild_context
    async def discard(self, interaction, button):
        self.done = True
        self.stop()
        await interaction.response.edit_message(content=tr("discarded"), embed=None, view=None)


class FeedModal(discord.ui.Modal, title="Programar mensaje"):
    def __init__(self, host, guild_id, author, channel_id, repeat, role_id, template=None, job=None):
        super().__init__()
        self.title = tr("modal")
        self.host, self.guild_id, self.author = host, guild_id, author
        self.channel_id, self.repeat, self.role_id = channel_id, repeat, role_id
        self.template, self.job = template, job
        self.snapshot = host["guild_config_get"](guild_id, CONFIG_KEY) if job else None
        self.message = discord.ui.TextInput(label="Mensaje", style=discord.TextStyle.paragraph,
                                            required=not bool(template or (job or {}).get("embed")), max_length=1900,
                                            default=(job or {}).get("text", ""))
        self.date = discord.ui.TextInput(label="Fecha y hora local (AAAA-MM-DD HH:MM)",
                                         placeholder="2026-10-30 18:00", max_length=24,
                                         default=((datetime.fromisoformat(job["start"]).astimezone(
                                             ZoneInfo(job["zone"])).strftime("%Y-%m-%d %H:%M")) if job else None))
        self.interval = discord.ui.TextInput(label="Intervalo (ej. 6h, 2d)", required=False,
                                             max_length=10, default=(job or {}).get("interval", ""))
        self.message.label = tr("msg")
        self.date.label = tr("date")
        self.interval.label = tr("interval_ui")
        self.add_item(self.message)
        self.add_item(self.date)
        self.add_item(self.interval)

    @guild_context
    async def on_submit(self, interaction):
        with use_guild(self.guild_id):
            try:
                zone = (self.job or {}).get("zone", "America/Santo_Domingo")
                start = start_from_form(str(self.date), zone)
                if self.repeat == "intervalo":
                    interval_seconds(str(self.interval))
                text = str(self.message).strip()
                if not text and not self.template and not (self.job or {}).get("embed"):
                    raise ValueError("content")
                job = {
                    "id": self.job["id"] if self.job else uuid.uuid4().hex[:12],
                    "guild": self.guild_id, "channel": self.channel_id,
                    "author": self.author, "start": start.isoformat(), "zone": zone,
                    "repeat": self.repeat, "interval": str(self.interval).strip() if self.repeat == "intervalo" else "",
                    "text": text, "template": self.template, "role": self.role_id,
                    "autofeed": True, "paused": (self.job or {}).get("paused", False),
                    "embed": (self.job or {}).get("embed"),
                    "repeat_parts": (self.job or {}).get("repeat_parts") if self.repeat == "custom" else None,
                    "requester": interaction.user.id,
                }
            except ValueError as exc:
                return await respond_error(interaction, "content" if str(exc) == "content" else "invalid")
            raw = self.snapshot if self.job else None
            view = DraftConfirm(self.host, job, prior=raw)
            await interaction.response.send_message(
                content=tr("preview") + "\n" + show_job(job), view=view,
                ephemeral=True, allowed_mentions=discord.AllowedMentions.none())


class ActionConfirm(discord.ui.View):
    def __init__(self, host, job, action, channel_id=None, *, from_setup=False):
        super().__init__(timeout=180)
        self.host, self.job, self.action = host, job, action
        self.channel_id = channel_id
        self.from_setup = from_setup
        self.owner_id, self.guild_id = job["author"], job["guild"]
        self.finished = False
        self.snapshot = host["guild_config_get"](self.guild_id, CONFIG_KEY)
        self.confirm.style = discord.ButtonStyle.danger if action == "eliminar" else discord.ButtonStyle.success
        self.confirm.label = tr("delete") if action == "eliminar" else tr("save")
        self.cancel.label = tr("discard")

    @guild_context
    async def interaction_check(self, interaction):
        if self.finished or interaction.guild is None or interaction.guild.id != self.guild_id:
            await respond_error(interaction, "denied")
            return False
        actual = next((j for j in get_jobs(self.host, self.guild_id) if j.get("id") == self.job["id"]), None)
        if actual is None or not can_manage(interaction.user, actual):
            await respond_error(interaction, "missing")
            return False
        return True

    @discord.ui.button(label="Confirmar cambios", style=discord.ButtonStyle.success)
    @guild_context
    async def confirm(self, interaction, button):
        if self.action == "mover":
            channel = interaction.guild.get_channel(self.channel_id)
            if not isinstance(channel, discord.TextChannel) or not is_ready(interaction, self.host, channel):
                return await respond_error(interaction, "denied")
        try:
            def apply(jobs, conn):
                found = next((j for j in jobs if j["id"] == self.job["id"]), None)
                if found is None or not can_manage(interaction.user, found):
                    raise ValueError("missing")
                if self.action == "eliminar":
                    jobs = [j for j in jobs if j["id"] != found["id"]]
                    conn.execute("DELETE FROM message_schedule_state WHERE guild_id=? AND job_id=?",
                                 (self.guild_id, found["id"]))
                elif self.action == "silenciar":
                    found["role"] = None
                elif self.action == "mover":
                    found["channel"] = self.channel_id
                else:
                    raise ValueError("invalid")
                return jobs, found["id"]
            atomic_change(self.host, self.guild_id, apply, expected=self.snapshot)
        except ValueError as exc:
            return await respond_error(interaction, ("changed" if str(exc) == "conflict" else str(exc)) if str(exc) in ("missing", "conflict") else "invalid")
        self.finished = True
        self.stop()
        if self.from_setup:
            from autofeed_setup import setup_panel
            content, view = setup_panel(self.host, self.guild_id, interaction.user.id)
            await interaction.response.edit_message(
                content=(tr("removed") if self.action == "eliminar" else tr("saved")) + "\n\n" + content,
                embed=None, view=view)
        else:
            await interaction.response.edit_message(
                content=tr("removed") if self.action == "eliminar" else tr("saved"), view=None)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger)
    @guild_context
    async def cancel(self, interaction, button):
        self.finished = True
        self.stop()
        if self.from_setup:
            from autofeed_setup import setup_panel
            content, view = setup_panel(self.host, self.guild_id, interaction.user.id)
            await interaction.response.edit_message(content=content, embed=None, view=view)
        else:
            await interaction.response.edit_message(content=tr("discarded"), view=None)


def set_paused(host, guild_id, job_id, actor, pause):
    from message_automation import next_occurrence
    now = datetime.now(timezone.utc)
    def apply(jobs, conn):
        job = next((j for j in jobs if j.get("id") == job_id), None)
        if job is None or not job.get("autofeed") or not can_manage(actor, job):
            raise ValueError("missing")
        if pause:
            job["paused"] = True
            conn.execute("UPDATE message_schedule_state SET status='paused' WHERE guild_id=? AND job_id=?",
                         (guild_id, job_id))
        else:
            if job.get("repeat") == "ninguna" and datetime.fromisoformat(job["start"]) <= now:
                raise ValueError("past")
            job["paused"] = False
            due = (job["start"] if datetime.fromisoformat(job["start"]) > now
                   else next_occurrence(job, now))
            conn.execute("INSERT INTO message_schedule_state(guild_id,job_id,next_run,status) VALUES(?,?,?,'pending') ON CONFLICT(guild_id,job_id) DO UPDATE SET next_run=excluded.next_run,status='pending',detail=NULL",
                         (guild_id, job_id, due))
        return jobs, job_id
    return atomic_change(host, guild_id, apply)


class ManageView(discord.ui.View):
    def __init__(self, host, guild_id, viewer_id, jobs, *, from_setup=False):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.viewer_id = host, guild_id, viewer_id
        self.from_setup = from_setup
        self.back.label = tr("back")
        self.selected = None
        self.edit.label, self.silence.label, self.delete.label = tr("edit"), tr("silence"), tr("delete")
        self.toggle.label = tr("pause") + " / " + tr("resume")
        select = discord.ui.Select(placeholder=tr("choose"), row=0, options=[
            discord.SelectOption(label=(j["id"] + " · " + (j.get("text") or j.get("template") or tr("msg"))[:60])[:100],
                                 value=j["id"]) for j in jobs[:25]])
        select.callback = self.select_job
        self.add_item(select)

    @guild_context
    async def interaction_check(self, interaction):
        if interaction.guild is None or interaction.guild.id != self.guild_id or interaction.user.id != self.viewer_id:
            await respond_error(interaction, "denied")
            return False
        return True

    def selected_job(self, actor):
        return next((j for j in get_jobs(self.host, self.guild_id)
                     if j.get("id") == self.selected and j.get("autofeed") and can_manage(actor, j)), None)

    @guild_context
    async def select_job(self, interaction):
        self.selected = interaction.data["values"][0]
        job = self.selected_job(interaction.user)
        if job is None:
            return await respond_error(interaction, "missing")
        self.toggle.label = tr("resume") if job.get("paused") else tr("pause")
        self.toggle.style = discord.ButtonStyle.success if job.get("paused") else discord.ButtonStyle.danger
        await interaction.response.edit_message(content=show_job(job), view=self)

    @discord.ui.button(label="Editar", style=discord.ButtonStyle.primary, row=1)
    @guild_context
    async def edit(self, interaction, button):
        job = self.selected_job(interaction.user)
        if job is None:
            return await respond_error(interaction, "missing")
        if self.from_setup:
            from autofeed_setup import AutofeedEditorView
            editor = AutofeedEditorView(self.host, self.guild_id, self.viewer_id, job=job)
            await interaction.response.edit_message(content=editor.summary(), embed=None, view=editor)
        else:
            await interaction.response.send_modal(FeedModal(
                self.host, self.guild_id, job["author"], job["channel"],
                job["repeat"], job.get("role"), job.get("template"), job))

    @discord.ui.button(label="Pausar / Reanudar", style=discord.ButtonStyle.secondary, row=1)
    @guild_context
    async def toggle(self, interaction, button):
        job = self.selected_job(interaction.user)
        if job is None:
            return await respond_error(interaction, "missing")
        paused = not job.get("paused", False)
        try:
            set_paused(self.host, self.guild_id, job["id"], interaction.user, paused)
        except ValueError:
            return await respond_error(interaction, "invalid")
        button.label = tr("resume") if paused else tr("pause")
        button.style = discord.ButtonStyle.success if paused else discord.ButtonStyle.danger
        current = self.selected_job(interaction.user)
        await interaction.response.edit_message(
            content=tr("paused" if paused else "resumed") + "\n\n" + show_job(current),
            view=self)

    @discord.ui.button(label="Silenciar", style=discord.ButtonStyle.primary, row=1)
    @guild_context
    async def silence(self, interaction, button):
        job = self.selected_job(interaction.user)
        if job is None:
            return await respond_error(interaction, "missing")
        view = ActionConfirm(self.host, {**job, "guild": self.guild_id}, "silenciar",
                             from_setup=self.from_setup)
        await interaction.response.edit_message(content=tr("preview") + "\n" + show_job(job), view=view)

    @discord.ui.button(label="Eliminar", style=discord.ButtonStyle.danger, row=2)
    @guild_context
    async def delete(self, interaction, button):
        job = self.selected_job(interaction.user)
        if job is None:
            return await respond_error(interaction, "missing")
        view = ActionConfirm(self.host, {**job, "guild": self.guild_id}, "eliminar",
                             from_setup=self.from_setup)
        await interaction.response.edit_message(content=tr("preview") + "\n" + show_job(job), view=view)


    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
    @guild_context
    async def back(self, interaction, button):
        if self.from_setup:
            from autofeed_setup import setup_panel
            content, view = setup_panel(self.host, self.guild_id, self.viewer_id)
            await interaction.response.edit_message(content=content, embed=None, view=view)
        else:
            await interaction.response.edit_message(content=tr("discarded"), view=None)


class PolicyView(discord.ui.View):
    def __init__(self, host, guild_id, viewer_id, *, return_to_setup=False):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.viewer_id = host, guild_id, viewer_id
        self.return_to_setup = return_to_setup
        self.original = host["guild_config_get"](guild_id, POLICY_KEY)
        self.current = policy(host, guild_id)
        self.channels = discord.ui.ChannelSelect(
            placeholder="Canales permitidos para miembros", min_values=0, max_values=10,
            channel_types=[discord.ChannelType.text], row=0)
        self.channels.callback = self.pick_channels
        self.add_item(self.channels)
        self.roles = discord.ui.RoleSelect(
            placeholder="Roles que pueden programar", min_values=0, max_values=10, row=1)
        self.roles.callback = self.pick_roles
        self.add_item(self.roles)
        self.activate.label = tr("pause") if self.current["enabled"] else tr("activate")
        self.save.label, self.discard.label = tr("save"), tr("discard")
        self.back.label = tr("back")
        self.channels.placeholder, self.roles.placeholder = tr("channels"), tr("roles_ui")
        self.activate.style = discord.ButtonStyle.danger if self.current["enabled"] else discord.ButtonStyle.success

    def summary(self):
        return (tr("settings") + "\n" + tr("status_label") + ": " + (tr("enabled_label") if self.current["enabled"] else tr("disabled_label"))
                + "\n" + tr("channels") + ": " + (", ".join(f"<#{c}>" for c in self.current["channels"]) or "—")
                + "\n" + tr("roles_ui") + ": " + (", ".join(f"<@&{r}>" for r in self.current["roles"]) or "—")
                + "\n" + tr("limit_label") + ": " + str(self.current["max_per_member"])
                + "\n" + tr("policy_help"))

    @guild_context
    async def interaction_check(self, interaction):
        if interaction.guild is None or interaction.guild.id != self.guild_id or interaction.user.id != self.viewer_id or not interaction.user.guild_permissions.manage_guild:
            await respond_error(interaction, "denied")
            return False
        return True

    @guild_context
    async def pick_channels(self, interaction):
        self.current["channels"] = [item.id for item in self.channels.values]
        await interaction.response.edit_message(content=self.summary(), view=self)

    @guild_context
    async def pick_roles(self, interaction):
        self.current["roles"] = [item.id for item in self.roles.values]
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    @guild_context
    async def save(self, interaction, button):
        latest = self.host["guild_config_get"](self.guild_id, POLICY_KEY)
        if (latest or None) != (self.original or None):
            return await respond_error(interaction, "changed")
        current = dict(self.current)
        current["enabled"] = policy(self.host, self.guild_id)["enabled"]
        self.host["guild_config_set"](self.guild_id, POLICY_KEY, json.dumps(current))
        self.original = self.host["guild_config_get"](self.guild_id, POLICY_KEY)
        self.current = policy(self.host, self.guild_id)
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger, row=2)
    @guild_context
    async def discard(self, interaction, button):
        self.original = self.host["guild_config_get"](self.guild_id, POLICY_KEY)
        self.current = policy(self.host, self.guild_id)
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Activar", style=discord.ButtonStyle.success, row=3)
    @guild_context
    async def activate(self, interaction, button):
        current = policy(self.host, self.guild_id)
        if not current["enabled"] and not current["channels"]:
            return await respond_error(interaction, "policy_needs")
        current["enabled"] = not current["enabled"]
        self.host["guild_config_set"](self.guild_id, POLICY_KEY, json.dumps(current))
        self.original = self.host["guild_config_get"](self.guild_id, POLICY_KEY)
        self.current["enabled"] = current["enabled"]
        button.label = tr("pause") if current["enabled"] else tr("activate")
        button.style = discord.ButtonStyle.danger if current["enabled"] else discord.ButtonStyle.success
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=3)
    @guild_context
    async def back(self, interaction, button):
        if self.return_to_setup:
            from autofeed_setup import setup_panel
            content, view = setup_panel(self.host, self.guild_id, self.viewer_id)
            await interaction.response.edit_message(content=content, embed=None, view=view)
        elif "HeraldoMessagesView" in self.host:
            parent = self.host["HeraldoMessagesView"](self.guild_id, self.viewer_id)
            await interaction.response.edit_message(
                content=self.host["heraldo_messages_command_content"](), view=parent)
        else:
            await interaction.response.edit_message(content=tr("discarded"), view=None)


def install(host):
    group = app_commands.Group(name="programar", description="Programar y administrar publicaciones.",
                               guild_only=True)

    @group.command(name="crear", description="Programar texto o una plantilla con vista previa.")
    @app_commands.choices(frecuencia=[
        app_commands.Choice(name="Una vez", value="ninguna"),
        app_commands.Choice(name="Diaria", value="diaria"),
        app_commands.Choice(name="Semanal", value="semanal"),
        app_commands.Choice(name="Mensual", value="mensual"),
        app_commands.Choice(name="Por intervalo", value="intervalo")])
    @guild_context
    async def crear(interaction: discord.Interaction, canal: discord.TextChannel,
                    frecuencia: app_commands.Choice[str], rol: discord.Role = None,
                    plantilla: str = None):
        if not is_ready(interaction, host, canal, rol):
            return await respond_error(interaction, "denied")
        if plantilla and not any(x["name"].casefold() == plantilla.casefold() for x in host["heraldo_template_list"](interaction.guild.id)):
            return await respond_error(interaction, "content")
        await interaction.response.send_modal(
            FeedModal(host, interaction.guild.id, interaction.user.id, canal.id, frecuencia.value,
                      rol.id if rol else None, plantilla))

    @group.command(name="listar", description="Consultar y administrar las publicaciones programadas.")
    @guild_context
    async def listar(interaction: discord.Interaction):
        jobs = [j for j in get_jobs(host, interaction.guild.id)
                if j.get("autofeed") and can_manage(interaction.user, j)]
        if not jobs:
            return await respond_error(interaction, "no_jobs")
        lines = [(j["id"] + " · <#" + str(j["channel"]) + "> · "
                  + (tr("disabled_label") if j.get("paused") else j["repeat"])) for j in jobs[:25]]
        await interaction.response.send_message(
            content="\n".join(lines), view=ManageView(host, interaction.guild.id, interaction.user.id, jobs),
            ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @group.command(name="editar", description="Editar el contenido y horario de una programación.")
    @guild_context
    async def editar(interaction: discord.Interaction, identificador: str):
        job = next((j for j in get_jobs(host, interaction.guild.id) if j.get("id") == identificador and j.get("autofeed") and can_manage(interaction.user, j)), None)
        if job is None:
            return await respond_error(interaction, "missing")
        await interaction.response.send_modal(FeedModal(host, interaction.guild.id, job["author"], job["channel"], job["repeat"], job.get("role"), job.get("template"), job))

    @group.command(name="pausar", description="Detener temporalmente una programación.")
    @guild_context
    async def pausar(interaction: discord.Interaction, identificador: str):
        try:
            set_paused(host, interaction.guild.id, identificador, interaction.user, True)
        except ValueError:
            return await respond_error(interaction, "missing")
        await interaction.response.send_message(tr("paused"), ephemeral=True)

    @group.command(name="reanudar", description="Reactivar una programación pausada.")
    @guild_context
    async def reanudar(interaction: discord.Interaction, identificador: str):
        try:
            set_paused(host, interaction.guild.id, identificador, interaction.user, False)
        except ValueError:
            return await respond_error(interaction, "invalid")
        await interaction.response.send_message(tr("resumed"), ephemeral=True)

    @group.command(name="silenciar", description="Retirar la mención de rol sin pausar publicaciones.")
    @guild_context
    async def silenciar(interaction: discord.Interaction, identificador: str):
        job = next((j for j in get_jobs(host, interaction.guild.id) if j.get("id") == identificador and j.get("autofeed") and can_manage(interaction.user, j)), None)
        if job is None:
            return await respond_error(interaction, "missing")
        await interaction.response.send_message(
            tr("preview") + "\n" + show_job(job),
            view=ActionConfirm(host, {**job, "guild": interaction.guild.id}, "silenciar"), ephemeral=True)

    @group.command(name="mover", description="Cambiar el canal de destino después de guardar.")
    @guild_context
    async def mover(interaction: discord.Interaction, identificador: str, canal: discord.TextChannel):
        job = next((j for j in get_jobs(host, interaction.guild.id) if j.get("id") == identificador and j.get("autofeed") and can_manage(interaction.user, j)), None)
        if job is None:
            return await respond_error(interaction, "missing")
        if not is_ready(interaction, host, canal):
            return await respond_error(interaction, "denied")
        await interaction.response.send_message(
            tr("preview") + "\n" + show_job({**job, "channel": canal.id}),
            view=ActionConfirm(host, {**job, "guild": interaction.guild.id}, "mover", canal.id), ephemeral=True)

    @group.command(name="eliminar", description="Eliminar una programación previa confirmación.")
    @guild_context
    async def eliminar(interaction: discord.Interaction, identificador: str):
        job = next((j for j in get_jobs(host, interaction.guild.id) if j.get("id") == identificador and j.get("autofeed") and can_manage(interaction.user, j)), None)
        if job is None:
            return await respond_error(interaction, "missing")
        await interaction.response.send_message(
            tr("preview") + "\n" + show_job(job),
            view=ActionConfirm(host, {**job, "guild": interaction.guild.id}, "eliminar"), ephemeral=True)

    @group.command(name="configurar", description="Configurar canales y roles autorizados.")
    @guild_context
    async def configurar(interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            return await respond_error(interaction, "denied")
        view = PolicyView(host, interaction.guild.id, interaction.user.id)
        await interaction.response.send_message(view.summary(), view=view, ephemeral=True)

    host["bot"].tree.add_command(group)
    return group
