"""Administración de expedientes de moderación para main.

Separada de las sanciones: omitir o limpiar expedientes no deshace castigos.
La limpieza total exige permiso administrador, confirmación visual y código textual.
"""
from __future__ import annotations

import sqlite3
import discord


LANG = {
    "es-419": {
        "title": "Gestión de expedientes", "open": "Abiertos", "closed": "Cerrados",
        "all": "Todos", "page": "Página {page}/{pages} · {total} casos",
        "none": "Sin expediente seleccionado.",
        "help": "Cerrar resuelve el caso. Omitir cierra sin levantar sanciones. Limpiar cerrados elimina solo los casos cerrados. Limpiar todo borra los expedientes de este servidor, pero no revierte las sanciones de Discord.",
        "case": "Abrir caso", "finish": "Cerrar caso", "omit": "Omitir caso",
        "delete": "Eliminar cerrado", "previous": "Anterior", "next": "Siguiente",
        "cleanup": "Limpiar cerrados", "cleanup_all": "Limpiar todo",
        "back": "Volver", "close": "Cerrar",
        "denied": "No tienes permisos para esta operación.",
        "stale": "El expediente cambió o ya no existe; actualiza el panel.",
        "finish_result": "Expediente cerrado. {effect}",
        "omit_result": "Expediente omitido; las sanciones no se modificaron.",
        "confirm": "Escribe {phrase} para confirmar esta eliminación irreversible.",
        "wrong": "La frase de confirmación no coincide.",
        "deleted": "Se eliminaron {count} expedientes. Las sanciones de Discord permanecen intactas.",
        "cancelled": "Operación cancelada.",
    },
    "en-US": {
        "title": "Case management", "open": "Open", "closed": "Closed",
        "all": "All", "page": "Page {page}/{pages} · {total} cases",
        "none": "No case selected.",
        "help": "Close resolves a case. Omit closes it without lifting sanctions. Clear closed deletes closed records only. Clear all deletes this server's records without reversing Discord sanctions.",
        "case": "View case", "finish": "Close case", "omit": "Omit case",
        "delete": "Delete closed", "previous": "Previous", "next": "Next",
        "cleanup": "Clear closed", "cleanup_all": "Clear all",
        "back": "Back", "close": "Close",
        "denied": "You are not authorized to perform this action.",
        "stale": "This case has changed or no longer exists. Refresh the panel.",
        "finish_result": "Case closed. {effect}",
        "omit_result": "Case omitted without changing any sanctions.",
        "confirm": "Type {phrase} to confirm this irreversible deletion.",
        "wrong": "Confirmation phrase does not match.",
        "deleted": "{count} case records deleted. Discord sanctions remain unchanged.",
        "cancelled": "Action cancelled.",
    },
    "pt-BR": {
        "title": "Gestão de casos", "open": "Abertos", "closed": "Fechados",
        "all": "Todos", "page": "Página {page}/{pages} · {total} casos",
        "none": "Nenhum caso selecionado.",
        "help": "Fechar resolve o caso. Ignorar fecha sem reverter sanções. Limpar fechados remove só registros fechados. Limpar tudo remove os registros deste servidor sem reverter sanções do Discord.",
        "case": "Ver caso", "finish": "Fechar caso", "omit": "Ignorar caso",
        "delete": "Excluir fechado", "previous": "Anterior", "next": "Próximo",
        "cleanup": "Limpar fechados", "cleanup_all": "Limpar tudo",
        "back": "Voltar", "close": "Fechar",
        "denied": "Você não tem permissão para esta ação.",
        "stale": "O caso mudou ou não existe mais. Atualize o painel.",
        "finish_result": "Caso fechado. {effect}",
        "omit_result": "Caso ignorado sem modificar as sanções.",
        "confirm": "Digite {phrase} para confirmar a exclusão irreversível.",
        "wrong": "A frase de confirmação não corresponde.",
        "deleted": "{count} registros excluídos. As sanções do Discord permanecem.",
        "cancelled": "Operação cancelada.",
    },
}


def _locale(host, guild_id):
    return host.get("guild_language", lambda _: "es-419")(guild_id)


def tr(host, guild_id, key, **fmt):
    return LANG.get(_locale(host, guild_id), LANG["es-419"])[key].format(**fmt)


def _conn(host):
    return host["db_connect"]()


class CaseDeleteModal(discord.ui.Modal):
    def __init__(self, panel, kind: str, number: int | None = None):
        super().__init__(title=panel.t("cleanup_all" if kind == "all" else "delete"))
        self.panel, self.kind, self.number = panel, kind, number
        self.required_text = (
            "LIMPIAR TODO" if kind == "all" else
            "LIMPIAR" if kind == "closed" else
            panel.host["moderation_case_code"](number, panel.guild_id)
        )
        self.acknowledgement = discord.ui.TextInput(
            label="Confirmación" if panel.locale == "es-419" else "Confirmation",
            placeholder=self.required_text, required=True, max_length=90)
        self.add_item(self.acknowledgement)

    async def on_submit(self, interaction: discord.Interaction):
        panel = self.panel
        if (not await panel.authorize(interaction, administrator=True)
                or panel.is_finished()):
            return
        if str(self.acknowledgement).strip() != self.required_text:
            await interaction.response.send_message(panel.t("wrong"), ephemeral=True)
            return
        try:
            db = _conn(panel.host)
            try:
                db.execute("BEGIN IMMEDIATE")
                if self.kind == "all":
                    cursor = db.execute(
                        "DELETE FROM moderation_cases WHERE guild_id=?", (panel.guild_id,))
                elif self.kind == "closed":
                    cursor = db.execute(
                        "DELETE FROM moderation_cases WHERE guild_id=? AND open=0",
                        (panel.guild_id,))
                elif self.kind == "one":
                    cursor = db.execute(
                        "DELETE FROM moderation_cases WHERE guild_id=? AND case_number=? AND open=0",
                        (panel.guild_id, self.number))
                else:
                    raise ValueError("invalid_case_cleanup")
                count = cursor.rowcount
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        except sqlite3.Error:
            await interaction.response.send_message(panel.t("stale"), ephemeral=True)
            return
        panel.selected = None
        panel.page = 0
        message = panel.t("deleted", count=count)
        print(f"CASE_CLEANUP guild={panel.guild_id} moderator={interaction.user.id} "
              f"scope={self.kind} count={count}", flush=True)
        # Preserve a single panel; no automated sanction changes or message deletion.
        await interaction.response.send_message(message, ephemeral=True)


class CaseDeleteConfirm(discord.ui.View):
    def __init__(self, panel, kind: str, number=None):
        super().__init__(timeout=180)
        self.panel, self.kind, self.number = panel, kind, number

    async def interaction_check(self, interaction):
        return await self.panel.authorize(interaction, administrator=True)

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.danger, row=0)
    async def confirm(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        await interaction.response.send_modal(CaseDeleteModal(self.panel, self.kind, self.number))

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, row=0)
    async def cancel(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(
            content=self.panel.t("cancelled"), view=None)


class CaseManagerView(discord.ui.View):
    """Private paginated case list with explicit review and safe cleanup."""

    def __init__(self, host, guild_id, owner_id, *, filter_key="open", page=0):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.locale = _locale(host, guild_id)
        self.filter_key, self.page, self.selected = filter_key, page, None
        self.filter_select = discord.ui.Select(
            placeholder=self.t("title"), row=0,
            options=[
                discord.SelectOption(label=self.t(k), value=k, default=k == filter_key)
                for k in ("open", "closed", "all")
            ])
        self.filter_select.callback = self.change_filter
        self.add_item(self.filter_select)
        self.case_select = discord.ui.Select(
            placeholder=self.t("case"), row=1, disabled=True,
            options=[discord.SelectOption(label=self.t("none")[:100], value="none")])
        self.case_select.callback = self.choose_case
        self.add_item(self.case_select)
        for component, key in (
            (self.inspect, "case"), (self.finish, "finish"), (self.omit, "omit"),
            (self.delete_one, "delete"), (self.previous, "previous"),
            (self.next_page, "next"), (self.cleanup, "cleanup"),
            (self.cleanup_all, "cleanup_all"), (self.back, "back"),
            (self.close, "close"),
        ):
            component.label = self.t(key)
        self.refresh_state()

    def t(self, key, **fmt):
        return tr(self.host, self.guild_id, key, **fmt)

    async def authorize(self, interaction, *, administrator=False):
        perms = getattr(interaction.user, "guild_permissions", None)
        valid = (
            interaction.guild is not None and interaction.guild.id == self.guild_id
            and interaction.user.id == self.owner_id
            and perms is not None and perms.manage_guild
            and (not administrator or perms.administrator)
        )
        if not valid:
            sender = (interaction.followup.send if interaction.response.is_done()
                      else interaction.response.send_message)
            await sender(self.t("denied"), ephemeral=True)
        return valid

    async def interaction_check(self, interaction):
        return await self.authorize(interaction)

    def _rows(self):
        db = _conn(self.host)
        try:
            db.row_factory = sqlite3.Row
            query = "guild_id=?"
            params = [self.guild_id]
            if self.filter_key != "all":
                query += " AND open=?"
                params.append(1 if self.filter_key == "open" else 0)
            count = db.execute(
                f"SELECT COUNT(*) FROM moderation_cases WHERE {query}", params).fetchone()[0]
            self.page = min(self.page, max(0, (count - 1) // 25))
            rows = db.execute(
                f"SELECT * FROM moderation_cases WHERE {query} "
                "ORDER BY case_number DESC LIMIT 25 OFFSET ?",
                [*params, self.page * 25]).fetchall()
            return rows, count
        finally:
            db.close()

    def refresh_state(self):
        rows, count = self._rows()
        self.case_select.options = [
            discord.SelectOption(
                label=f"{self.host['moderation_case_code'](int(r['case_number']), self.guild_id)} · {r['type']}"[:100],
                value=str(r["case_number"]),
                description=(("Abierto" if r["open"] else "Cerrado") +
                             " · " + str(r["reason"] or ""))[:100],
                default=int(r["case_number"]) == self.selected)
            for r in rows
        ] or [discord.SelectOption(label=self.t("none")[:100], value="none")]
        self.case_select.disabled = not bool(rows)
        if self.selected not in {int(r["case_number"]) for r in rows}:
            self.selected = None
        current = self.host["moderation_case_get"](self.guild_id, self.selected) if self.selected else None
        self.inspect.disabled = current is None
        self.finish.disabled = current is None or not current["open"]
        self.omit.disabled = current is None or not current["open"]
        self.delete_one.disabled = current is None or bool(current["open"])
        self.previous.disabled = self.page == 0
        self.next_page.disabled = (self.page + 1) * 25 >= count
        self.cleanup.disabled = count == 0 and self.filter_key == "closed"
        return rows, count, current

    def summary(self):
        rows, total, current = self.refresh_state()
        pages = max(1, (total + 24) // 25)
        lines = [
            f"**{self.t('title')} · {self.t(self.filter_key)}**",
            self.t("page", page=self.page + 1, pages=pages, total=total)
        ]
        if current is not None:
            code = self.host["moderation_case_code"](int(current["case_number"]), self.guild_id)
            lines.append(
                f"**{code}** · {current['type']} · <@{current['user_id']}> · "
                f"{self.t('open' if current['open'] else 'closed')}\n"
                f"{discord.utils.escape_mentions(str(current['reason'] or '—'))[:300]}"
            )
        else:
            lines.append(self.t("none"))
        lines.append(self.t("help"))
        return "\n\n".join(lines)[:1900]

    async def change_filter(self, interaction):
        selected = (interaction.data or {}).get("values", ["open"])[0]
        if selected in {"open", "closed", "all"}:
            self.filter_key, self.page, self.selected = selected, 0, None
        await interaction.response.edit_message(content=self.summary(), view=self)

    async def choose_case(self, interaction):
        raw = (interaction.data or {}).get("values", ["none"])[0]
        try:
            value = int(raw)
        except ValueError:
            return await interaction.response.send_message(self.t("stale"), ephemeral=True)
        if value not in {int(r["case_number"]) for r in self._rows()[0]}:
            return await interaction.response.send_message(self.t("stale"), ephemeral=True)
        self.selected = value
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Abrir caso", style=discord.ButtonStyle.primary, row=2)
    async def inspect(self, interaction, button):
        row = self.host["moderation_case_get"](self.guild_id, self.selected) if self.selected else None
        if row is None:
            return await interaction.response.send_message(self.t("stale"), ephemeral=True)
        await interaction.response.send_message(
            embed=self.host["moderation_case_embed"](interaction.guild, row),
            ephemeral=True)

    @discord.ui.button(label="Cerrar caso", style=discord.ButtonStyle.success, row=2)
    async def finish(self, interaction, button):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message(self.t("denied"), ephemeral=True)
        row = self.host["moderation_case_get"](self.guild_id, self.selected) if self.selected else None
        if row is None or not row["open"]:
            return await interaction.response.send_message(self.t("stale"), ephemeral=True)
        await interaction.response.defer()
        effect = await self.host["moderation_close_case_effect"](interaction.guild, row, interaction.user)
        self.host["moderation_case_close"](
            self.guild_id, self.selected, closed_by=interaction.user.id,
            resolution="Cerrado desde el administrador")
        self.selected = None
        await interaction.edit_original_response(
            content=self.t("finish_result", effect=effect) + "\n\n" + self.summary(),
            view=self)

    @discord.ui.button(label="Omitir caso", style=discord.ButtonStyle.secondary, row=2)
    async def omit(self, interaction, button):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message(self.t("denied"), ephemeral=True)
        row = self.host["moderation_case_get"](self.guild_id, self.selected) if self.selected else None
        if row is None or not row["open"]:
            return await interaction.response.send_message(self.t("stale"), ephemeral=True)
        self.host["moderation_case_close"](
            self.guild_id, self.selected, closed_by=interaction.user.id,
            resolution="Omitido sin modificar sanciones")
        self.selected = None
        await interaction.response.edit_message(
            content=self.t("omit_result") + "\n\n" + self.summary(), view=self)

    @discord.ui.button(label="Eliminar cerrado", style=discord.ButtonStyle.danger, row=2)
    async def delete_one(self, interaction, button):
        if not await self.authorize(interaction, administrator=True):
            return
        row = self.host["moderation_case_get"](self.guild_id, self.selected) if self.selected else None
        if row is None or row["open"]:
            return await interaction.response.send_message(self.t("stale"), ephemeral=True)
        prompt = self.t("confirm", phrase=self.host["moderation_case_code"](self.selected, self.guild_id))
        await interaction.response.send_message(
            prompt, view=CaseDeleteConfirm(self, "one", self.selected), ephemeral=True)

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.secondary, row=3)
    async def previous(self, interaction, button):
        self.page = max(0, self.page - 1)
        self.selected = None
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Siguiente", style=discord.ButtonStyle.secondary, row=3)
    async def next_page(self, interaction, button):
        self.page += 1
        self.selected = None
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Limpiar cerrados", style=discord.ButtonStyle.danger, row=3)
    async def cleanup(self, interaction, button):
        if not await self.authorize(interaction, administrator=True):
            return
        await interaction.response.send_message(
            self.t("confirm", phrase="LIMPIAR"),
            view=CaseDeleteConfirm(self, "closed"), ephemeral=True)

    @discord.ui.button(label="Limpiar todo", style=discord.ButtonStyle.danger, row=4)
    async def cleanup_all(self, interaction, button):
        if not await self.authorize(interaction, administrator=True):
            return
        await interaction.response.send_message(
            self.t("confirm", phrase="LIMPIAR TODO"),
            view=CaseDeleteConfirm(self, "all"), ephemeral=True)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=4)
    async def back(self, interaction, button):
        if self.host.get("HeraldoCasesSetupView"):
            view = self.host["HeraldoCasesSetupView"](self.guild_id, self.owner_id)
            await interaction.response.edit_message(
                content=view._content(interaction.guild), view=view)
        else:
            view = self.host["HeraldoModerationSetupView"](self.guild_id, self.owner_id)
            await interaction.response.edit_message(
                content="**El Heraldo · Moderación**", view=view)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger, row=4)
    async def close(self, interaction, button):
        self.stop()
        from panel_navigation import dismiss_panel
        await dismiss_panel(interaction)


def open_panel(host, guild_id, owner_id):
    view = CaseManagerView(host, guild_id, owner_id)
    return view.summary(), view
