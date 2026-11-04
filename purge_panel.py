"""Panel independiente y seguro del comando /purge (sin datos persistentes).

La vista previa conserva únicamente IDs; nunca vuelve a buscar al confirmar.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import asyncio

import discord


TEXT = {
    "es-419": {
        "title": "🧹 Limpieza de mensajes", "review": "Confirmar limpieza",
        "done": "Resultado de la limpieza", "users": "Usuarios",
        "channel": "Canal", "kind": "Tipo", "range": "Intervalo",
        "limit": "Límite por usuario", "all": "Todos los mensajes",
        "none": "Sin seleccionar", "whole": "Todos los canales",
        "all_kind": "Cualquier mensaje", "links": "Solo enlaces",
        "text": "Solo texto (sin imágenes ni vídeos)",
        "settings": "Rango y límite", "all_button": "Todos",
        "channel_reset": "Quitar canal", "next": "Continuar",
        "back": "Volver", "close": "Cerrar", "confirm": "Confirmar eliminación",
        "selected": "Usuarios seleccionados", "scanned": "Canales examinados",
        "skipped": "Canales omitidos", "total": "Mensajes encontrados",
        "per_user": "Desglose por usuario", "deleted": "Eliminados",
        "failed": "No eliminados", "audit": "Registro de limpieza",
        "permission": "No tienes permisos para administrar mensajes en esta operación.",
        "owner": "Este panel pertenece a otro moderador.",
        "busy": "Hay una operación en curso. No se puede modificar el panel.",
        "choose": "Selecciona al menos un usuario.",
        "scope": "Indica un intervalo o un límite, o activa «Todos».",
        "wide": "La limpieza completa exige «Gestionar servidor».",
        "range_error": "El intervalo es inválido: «Desde» debe ser más antiguo que «Hasta».",
        "invalid": "Introduce una duración válida y una cantidad entera positiva.",
        "no_access": "No hay canales accesibles con los permisos necesarios.",
        "stale": "La vista previa ya no es válida. Ejecuta «Continuar» otra vez.",
        "preview_help": "Esta es una fotografía de los mensajes encontrados; solo esos ID podrán eliminarse. Los mensajes nuevos quedan fuera.",
        "partial": "Algunos canales no pudieron revisarse; el total corresponde únicamente a los examinados.",
        "no_messages": "No se encontraron mensajes; no hay nada que eliminar.",
        "audit_missing": "No se puede completar la operación: el canal de registros del bot no está disponible.",
        "running": "Otra limpieza ya está procesando uno de los usuarios seleccionados.",
        "unexpected": "No se pudo completar la búsqueda. No se eliminó ningún mensaje.",
        "closed": "Panel cerrado sin eliminar mensajes.",
        "period_from": "Desde (ej. 2d, 12h)", "period_to": "Hasta (ej. 2h)",
        "quantity": "Cantidad máxima por usuario", "mode_note": "«Todos» elimina los límites de cantidad y tiempo.",
        "log_status": "Resultado", "finished": "Operación terminada",
    },
    "en-US": {
        "title": "🧹 Message cleanup", "review": "Confirm cleanup",
        "done": "Cleanup result", "users": "Users",
        "channel": "Channel", "kind": "Type", "range": "Time range",
        "limit": "Limit per user", "all": "All messages",
        "none": "Not selected", "whole": "All channels",
        "all_kind": "Any message", "links": "Links only",
        "text": "Text only (no images/videos)",
        "settings": "Range and limit", "all_button": "All",
        "channel_reset": "Clear channel", "next": "Continue",
        "back": "Back", "close": "Close", "confirm": "Confirm deletion",
        "selected": "Selected users", "scanned": "Channels scanned",
        "skipped": "Channels skipped", "total": "Messages found",
        "per_user": "By user", "deleted": "Deleted",
        "failed": "Not deleted", "audit": "Cleanup audit",
        "permission": "You lack permission to manage messages for this operation.",
        "owner": "This panel belongs to another moderator.",
        "busy": "An operation is in progress. Changes are disabled.",
        "choose": "Select at least one user.",
        "scope": "Set a time range or limit, or enable All.",
        "wide": "Full cleanup requires Manage Server permission.",
        "range_error": "Invalid time range: From must be older than To.",
        "invalid": "Enter valid durations and a positive whole number.",
        "no_access": "No channels are accessible with the required permissions.",
        "stale": "The preview is no longer valid. Continue again.",
        "preview_help": "This is a fixed snapshot of message IDs. New messages cannot be added.",
        "partial": "Some channels could not be inspected; the count covers inspected channels only.",
        "no_messages": "No messages were found.",
        "audit_missing": "Cannot proceed: the bot's audit log channel is unavailable.",
        "running": "Another cleanup is already processing one of the selected users.",
        "unexpected": "The scan failed; no messages were deleted.",
        "closed": "Panel closed without deleting messages.",
        "period_from": "From (e.g. 2d, 12h)", "period_to": "To (e.g. 2h)",
        "quantity": "Maximum messages per user", "mode_note": "All removes time and count limits.",
        "log_status": "Result", "finished": "Operation complete",
    },
    "pt-BR": {
        "title": "🧹 Limpeza de mensagens", "review": "Confirmar limpeza",
        "done": "Resultado da limpeza", "users": "Usuários",
        "channel": "Canal", "kind": "Tipo", "range": "Período",
        "limit": "Limite por usuário", "all": "Todas as mensagens",
        "none": "Não selecionado", "whole": "Todos os canais",
        "all_kind": "Qualquer mensagem", "links": "Apenas links",
        "text": "Apenas texto (sem imagens ou vídeos)",
        "settings": "Período e limite", "all_button": "Todas",
        "channel_reset": "Limpar canal", "next": "Continuar",
        "back": "Voltar", "close": "Fechar", "confirm": "Confirmar exclusão",
        "selected": "Usuários selecionados", "scanned": "Canais analisados",
        "skipped": "Canais ignorados", "total": "Mensagens encontradas",
        "per_user": "Por usuário", "deleted": "Excluídas",
        "failed": "Não excluídas", "audit": "Registro da limpeza",
        "permission": "Você não tem permissão para gerenciar mensagens.",
        "owner": "Este painel pertence a outro moderador.",
        "busy": "Uma operação está em andamento; alterações desativadas.",
        "choose": "Selecione pelo menos um usuário.",
        "scope": "Defina um período/limite ou ative Todas.",
        "wide": "A limpeza completa requer Gerenciar Servidor.",
        "range_error": "Período inválido: De deve ser anterior a Até.",
        "invalid": "Informe durações válidas e um número inteiro positivo.",
        "no_access": "Não há canais acessíveis com as permissões necessárias.",
        "stale": "A prévia expirou. Continue novamente.",
        "preview_help": "Esta é uma lista fixa de IDs; mensagens novas não serão incluídas.",
        "partial": "Alguns canais não puderam ser lidos; a contagem cobre apenas os analisados.",
        "no_messages": "Nenhuma mensagem encontrada.",
        "audit_missing": "Impossível continuar: o canal de registro do bot está indisponível.",
        "running": "Outra limpeza já está processando um usuário selecionado.",
        "unexpected": "A busca falhou; nenhuma mensagem foi excluída.",
        "closed": "Painel fechado sem excluir mensagens.",
        "period_from": "De (ex. 2d, 12h)", "period_to": "Até (ex. 2h)",
        "quantity": "Máximo de mensagens por usuário", "mode_note": "Todas remove os limites.",
        "log_status": "Resultado", "finished": "Operação concluída",
    },
}


class PurgeRangeModal(discord.ui.Modal):
    def __init__(self, panel: "PurgePanel"):
        self.panel = panel
        super().__init__(title=panel.t("settings"))
        self.from_input = discord.ui.TextInput(
            label=panel.t("period_from"), required=False, max_length=40,
            default=panel.from_text or "",
        )
        self.to_input = discord.ui.TextInput(
            label=panel.t("period_to"), required=False, max_length=40,
            default=panel.to_text or "",
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
            now = datetime.now(timezone.utc)
            after = (now - timedelta(minutes=self.panel.parse_duration(raw_from, 1, self.panel.max_minutes))) if raw_from else None
            before = (now - timedelta(minutes=self.panel.parse_duration(raw_to, 1, self.panel.max_minutes))) if raw_to else None
            count = int(raw_count) if raw_count else None
            if count is not None and count <= 0:
                raise ValueError("non-positive")
        except (ValueError, OverflowError):
            await interaction.response.send_message(self.panel.t("invalid"), ephemeral=True)
            return
        if after is not None and before is not None and after >= before:
            await interaction.response.send_message(self.panel.t("range_error"), ephemeral=True)
            return
        self.panel.after, self.panel.before = after, before
        self.panel.from_text, self.panel.to_text, self.panel.limit = raw_from, raw_to, count
        self.panel.everything = False
        self.panel.invalidate()
        await interaction.response.defer(ephemeral=True)
        await self.panel.refresh()


class PurgePanel(discord.ui.View):
    def __init__(
        self, interaction: discord.Interaction, *,
        language: str, footer, targets, matches, delete, log, parse_duration,
        max_minutes: int, running: set, audit_channel_id: int,
    ):
        super().__init__(timeout=900)
        self.origin = interaction
        self.guild_id = interaction.guild.id
        self.owner_id = interaction.user.id
        self.language = language if language in TEXT else "es-419"
        self.footer = footer
        self.targets = targets
        self.matches = matches
        self.delete = delete
        self.log = log
        self.parse_duration = parse_duration
        self.max_minutes = max_minutes
        self.running = running
        self.audit_channel_id = audit_channel_id
        self.user_ids: tuple[int, ...] = ()
        self.channel_id: int | None = None
        self.kind = "all"
        self.everything = False
        self.after = self.before = None
        self.from_text = self.to_text = ""
        self.limit: int | None = None
        self.snapshot: list[tuple[int, int, int]] | None = None
        self.scanned = self.skipped = 0
        self.busy = self.closed = False
        self._build()

    def t(self, key: str) -> str:
        return TEXT[self.language][key]

    def invalidate(self) -> None:
        self.snapshot = None
        self.scanned = self.skipped = 0
        self._build()

    def _button(self, key, style, row, callback):
        button = discord.ui.Button(label=self.t(key), style=style, row=row)
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
        self.user_select = discord.ui.UserSelect(
            placeholder=self.t("selected") + f": {len(self.user_ids)}/25",
            min_values=0, max_values=25, row=0,
        )
        self.user_select.callback = self.users_changed
        self.add_item(self.user_select)
        self.channel_select = discord.ui.ChannelSelect(
            placeholder=self.t("channel") + ": " + (
                str(self.channel_id) if self.channel_id else self.t("whole")
            ),
            min_values=0, max_values=1, row=1,
        )
        self.channel_select.callback = self.channel_changed
        self.add_item(self.channel_select)
        self.kind_select = discord.ui.Select(
            placeholder=self.t("kind"), min_values=1, max_values=1, row=2,
            options=[
                discord.SelectOption(label=self.t(k), value=v, default=self.kind == v)
                for v, k in (("all", "all_kind"), ("links", "links"), ("text", "text"))
            ],
        )
        self.kind_select.callback = self.kind_changed
        self.add_item(self.kind_select)
        self._button("settings", discord.ButtonStyle.primary, 3, self.open_range)
        self._button("all_button", discord.ButtonStyle.secondary, 3, self.toggle_all)
        self._button("channel_reset", discord.ButtonStyle.secondary, 3, self.clear_channel)
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
        await self.origin.edit_original_response(embed=self.embed(), view=self)

    def embed(self) -> discord.Embed:
        guild = self.origin.guild
        review = self.snapshot is not None
        result = discord.Embed(
            title=self.t("review") if review else self.t("title"),
            color=discord.Color.orange() if review else discord.Color.blurple(),
        )
        user_mentions = ", ".join(f"<@{uid}>" for uid in self.user_ids) or self.t("none")
        where = f"<#{self.channel_id}>" if self.channel_id else self.t("whole")
        scope = self.t("all") if self.everything else (
            f"{self.from_text or '—'} → {self.to_text or '0'}"
            if self.from_text or self.to_text else "—"
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
        footer_text, footer_icon = self.footer(guild)
        result.set_footer(text=footer_text, icon_url=footer_icon or None)
        return result

    async def users_changed(self, interaction: discord.Interaction) -> None:
        self.user_ids = tuple(dict.fromkeys(u.id for u in self.user_select.values))
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

    async def toggle_all(self, interaction: discord.Interaction) -> None:
        perms = interaction.user.guild_permissions
        if not self.everything and not (interaction.user.id == interaction.guild.owner_id or perms.administrator or perms.manage_guild):
            await interaction.response.send_message(self.t("wide"), ephemeral=True)
            return
        self.everything = not self.everything
        if self.everything:
            self.from_text = self.to_text = ""
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
        try:
            guild = interaction.guild
            target_channels = await self.targets(guild, self._channel(), self.after)
            found: dict[int, list[tuple[int, int, int]]] = {uid: [] for uid in self.user_ids}
            self.scanned = self.skipped = 0
            for channel in target_channels:
                if not self._channel_available(channel, interaction.user):
                    self.skipped += 1
                    continue
                try:
                    # newest first even when 'after' is set. Per-channel early stop
                    # is safe: global top N must be contained in every channel's top N.
                    counts = Counter()
                    async for msg in channel.history(
                        limit=None, after=self.after, before=self.before, oldest_first=False
                    ):
                        uid = msg.author.id
                        if uid not in found or not self.matches(msg, self.kind):
                            continue
                        if self.limit is not None and counts[uid] >= self.limit:
                            continue
                        counts[uid] += 1
                        found[uid].append((channel.id, msg.id, uid))
                        if self.limit is not None and all(
                            counts[chosen] >= self.limit for chosen in self.user_ids
                        ):
                            break
                    self.scanned += 1
                except (discord.Forbidden, discord.HTTPException):
                    self.skipped += 1
            if self.scanned == 0:
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
            self._build()
            await self.refresh()
            if not self.snapshot:
                await interaction.followup.send(self.t("no_messages"), ephemeral=True)
        except Exception:
            self.snapshot = None
            self._build()
            await self.refresh()
            await interaction.followup.send(self.t("unexpected"), ephemeral=True)
        finally:
            self.busy = False

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
        deleted = failed = 0
        per_user = Counter()
        try:
            guild = interaction.guild
            for channel_id, message_id, uid in frozen:
                channel = guild.get_channel(channel_id) or guild.get_thread(channel_id)
                if channel is None or not self._channel_available(channel, interaction.user) or not self._permissions(interaction):
                    failed += 1
                    continue
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
        finally:
            self.running.difference_update(keys)
        summary = (
            f"{self.t('total')}: {len(frozen)}\n"
            f"{self.t('deleted')}: {deleted}\n{self.t('failed')}: {failed}\n"
            f"{self.t('scanned')}: {self.scanned}\n{self.t('skipped')}: {self.skipped}\n"
            + "\n".join(f"<@{uid}>: {per_user[uid]}" for uid in self.user_ids)
        )
        # Exactly one audit entry per confirmed operation (success or partial failure).
        try:
            await self.log(
                interaction.guild, self.t("audit"),
                f"<@{self.owner_id}> · {self.t('channel')}: "
                f"{f'<#{self.channel_id}>' if self.channel_id else self.t('whole')}\n"
                f"{self.t('kind')}: {self.t({'all':'all_kind','links':'links','text':'text'}[self.kind])}\n"
                + summary,
                discord.Color.green() if not failed else discord.Color.orange(),
            )
        except Exception:
            summary += "\n⚠️ " + self.t("audit_missing")
        result = discord.Embed(title=self.t("done"), description=summary[:4096], color=discord.Color.green() if not failed else discord.Color.orange())
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
