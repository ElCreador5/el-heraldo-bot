"""Panel independiente y seguro del comando /purge (sin datos persistentes).

La vista previa conserva únicamente IDs; nunca vuelve a buscar al confirmar.
"""
from __future__ import annotations

from collections import Counter
from purge_period import PurgePeriodError, parse_purge_period
import asyncio
import re
import secrets

import discord
from heraldo_datetime import clock_style
from operation_progress import ProgressReporter, compact_operation_status, status_text

# Etiquetas exclusivas de /purge, sin dependencia del sistema global de idiomas.
PURGE_LABELS = {
  "es-419": {
    "all": "Todos los mensajes",
    "all_button": "Todos",
    "all_kind": "Cualquier mensaje",
    "audit": "Registro de limpieza",
    "audit_missing": "No se puede completar la operación: el canal de registros del bot no está disponible.",
    "back": "Volver",
    "busy": "Hay una operación en curso. No se puede modificar el panel.",
    "channel": "Canal",
    "channel_reset": "Quitar canal",
    "choose": "Selecciona al menos un usuario.",
    "close": "Cerrar",
    "closed": "Panel cerrado sin eliminar mensajes.",
    "confirm": "Confirmar eliminación",
    "deleted": "Eliminados",
    "done": "Resultado de la limpieza",
    "expired": "El panel de /purge caducó o el bot se reinició. No se ejecutó ninguna eliminación al pulsar este botón. Ejecuta /purge y confirma en la nueva vista previa.",
    "failed": "No eliminados",
    "finished": "Operación terminada",
    "ids": "Añadir usuarios por ID",
    "ids_input": "ID de usuarios separados por comas",
    "invalid": "Introduce fechas u horas válidas según /formato_fecha, y un límite positivo. Si solo escribes horas, completa Desde y Hasta.",
    "kind": "Tipo",
    "limit": "Límite por usuario",
    "links": "Solo enlaces",
    "log_status": "Resultado",
    "max_users": "Máximo 25 usuarios en total.",
    "mode_note": "Desde y Hasta admiten fecha, hora de hoy o fecha con hora. Una fecha sola cubre el día completo; una hora sola exige ambos campos. «Todas» quita los límites.",
    "next": "Continuar",
    "no_access": "No hay canales accesibles con los permisos necesarios.",
    "no_messages": "No se encontraron mensajes; no hay nada que eliminar.",
    "none": "Sin seleccionar",
    "owner": "Este panel pertenece a otro moderador.",
    "partial": "Algunos canales no pudieron revisarse; el total corresponde únicamente a los examinados.",
    "per_user": "Desglose por usuario",
    "period_from": "Desde (fecha u hora)",
    "period_to": "Hasta (fecha u hora)",
    "permission": "No tienes permisos para administrar mensajes en esta operación.",
    "preview_help": "Esta es una fotografía de los mensajes encontrados; solo esos ID podrán eliminarse. Los mensajes nuevos quedan fuera.",
    "quantity": "Cantidad máxima por usuario",
    "range": "Intervalo",
    "range_error": "Intervalo inválido: Desde debe ser anterior a Hasta.",
    "review": "Confirmar limpieza",
    "running": "Otra limpieza ya está procesando uno de los usuarios seleccionados.",
    "scanned": "Canales examinados",
    "scope": "Indica un intervalo o un límite, o activa «Todos».",
    "selected": "Usuarios seleccionados",
    "settings": "Fechas, horas y límite",
    "skipped": "Canales omitidos",
    "stale": "La vista previa ya no es válida. Ejecuta «Continuar» otra vez.",
    "text": "Solo texto (sin imágenes ni vídeos)",
    "title": "🧹 Limpieza de mensajes",
    "total": "Mensajes encontrados",
    "unexpected": "No se pudo completar la búsqueda. No se eliminó ningún mensaje.",
    "users": "Usuarios",
    "whole": "Todos los canales",
    "wide": "La limpieza completa exige «Gestionar servidor»."
  },
  "en-US": {
    "all": "All messages",
    "all_button": "All",
    "all_kind": "Any message",
    "audit": "Cleanup audit",
    "audit_missing": "Cannot proceed: the bot's audit log channel is unavailable.",
    "back": "Back",
    "busy": "An operation is in progress. Changes are disabled.",
    "channel": "Channel",
    "channel_reset": "Clear channel",
    "choose": "Select at least one user.",
    "close": "Close",
    "closed": "Panel closed without deleting messages.",
    "confirm": "Confirm deletion",
    "deleted": "Deleted",
    "done": "Cleanup result",
    "expired": "The /purge panel expired or the bot restarted. No deletion was performed by this click. Run /purge again and confirm from a new preview.",
    "failed": "Not deleted",
    "finished": "Operation complete",
    "ids": "Add users by ID",
    "ids_input": "Comma-separated user IDs",
    "invalid": "Use valid dates or times as configured in /formato_fecha and a positive limit. For time-only ranges, fill in both From and Until.",
    "kind": "Type",
    "limit": "Limit per user",
    "links": "Links only",
    "log_status": "Result",
    "max_users": "Maximum 25 users in total.",
    "mode_note": "From and Until accept a date, today's time, or date and time. A date covers the full day; time-only ranges need both fields. All removes limits.",
    "next": "Continue",
    "no_access": "No channels are accessible with the required permissions.",
    "no_messages": "No messages were found.",
    "none": "Not selected",
    "owner": "This panel belongs to another moderator.",
    "partial": "Some channels could not be inspected; the count covers inspected channels only.",
    "per_user": "By user",
    "period_from": "From (date or time)",
    "period_to": "Until (date or time)",
    "permission": "You lack permission to manage messages for this operation.",
    "preview_help": "This is a fixed snapshot of message IDs. New messages cannot be added.",
    "quantity": "Maximum messages per user",
    "range": "Time range",
    "range_error": "Invalid interval: From must be earlier than Until.",
    "review": "Confirm cleanup",
    "running": "Another cleanup is already processing one of the selected users.",
    "scanned": "Channels scanned",
    "scope": "Set a time range or limit, or enable All.",
    "selected": "Selected users",
    "settings": "Dates, times and limit",
    "skipped": "Channels skipped",
    "stale": "The preview is no longer valid. Continue again.",
    "text": "Text only (no images/videos)",
    "title": "🧹 Message cleanup",
    "total": "Messages found",
    "unexpected": "The scan failed; no messages were deleted.",
    "users": "Users",
    "whole": "All channels",
    "wide": "Full cleanup requires Manage Server permission."
  },
  "pt-BR": {
    "all": "Todas as mensagens",
    "all_button": "Todas",
    "all_kind": "Qualquer mensagem",
    "audit": "Registro da limpeza",
    "audit_missing": "Impossível continuar: o canal de registro do bot está indisponível.",
    "back": "Voltar",
    "busy": "Uma operação está em andamento; alterações desativadas.",
    "channel": "Canal",
    "channel_reset": "Limpar canal",
    "choose": "Selecione pelo menos um usuário.",
    "close": "Fechar",
    "closed": "Painel fechado sem excluir mensagens.",
    "confirm": "Confirmar exclusão",
    "deleted": "Excluídas",
    "done": "Resultado da limpeza",
    "expired": "O painel de /purge expirou ou o bot foi reiniciado. Nenhuma exclusão foi feita com este clique. Execute /purge novamente e confirme em uma nova prévia.",
    "failed": "Não excluídas",
    "finished": "Operação concluída",
    "ids": "Adicionar IDs de usuários",
    "ids_input": "IDs separados por vírgulas",
    "invalid": "Informe datas ou horas válidas conforme /formato_fecha e um limite positivo. Para usar somente horas, preencha Desde e Até.",
    "kind": "Tipo",
    "limit": "Limite por usuário",
    "links": "Apenas links",
    "log_status": "Resultado",
    "max_users": "Máximo de 25 usuários.",
    "mode_note": "Desde e Até aceitam data, hora de hoje ou data com hora. Uma data cobre o dia todo; só horas exigem ambos os campos. Todas remove os limites.",
    "next": "Continuar",
    "no_access": "Não há canais acessíveis com as permissões necessárias.",
    "no_messages": "Nenhuma mensagem encontrada.",
    "none": "Não selecionado",
    "owner": "Este painel pertence a outro moderador.",
    "partial": "Alguns canais não puderam ser lidos; a contagem cobre apenas os analisados.",
    "per_user": "Por usuário",
    "period_from": "Desde (data ou hora)",
    "period_to": "Até (data ou hora)",
    "permission": "Você não tem permissão para gerenciar mensagens.",
    "preview_help": "Esta é uma lista fixa de IDs; mensagens novas não serão incluídas.",
    "quantity": "Máximo de mensagens por usuário",
    "range": "Período",
    "range_error": "Intervalo inválido: Desde deve ser anterior a Até.",
    "review": "Confirmar limpeza",
    "running": "Outra limpeza já está processando um usuário selecionado.",
    "scanned": "Canais analisados",
    "scope": "Defina um período/limite ou ative Todas.",
    "selected": "Usuários selecionados",
    "settings": "Datas, horários e limite",
    "skipped": "Canais ignorados",
    "stale": "A prévia expirou. Continue novamente.",
    "text": "Apenas texto (sem imagens ou vídeos)",
    "title": "🧹 Limpeza de mensagens",
    "total": "Mensagens encontradas",
    "unexpected": "A busca falhou; nenhuma mensagem foi excluída.",
    "users": "Usuários",
    "whole": "Todos os canais",
    "wide": "A limpeza completa requer Gerenciar Servidor."
  }
}


class PurgeRangeModal(discord.ui.Modal):
    def __init__(self, panel: "PurgePanel"):
        self.panel = panel
        super().__init__(title=panel.t("settings"))
        self.from_input = discord.ui.TextInput(
            label=panel.t("period_from"), required=False, max_length=40,
            placeholder=panel.period_hint(), default=panel.from_text or "",
        )
        self.to_input = discord.ui.TextInput(
            label=panel.t("period_to"), required=False, max_length=40,
            placeholder=panel.period_hint(), default=panel.to_text or "",
        )
        self.count_input = discord.ui.TextInput(
            label=panel.t("quantity"), required=False, max_length=12,
            default=str(panel.limit) if panel.limit is not None else "",
        )
        self.add_item(self.from_input)
        self.add_item(self.to_input)
        self.add_item(self.count_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not await self.panel.authorize(interaction):
            return
        raw_from = str(self.from_input).strip()
        raw_to = str(self.to_input).strip()
        raw_count = str(self.count_input).strip()
        try:
            period = parse_purge_period(
                raw_from, raw_to, mode=self.panel.date_mode, locale=self.panel.language,
            )
            count = int(raw_count) if raw_count else None
            if count is not None and count <= 0:
                raise ValueError("non-positive")
        except PurgePeriodError as exc:
            error = "range_error" if str(exc) == "order" else "invalid"
            await interaction.response.send_message(self.panel.t(error), ephemeral=True)
            return
        except (ValueError, OverflowError):
            await interaction.response.send_message(self.panel.t("invalid"), ephemeral=True)
            return
        self.panel.after, self.panel.before = period.after, period.before
        self.panel.display_from, self.panel.display_to = period.display_from, period.display_to
        self.panel.from_text, self.panel.to_text, self.panel.limit = raw_from, raw_to, count
        self.panel.everything = False
        self.panel.invalidate()
        await interaction.response.defer(ephemeral=True)
        await self.panel.refresh()



class PurgeUsersModal(discord.ui.Modal):
    """Permite seleccionar autores que ya abandonaron el servidor."""

    def __init__(self, panel: "PurgePanel"):
        self.panel = panel
        super().__init__(title=panel.t("ids"))
        self.ids_input = discord.ui.TextInput(
            label=panel.t("ids_input"), style=discord.TextStyle.paragraph,
            required=False, max_length=600,
            default=", ".join(str(uid) for uid in panel.manual_user_ids),
        )
        self.add_item(self.ids_input)

    async def on_submit(self, interaction: discord.Interaction):
        if not await self.panel.authorize(interaction):
            return
        raw = str(self.ids_input).strip()
        try:
            manual = tuple(dict.fromkeys(int(item) for item in re.split(r"[\s,;]+", raw) if item))
            combined = tuple(dict.fromkeys((*self.panel.selected_user_ids, *manual)))
            if any(uid <= 0 for uid in manual) or len(combined) > 25:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(self.panel.t("max_users"), ephemeral=True)
            return
        self.panel.manual_user_ids = manual
        self.panel.user_ids = combined
        self.panel.invalidate()
        await interaction.response.defer(ephemeral=True)
        await self.panel.refresh()


class PurgePanel(discord.ui.View):
    def __init__(
        self, interaction: discord.Interaction, *,
        language: str, footer, targets, matches, delete, log, parse_duration,
        max_minutes: int, running: set, audit_channel_id: int,
        date_mode: str = "discord", time_mode: str | None = None, format_datetime=None,
    ):
        super().__init__(timeout=900)
        self.origin = interaction
        self.guild_id = interaction.guild.id
        self.owner_id = interaction.user.id
        # La vista es temporal: el identificador permite reconocerla después de reiniciar.
        # No se restaura una confirmación antigua ni se conserva una purga pendiente.
        self.session_id = secrets.token_hex(8)
        self.language = language if language in PURGE_LABELS else "es-419"
        self.footer = footer
        self.targets = targets
        self.matches = matches
        self.delete = delete
        self.log = log
        self.parse_duration = parse_duration
        self.max_minutes = max_minutes
        self.running = running
        self.audit_channel_id = audit_channel_id
        self.date_mode = date_mode
        self.time_mode = time_mode
        self.format_datetime = format_datetime or (lambda dt: dt.strftime("%Y-%m-%d %H:%M"))
        self.user_ids: tuple[int, ...] = ()
        self.selected_user_ids: tuple[int, ...] = ()
        self.manual_user_ids: tuple[int, ...] = ()
        self.scanned_channels: dict[int, object] = {}
        self.channel_id: int | None = None
        self.kind = "all"
        self.everything = False
        self.after = self.before = None
        self.from_text = self.to_text = ""
        self.display_from = self.display_to = None
        self.limit: int | None = None
        self.snapshot: list[tuple[int, int, int]] | None = None
        self.scanned = self.skipped = 0
        self.busy = self.closed = False
        self._progress: str | None = None
        self._build()

    def t(self, key: str) -> str:
        return PURGE_LABELS[self.language][key]

    def period_hint(self) -> str:
        """Ejemplos para el formato configurado en el servidor."""
        date = ("2026-05-06" if self.date_mode == "iso" else
                "05/06/2026" if self.date_mode == "mdy12" or
                (self.date_mode == "discord" and self.language == "en-US")
                else "06/05/2026")
        clock = "6:00 PM" if clock_style(self.date_mode, self.time_mode) == "12h" else "18:00"
        return f"{date} {clock} · {clock}"

    def invalidate(self) -> None:
        self._progress = None
        self.snapshot = None
        self.scanned = self.skipped = 0
        self.scanned_channels = {}
        self._build()

    def _custom_id(self, action: str) -> str:
        return f"ehpurge:v1:{self.session_id}:{action}"

    def _button(self, key, style, row, callback):
        button = discord.ui.Button(
            label=self.t(key), style=style, row=row,
            custom_id=self._custom_id(key),
        )
        button.callback = callback
        self.add_item(button)

    def _build(self) -> None:
        self.clear_items()
        if self.closed:
            return
        if self.snapshot is not None:
            self._button("confirm", discord.ButtonStyle.danger, 0, self.confirm)
            self._button("back", discord.ButtonStyle.secondary, 0, self.back)
            self._button("close", discord.ButtonStyle.secondary, 0, self.close)
            return
        user_kwargs = {}
        if hasattr(discord, "SelectDefaultValue"):
            user_kwargs["default_values"] = [
                discord.SelectDefaultValue(id=uid, type=discord.SelectDefaultValueType.user)
                for uid in self.selected_user_ids
            ]
        try:
            self.user_select = discord.ui.UserSelect(
                placeholder=self.t("selected") + f": {len(self.user_ids)}/25",
                min_values=0, max_values=25, row=0, **user_kwargs,
            )
        except TypeError:
            self.user_select = discord.ui.UserSelect(
                placeholder=self.t("selected") + f": {len(self.user_ids)}/25",
                min_values=0, max_values=25, row=0,
            )
        self.user_select.custom_id = self._custom_id("users")
        self.user_select.callback = self.users_changed
        self.add_item(self.user_select)
        channel_kwargs = {}
        if self.channel_id is not None and hasattr(discord, "SelectDefaultValue"):
            channel_kwargs["default_values"] = [
                discord.SelectDefaultValue(
                    id=self.channel_id, type=discord.SelectDefaultValueType.channel,
                )
            ]
        try:
            self.channel_select = discord.ui.ChannelSelect(
                placeholder=self.t("channel") + ": " + (
                    str(self.channel_id) if self.channel_id else self.t("whole")
                ),
                min_values=0, max_values=1, row=1, **channel_kwargs,
            )
        except TypeError:
            self.channel_select = discord.ui.ChannelSelect(
                placeholder=self.t("channel") + ": " + (
                    str(self.channel_id) if self.channel_id else self.t("whole")
                ),
                min_values=0, max_values=1, row=1,
            )
        self.channel_select.custom_id = self._custom_id("channel")
        self.channel_select.callback = self.channel_changed
        self.add_item(self.channel_select)
        self.kind_select = discord.ui.Select(
            placeholder=self.t("kind"), min_values=1, max_values=1, row=2,
            options=[
                discord.SelectOption(label=self.t(k), value=v, default=self.kind == v)
                for v, k in (("all", "all_kind"), ("links", "links"), ("text", "text"))
            ],
        )
        self.kind_select.custom_id = self._custom_id("kind")
        self.kind_select.callback = self.kind_changed
        self.add_item(self.kind_select)
        self._button("settings", discord.ButtonStyle.primary, 3, self.open_range)
        self._button("all_button", discord.ButtonStyle.secondary, 3, self.toggle_all)
        self._button("channel_reset", discord.ButtonStyle.secondary, 3, self.clear_channel)
        self._button("ids", discord.ButtonStyle.secondary, 3, self.open_ids)
        self._button("next", discord.ButtonStyle.success, 4, self.continue_scan)
        self._button("close", discord.ButtonStyle.secondary, 4, self.close)

    def _channel(self):
        guild = self.origin.guild
        if self.channel_id is None:
            return None
        return (guild.get_channel(self.channel_id)
                or guild.get_thread(self.channel_id))

    def _permissions(self, interaction: discord.Interaction) -> bool:
        guild = interaction.guild
        if guild is None or guild.id != self.guild_id:
            return False
        perms = getattr(interaction.user, "guild_permissions", None)
        return bool(
            interaction.user.id == guild.owner_id
            or (perms is not None and (perms.administrator or perms.manage_messages))
        )

    async def authorize(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id or interaction.guild is None or interaction.guild.id != self.guild_id:
            await interaction.response.send_message(self.t("owner"), ephemeral=True)
            return False
        if not self._permissions(interaction):
            await interaction.response.send_message(self.t("permission"), ephemeral=True)
            return False
        if self.busy or self.closed:
            await interaction.response.send_message(self.t("busy"), ephemeral=True)
            return False
        return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.authorize(interaction)

    async def refresh(self) -> None:
        await self.origin.edit_original_response(
            embed=self.embed(), view=None if self.busy else self
        )

    def embed(self) -> discord.Embed:
        if self.busy and self._progress:
            return self.operation_embed()
        guild = self.origin.guild
        review = self.snapshot is not None
        result = discord.Embed(
            title=self.t("review") if review else self.t("title"),
            color=discord.Color.orange() if review else discord.Color.blurple(),
        )
        user_mentions = ", ".join(f"<@{uid}>" for uid in self.user_ids) or self.t("none")
        where = f"<#{self.channel_id}>" if self.channel_id else self.t("whole")
        scope = self.t("all") if self.everything else (
            f"{self.format_datetime(self.display_from) if self.display_from else '—'}"
            f" → {self.format_datetime(self.display_to) if self.display_to else '—'}"
            if self.display_from or self.display_to else "—"
        )
        result.add_field(name=self.t("users"), value=user_mentions[:1024], inline=False)
        result.add_field(name=self.t("channel"), value=where)
        result.add_field(name=self.t("kind"), value=self.t({"all": "all_kind", "links": "links", "text": "text"}[self.kind]))
        result.add_field(name=self.t("range"), value=scope)
        result.add_field(name=self.t("limit"), value=str(self.limit) if self.limit is not None and not self.everything else "—")
        if review:
            result.add_field(name=self.t("total"), value=str(len(self.snapshot)), inline=False)
            result.add_field(name=self.t("scanned"), value=str(self.scanned))
            result.add_field(name=self.t("skipped"), value=str(self.skipped))
            counts = Counter(uid for _, _, uid in self.snapshot)
            result.add_field(
                name=self.t("per_user"),
                value=("\n".join(f"<@{uid}>: {counts[uid]}" for uid in self.user_ids) or "—")[:1024],
                inline=False,
            )
            result.description = self.t("preview_help") + (
                "\n⚠️ " + self.t("partial") if self.skipped else ""
            )
        else:
            result.description = self.t("mode_note")
        if self._progress:
            result.add_field(
                name=status_text(self.language, "heading"),
                value=self._progress[:1024],
                inline=False,
            )
        footer_text, footer_icon = self.footer(guild)
        result.set_footer(text=footer_text, icon_url=footer_icon or None)
        return result

    def operation_embed(self) -> discord.Embed:
        """Show only the running destructive action, not an editable preview."""
        result = discord.Embed(
            description=self._progress or "",
            color=discord.Color.blurple(),
        )
        footer_text, footer_icon = self.footer(self.origin.guild)
        result.set_footer(text=footer_text, icon_url=footer_icon or None)
        return result

    async def users_changed(self, interaction: discord.Interaction) -> None:
        selected = tuple(dict.fromkeys(u.id for u in self.user_select.values))
        combined = tuple(dict.fromkeys((*selected, *self.manual_user_ids)))
        if len(combined) > 25:
            await interaction.response.send_message(self.t("max_users"), ephemeral=True)
            return
        self.selected_user_ids = selected
        self.user_ids = combined
        self.invalidate()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    async def channel_changed(self, interaction: discord.Interaction) -> None:
        self.channel_id = self.channel_select.values[0].id if self.channel_select.values else None
        self.invalidate()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    async def kind_changed(self, interaction: discord.Interaction) -> None:
        self.kind = self.kind_select.values[0]
        self.invalidate()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    async def open_range(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(PurgeRangeModal(self))

    async def open_ids(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(PurgeUsersModal(self))

    async def toggle_all(self, interaction: discord.Interaction) -> None:
        perms = interaction.user.guild_permissions
        if not self.everything and not (interaction.user.id == interaction.guild.owner_id or perms.administrator or perms.manage_guild):
            await interaction.response.send_message(self.t("wide"), ephemeral=True)
            return
        self.everything = not self.everything
        if self.everything:
            self.from_text = self.to_text = ""
            self.display_from = self.display_to = None
            self.after = self.before = None
            self.limit = None
        self.invalidate()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    async def clear_channel(self, interaction: discord.Interaction) -> None:
        self.channel_id = None
        self.invalidate()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    async def close(self, interaction: discord.Interaction) -> None:
        self.closed = True
        self.snapshot = None
        self._build()
        self.stop()
        await interaction.response.edit_message(
            content=self.t("closed"), embed=None, view=None,
        )

    async def back(self, interaction: discord.Interaction) -> None:
        self.invalidate()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    def _audit_available(self):
        guild = self.origin.guild
        channel = guild.get_channel(self.audit_channel_id)
        me = guild.me
        if channel is None or me is None:
            return False
        perms = channel.permissions_for(me)
        return bool(perms.view_channel and perms.send_messages and perms.embed_links)

    def _channel_available(self, channel, actor):
        guild = self.origin.guild
        if guild.me is None:
            return False
        try:
            member_perm = channel.permissions_for(actor)
            bot_perm = channel.permissions_for(guild.me)
            return all((
                member_perm.view_channel, member_perm.read_message_history,
                member_perm.manage_messages, bot_perm.view_channel,
                bot_perm.read_message_history, bot_perm.manage_messages,
            ))
        except (AttributeError, discord.HTTPException):
            return False

    async def continue_scan(self, interaction: discord.Interaction) -> None:
        if not self.user_ids:
            await interaction.response.send_message(self.t("choose"), ephemeral=True)
            return
        if not self.everything and self.after is None and self.before is None and self.limit is None:
            await interaction.response.send_message(self.t("scope"), ephemeral=True)
            return
        if self.everything:
            perms = interaction.user.guild_permissions
            if not (interaction.user.id == interaction.guild.owner_id or perms.administrator or perms.manage_guild):
                await interaction.response.send_message(self.t("wide"), ephemeral=True)
                return
        if not self._audit_available():
            await interaction.response.send_message(self.t("audit_missing"), ephemeral=True)
            return
        if self.channel_id is not None and self._channel() is None:
            await interaction.response.send_message(self.t("stale"), ephemeral=True)
            return
        self.busy = True
        await interaction.response.defer()
        self.scanned = self.skipped = 0
        self.scanned_channels = {}
        examined = found_count = 0
        total = "?"
        reporter = ProgressReporter(lambda _text: self.refresh())

        async def report(*, force=False):
            self._progress = compact_operation_status(
                self.language, "purge_scan", self.scanned + self.skipped,
                total if isinstance(total, int) else None,
                examined=examined, found=found_count,
            )
            await reporter.publish(self._progress, force=force)

        # Show immediate acknowledgement and prevent a second action until
        # the preview finishes (including selection and confirmation).
        self._build()
        for item in self.children:
            item.disabled = True
        await report(force=True)
        try:
            guild = interaction.guild
            target_channels = list(await self.targets(guild, self._channel(), self.after))
            total = len(target_channels)
            found: dict[int, list[tuple[int, int, int]]] = {uid: [] for uid in self.user_ids}
            await report(force=True)
            for channel in target_channels:
                if not self._channel_available(channel, interaction.user):
                    self.skipped += 1
                    await report()
                    continue
                try:
                    # newest first even when 'after' is set. Per-channel early stop
                    # is safe: global top N must be contained in every channel's top N.
                    counts = Counter()
                    async for msg in channel.history(
                        limit=None, after=self.after, before=self.before, oldest_first=False
                    ):
                        examined += 1
                        if examined % 100 == 0:
                            await report()
                        uid = msg.author.id
                        if uid not in found or not self.matches(msg, self.kind):
                            continue
                        if self.limit is not None and counts[uid] >= self.limit:
                            continue
                        counts[uid] += 1
                        found_count += 1
                        found[uid].append((channel.id, msg.id, uid))
                        if self.limit is not None and all(
                            counts[chosen] >= self.limit for chosen in self.user_ids
                        ):
                            break
                    self.scanned += 1
                    self.scanned_channels[channel.id] = channel
                except (discord.Forbidden, discord.HTTPException):
                    self.skipped += 1
                await report()
            if self.scanned == 0:
                self._progress = None
                self.snapshot = None
                self._build()
                await self.refresh()
                await interaction.followup.send(self.t("no_access"), ephemeral=True)
                return
            self.snapshot = sorted(
                (entry for uid in self.user_ids for entry in (
                    sorted(found[uid], key=lambda row: row[1], reverse=True)[:self.limit]
                    if self.limit is not None else found[uid]
                )),
                key=lambda row: row[1], reverse=True,
            )
            self._progress = None
            self._build()
            await self.refresh()
            if not self.snapshot:
                await interaction.followup.send(self.t("no_messages"), ephemeral=True)
        except Exception as exc:
            print(f"PURGE status=PREVIEW_FAILED guild={self.guild_id} error={type(exc).__name__}", flush=True)
            self.snapshot = None
            self._progress = status_text(self.language, "scan_failed")
            self._build()
            await self.refresh()
        finally:
            self.busy = False
            if not self.closed:
                self._build()
                await self.refresh()

    async def confirm(self, interaction: discord.Interaction) -> None:
        if self.snapshot is None or not self.snapshot:
            await interaction.response.send_message(self.t("stale"), ephemeral=True)
            return
        if not self._audit_available():
            await interaction.response.send_message(self.t("audit_missing"), ephemeral=True)
            return
        if self.everything:
            perms = interaction.user.guild_permissions
            if not (interaction.user.id == interaction.guild.owner_id or perms.administrator or perms.manage_guild):
                await interaction.response.send_message(self.t("wide"), ephemeral=True)
                return
        keys = {(self.guild_id, uid) for uid in self.user_ids}
        if keys & self.running:
            await interaction.response.send_message(self.t("running"), ephemeral=True)
            return
        self.running.update(keys)
        self.busy = True
        frozen = tuple(self.snapshot)
        self.snapshot = None
        self.closed = True
        self._build()
        await interaction.response.defer()
        deleted = failed = processed = 0
        interrupted = False
        per_user = Counter()
        reporter = ProgressReporter(
            lambda _text: self.origin.edit_original_response(
                embed=self.operation_embed(), view=None
            )
        )

        async def report(*, force=False):
            self._progress = compact_operation_status(
                self.language, "purge_delete", processed, len(frozen),
                deleted=deleted, failed=failed,
            )
            await reporter.publish(self._progress, force=force)

        await report(force=True)
        try:
            guild = interaction.guild
            for channel_id, message_id, uid in frozen:
                channel = (self.scanned_channels.get(channel_id)
                           or guild.get_channel(channel_id) or guild.get_thread(channel_id))
                if channel is None or not self._channel_available(channel, interaction.user) or not self._permissions(interaction):
                    failed += 1
                else:
                    try:
                        ok = await self.delete(
                            channel, message_id, expected_author_id=uid,
                            after=self.after, before=self.before, content_type=self.kind,
                        )
                    except Exception:
                        ok = False
                    if ok:
                        deleted += 1
                        per_user[uid] += 1
                    else:
                        failed += 1
                processed += 1
                await report()
        except Exception as exc:
            interrupted = True
            print(f"PURGE status=DELETE_INTERRUPTED guild={self.guild_id} "
                  f"error={type(exc).__name__}", flush=True)
        finally:
            self.running.difference_update(keys)
        summary = (
            f"{self.t('total')}: {len(frozen)}\n"
            f"{self.t('deleted')}: {deleted}\n{self.t('failed')}: {failed}\n"
            f"{self.t('scanned')}: {self.scanned}\n{self.t('skipped')}: {self.skipped}\n"
            + "\n".join(f"<@{uid}>: {per_user[uid]}" for uid in self.user_ids)
        )
        if interrupted:
            summary += ("\n" + status_text(self.language, "delete_failed")
                        + "\n" + status_text(
                            self.language, "remaining", count=len(frozen) - processed
                        ))
        # Exactly one audit entry per confirmed operation (success or partial failure).
        try:
            await self.log(
                interaction.guild, self.t("audit"),
                f"<@{self.owner_id}> · {self.t('channel')}: "
                f"{f'<#{self.channel_id}>' if self.channel_id else self.t('whole')}\n"
                f"{self.t('kind')}: {self.t({'all':'all_kind','links':'links','text':'text'}[self.kind])}\n"
                + summary,
                discord.Color.green() if not failed and not interrupted else discord.Color.orange(),
            )
        except Exception:
            summary += "\n⚠️ " + self.t("audit_missing")
        result = discord.Embed(
            title=(status_text(self.language, "interrupted") if interrupted else self.t("done")),
            description=summary[:4096],
            color=discord.Color.green() if not failed and not interrupted else discord.Color.orange(),
        )
        ft, fi = self.footer(interaction.guild)
        result.set_footer(text=ft, icon_url=fi or None)
        try:
            await self.origin.edit_original_response(embed=result, view=None)
        except discord.HTTPException:
            pass
        self.stop()

    async def on_timeout(self) -> None:
        self.closed = True
        self.snapshot = None
        self._build()
