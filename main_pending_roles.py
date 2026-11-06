"""Pending moderation-role restoration, isolated by guild and member.

Only roles from an actual prior condemnation release can appear in this list.
A fresh admin confirmation rechecks live role hierarchy, permissions and state.
"""
from __future__ import annotations

import json
import discord


def pending_get(host, guild_id: int, user_id: int) -> list[int]:
    raw = host["guild_config_get"](guild_id, f"condemnation_pending_roles:{user_id}")
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        return sorted({int(rid) for rid in data if int(rid) > 0})
    except (ValueError, TypeError, OverflowError):
        return []


def pending_set(host, guild_id: int, user_id: int, role_ids) -> None:
    values = sorted({int(rid) for rid in role_ids if int(rid) > 0})
    host["guild_config_set"](
        guild_id, f"condemnation_pending_roles:{user_id}", json.dumps(values))


MESSAGES = {
    "es-419": {
        "denied": "Solo un moderador autorizado con permisos para gestionar roles puede continuar.",
        "empty": "Este miembro no tiene roles pendientes de restauración.",
        "active": "El miembro sigue condenado. No se restaurarán roles.",
        "begin": "Hay **{count}** roles pendientes para <@{member}>. Confirma el reintento.",
        "stale": "La lista cambió mientras confirmabas. Vuelve a abrir el comando.",
        "missing": "El miembro ya no está en el servidor.",
        "blocked": "Ningún rol pendiente es asignable con los permisos y jerarquía actuales.",
        "failed": "Discord no permitió restaurar los roles. La lista pendiente se conserva.",
        "done": "**{added}** roles restaurados; **{remaining}** pendientes.",
        "cancelled": "Restauración cancelada.",
        "confirm": "Confirmar restauración", "cancel": "Cancelar",
    },
    "en-US": {
        "denied": "An authorized moderator with Manage Roles permission is required.",
        "empty": "This member has no pending roles to restore.",
        "active": "This member is still condemned. Roles cannot be restored.",
        "begin": "**{count}** roles are pending for <@{member}>. Confirm the retry.",
        "stale": "The pending list changed. Open the command again.",
        "missing": "The member is no longer in this server.",
        "blocked": "No pending roles can be assigned with current permissions and hierarchy.",
        "failed": "Discord rejected the role update. Pending roles were preserved.",
        "done": "**{added}** roles restored; **{remaining}** still pending.",
        "cancelled": "Restoration cancelled.",
        "confirm": "Confirm restoration", "cancel": "Cancel",
    },
    "pt-BR": {
        "denied": "É necessário ser moderador autorizado e ter permissão para gerenciar cargos.",
        "empty": "Este membro não possui cargos pendentes para restaurar.",
        "active": "O membro ainda está condenado. Não é possível restaurar cargos.",
        "begin": "Há **{count}** cargos pendentes para <@{member}>. Confirme a tentativa.",
        "stale": "A lista pendente mudou. Abra o comando novamente.",
        "missing": "O membro não está mais neste servidor.",
        "blocked": "Nenhum cargo pendente pode ser atribuído com as permissões atuais.",
        "failed": "Discord rejeitou a atribuição. Os cargos pendentes foram preservados.",
        "done": "**{added}** cargos restaurados; **{remaining}** ainda pendentes.",
        "cancelled": "Restauração cancelada.",
        "confirm": "Confirmar restauração", "cancel": "Cancelar",
    },
}
_IN_PROGRESS: set[tuple[int, int]] = set()


def _lang(host, guild_id):
    return MESSAGES.get(host.get("guild_language", lambda gid: "es-419")(guild_id),
                        MESSAGES["es-419"])


class PendingRestoreView(discord.ui.View):
    def __init__(self, host, guild_id: int, owner_id: int, member_id: int):
        super().__init__(timeout=300)
        self.host = host
        self.guild_id, self.owner_id, self.member_id = guild_id, owner_id, member_id
        self.original = pending_get(host, guild_id, member_id)
        self.confirm.label = self.t("confirm")
        self.cancel.label = self.t("cancel")

    def t(self, key, **fmt):
        return _lang(self.host, self.guild_id)[key].format(**fmt)

    async def interaction_check(self, interaction):
        perms = getattr(interaction.user, "guild_permissions", None)
        valid = (
            interaction.guild is not None and interaction.guild.id == self.guild_id
            and interaction.user.id == self.owner_id and perms is not None
            and perms.manage_guild and perms.manage_roles
        )
        if not valid:
            await interaction.response.send_message(self.t("denied"), ephemeral=True)
        return valid

    @discord.ui.button(label="Confirmar restauración", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        guild = interaction.guild
        key = (guild.id, self.member_id)
        if key in _IN_PROGRESS:
            return await interaction.response.send_message(self.t("stale"), ephemeral=True)
        pending = pending_get(self.host, self.guild_id, self.member_id)
        if not pending or pending != self.original:
            return await interaction.response.send_message(self.t("stale"), ephemeral=True)
        if self.host["condemnation_get"](guild.id, self.member_id) is not None:
            return await interaction.response.send_message(self.t("active"), ephemeral=True)
        bot = guild.me
        if bot is None or not bot.guild_permissions.manage_roles:
            return await interaction.response.send_message(self.t("denied"), ephemeral=True)
        _IN_PROGRESS.add(key)
        try:
            await interaction.response.defer()
            try:
                member = guild.get_member(self.member_id) or await guild.fetch_member(self.member_id)
            except discord.HTTPException:
                return await interaction.edit_original_response(content=self.t("missing"), view=None)
            if (self.host["condemnation_get"](guild.id, self.member_id) is not None
                    or pending_get(self.host, guild.id, self.member_id) != pending):
                return await interaction.edit_original_response(content=self.t("stale"), view=None)
            already = {r.id for r in member.roles}
            allowed = []
            missing = []
            for rid in pending:
                role = guild.get_role(rid)
                if rid in already:
                    continue
                if (role is None or role.managed or role.is_default()
                        or not role.is_assignable() or role >= bot.top_role
                        or (not interaction.user.guild_permissions.administrator
                            and interaction.user.id != guild.owner_id
                            and role >= interaction.user.top_role)):
                    missing.append(rid)
                    continue
                allowed.append(role)
            if not allowed and len(missing) == len(pending):
                return await interaction.edit_original_response(content=self.t("blocked"), view=None)
            try:
                if allowed:
                    await member.add_roles(*allowed, reason=f"Restauración autorizada por {interaction.user.id}")
            except discord.HTTPException:
                return await interaction.edit_original_response(content=self.t("failed"), view=None)
            pending_set(self.host, guild.id, self.member_id, missing)
            self.stop()
            await interaction.edit_original_response(
                content=self.t("done", added=len(allowed), remaining=len(missing)), view=None)
            try:
                await self.host["log_embed"](
                    guild, "Roles pendientes restaurados",
                    f"{interaction.user.mention}: <@{self.member_id}> "
                    f"{len(allowed)} restaurados · {len(missing)} pendientes.",
                    discord.Color.blurple())
            except discord.HTTPException:
                pass
        finally:
            _IN_PROGRESS.discard(key)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content=self.t("cancelled"), view=None)


def create_confirmation(host, guild_id, owner_id, member_id):
    rows = pending_get(host, guild_id, member_id)
    lang = _lang(host, guild_id)
    if not rows:
        return lang["empty"], None
    return lang["begin"].format(count=len(rows), member=member_id), PendingRestoreView(
        host, guild_id, owner_id, member_id)
