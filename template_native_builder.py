"""Panel nativo de Plantillas: un borrador, controles Discord y confirmación explícita.

Se reutilizan los editores de AutoFeed sin crear una interfaz web. Guardar una
plantilla NO publica ni programa mensajes. El canal y la fecha son opciones
del envío, no datos que alteren la plantilla reutilizable.
"""
from __future__ import annotations

import copy
import re
from datetime import datetime, timezone

import discord
import message_payload
import message_autofeeds as feeds
from heraldo_i18n import current_locale, guild_context
from autofeed_setup import AutofeedEditorView, SetupConfirmView
from autofeed_embed_builder import has_content, validate_data

STRINGS = {
    "es-419": dict(new="Crear plantilla", edit="Editar plantilla", name="Nombre de la plantilla",
        name_button="Nombre", save="Guardar cambios", confirm="Confirmar cambios",
        publish="Publicar / Programar", back="Volver", discard="Descartar cambios",
        intro="Edita cada apartado mediante botones y selectores. Ningún cambio se guarda al seleccionar.",
        missing="Escribe un nombre y configura un mensaje o embed válido.",
        duplicate="Ya existe una plantilla con ese nombre o se alcanzó el límite de 25.",
        changed="Las plantillas cambiaron en otra sesión. Vuelve a abrir el editor.",
        saved="Plantilla guardada.", unsaved="Guarda y confirma la plantilla antes de publicarla.",
        prompt="¿Guardar esta plantilla? Guardar no la publica ni programa.",
        notice="Canal, rol, fecha y repetición son opciones de publicación; no se guardan como parte de la plantilla.",
        no_permission="No tienes permiso para editar plantillas."),
    "en-US": dict(new="Create template", edit="Edit template", name="Template name",
        name_button="Name", save="Save changes", confirm="Confirm changes",
        publish="Publish / Schedule", back="Back", discard="Discard changes",
        intro="Use buttons and menus to edit each section. Selecting an option does not save.",
        missing="Enter a name and a valid message or embed.",
        duplicate="A template with this name already exists or the limit of 25 was reached.",
        changed="Templates changed in another session. Reopen the editor.",
        saved="Template saved.", unsaved="Save and confirm this template before publishing it.",
        prompt="Save this template? Saving does not publish or schedule it.",
        notice="Channel, role, date, and repeat settings belong to the publication, not the saved template.",
        no_permission="You cannot edit templates."),
    "pt-BR": dict(new="Criar modelo", edit="Editar modelo", name="Nome do modelo",
        name_button="Nome", save="Salvar alterações", confirm="Confirmar alterações",
        publish="Publicar / Programar", back="Voltar", discard="Descartar alterações",
        intro="Use botões e menus para editar cada seção. Selecionar não salva automaticamente.",
        missing="Digite um nome e configure uma mensagem ou embed válido.",
        duplicate="Já existe um modelo com esse nome ou o limite de 25 foi atingido.",
        changed="Os modelos mudaram em outra sessão. Abra o editor novamente.",
        saved="Modelo salvo.", unsaved="Salve e confirme este modelo antes de publicar.",
        prompt="Salvar este modelo? Salvar não publica nem agenda.",
        notice="Canal, cargo, data e repetição são opções de publicação, não do modelo salvo.",
        no_permission="Você não tem permissão para editar modelos."),
}

def tr(key):
    return STRINGS.get(current_locale(), STRINGS["es-419"])[key]


def to_builder(raw):
    """Leer el primer embed heredado sin alterar los demás."""
    if not raw:
        return None
    author = raw.get("author") or {}
    data = {
        "title": raw.get("title", ""), "description": raw.get("description", ""),
        "url": raw.get("url", ""),
        "color_hex": f'{raw.get("color", 0x5865F2):06X}',
        "author": copy.deepcopy(author),
        "image_url": (raw.get("image") or {}).get("url", ""),
        "thumbnail_url": (raw.get("thumbnail") or {}).get("url", ""),
        "fields": copy.deepcopy(raw.get("fields") or []),
        "timestamp": bool(raw.get("timestamp")),
        "timestamp_value": str(raw.get("timestamp") or ""),
    }
    return validate_data(data)


def to_raw(data):
    if not has_content(data):
        return None
    data = validate_data(data)
    raw = {key: data[key] for key in ("title", "description", "url") if data.get(key)}
    raw["color"] = int(data["color_hex"], 16)
    author = {key: value for key, value in (data.get("author") or {}).items() if value}
    if author.get("name"):
        raw["author"] = author
    for key, target in (("image_url", "image"), ("thumbnail_url", "thumbnail")):
        if data.get(key):
            raw[target] = {"url": data[key]}
    if data.get("fields"):
        raw["fields"] = copy.deepcopy(data["fields"])
    if data.get("timestamp"):
        raw["timestamp"] = data.get("timestamp_value") or datetime.now(timezone.utc).isoformat()
    return raw


class NameModal(discord.ui.Modal):
    def __init__(self, editor):
        super().__init__(title=tr("name"))
        self.editor = editor
        self.field = discord.ui.TextInput(label=tr("name"), max_length=70,
                                         default=editor.name, required=True)
        self.add_item(self.field)

    @guild_context
    async def on_submit(self, interaction):
        if not await self.editor.interaction_check(interaction):
            return
        self.editor.name = str(self.field).strip()
        self.editor.dirty = True
        await interaction.response.edit_message(content=self.editor.summary(),
                                                embeds=[], view=self.editor)


class TemplateEditorView(AutofeedEditorView):
    def __init__(self, host, guild_id, owner_id, template=None):
        super().__init__(host, guild_id, owner_id)
        self.original_template = copy.deepcopy(template)
        self.original_name = template.get("name") if template else None
        self.template_snapshot = copy.deepcopy(host["heraldo_template_list"](guild_id))
        self.schedule_snapshot = self.snapshot
        self.name = self.original_name or ""
        self.extra_embeds = []
        if template:
            text, embeds = message_payload.render(template)
            self.text = text or ""
            if embeds:
                self.embed = to_builder(embeds[0])
                self.extra_embeds = copy.deepcopy(embeds[1:])
        self.save.label = tr("save")
        self.save.callback = self._save_template
        self.back.label = tr("back")
        self.back.callback = self._back_to_templates
        self.preview.callback = self._preview_template
        self.discard.label = tr("discard")
        self.discard.callback = self._discard_template
        self.name_button = discord.ui.Button(label=tr("name_button"),
                                              style=discord.ButtonStyle.primary, row=3)
        self.name_button.callback = self._open_name
        self.add_item(self.name_button)
        self.publish_button = discord.ui.Button(label=tr("publish"),
                                                  style=discord.ButtonStyle.success, row=4)
        self.publish_button.callback = self._publish_template
        self.add_item(self.publish_button)
        self.dirty = False

    @guild_context
    async def interaction_check(self, interaction):
        if not await self.host["configuration_access"](interaction, self.guild_id, self.owner_id):
            return False
        return await super().interaction_check(interaction)

    def summary(self):
        name = discord.utils.escape_markdown(self.name or "—")
        heading = tr("edit") if self.original_template else tr("new")
        return (f"**{heading} — {name}**\n{tr('intro')}\n\n"
                + super().summary().split("\n\n", 1)[-1]
                + "\n\n" + tr("notice"))

    def template(self):
        name = (self.name or "").strip()
        if not name or len(name) > 70:
            raise ValueError(tr("missing"))
        result = copy.deepcopy(self.original_template or {})
        for key in ("title", "description", "image", "content", "embeds"):
            result.pop(key, None)
        result["name"] = name
        result["content"] = self.text
        raw = to_raw(self.embed)
        embeds = ([raw] if raw else []) + copy.deepcopy(self.extra_embeds)
        if embeds:
            result["embeds"] = embeds
        clean = {key: value for key, value in result.items()
                 if key in message_payload.VISUAL_KEYS}
        try:
            message_payload.validate(clean)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return result

    def _is_saved(self):
        if not self.original_name:
            return False
        current = next((item for item in self.host["heraldo_template_list"](self.guild_id)
                        if item.get("name") == self.original_name), None)
        if current is None:
            return False
        try:
            new = self.template()
        except ValueError:
            return False
        return current == new

    @guild_context
    async def _open_name(self, interaction):
        await interaction.response.send_modal(NameModal(self))

    @guild_context
    async def _save_template(self, interaction):
        try:
            proposed = self.template()
        except ValueError as exc:
            await interaction.response.edit_message(content=self.summary() + "\n\n" + str(exc),
                                                    embeds=[], view=self)
            return
        existing = self.host["heraldo_template_list"](self.guild_id)
        if (len(existing) >= 25 and self.original_name is None) or any(
                x["name"].casefold() == proposed["name"].casefold()
                and x["name"] != self.original_name for x in existing):
            await interaction.response.edit_message(content=self.summary() + "\n\n" + tr("duplicate"),
                                                    embeds=[], view=self)
            return
        confirm = TemplateConfirmView(self, proposed)
        await interaction.response.edit_message(
            content=tr("prompt") + "\n\n" + self.summary(),
            embeds=[], view=confirm)

    @guild_context
    async def _publish_template(self, interaction):
        if not self._is_saved():
            await interaction.response.edit_message(
                content=self.summary() + "\n\n" + tr("unsaved"), embeds=[], view=self)
            return
        try:
            job = self.prepared(interaction)
        except ValueError as exc:
            from autofeed_setup import t
            key = str(exc)
            await interaction.response.edit_message(
                content=self.summary() + "\n\n" + (t(key) if key in ("warning", "unavailable") else feeds.tr("invalid")),
                embeds=[], view=self)
            return
        # Envío/agenda separado de guardar plantilla; confirmación obligatoria.
        confirm = SetupConfirmView(
            self.host, job, self.schedule_snapshot, result_panel=_template_panel)
        await interaction.response.edit_message(
            content=self.summary() + "\n\n" + tr("confirm"),
            embeds=[], view=confirm, allowed_mentions=discord.AllowedMentions.none())

    @guild_context
    async def _preview_template(self, interaction):
        try:
            proposed = self.template()
            payload = self.host["heraldo_template_payload"](
                proposed, interaction.guild, interaction.user, interaction.channel)
            embeds = list(payload["embeds"])
        except ValueError as exc:
            await interaction.response.edit_message(content=self.summary() + "\n\n" + str(exc),
                                                    embeds=[], view=self)
            return
        await interaction.response.edit_message(
            content=self.summary(), embeds=embeds, view=self,
            allowed_mentions=discord.AllowedMentions.none())

    @guild_context
    async def _back_to_templates(self, interaction):
        content, view = _template_panel(self.host, self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=content, embeds=[], view=view)

    @guild_context
    async def _discard_template(self, interaction):
        await self._back_to_templates(interaction)


def _template_panel(host, guild_id, owner_id, selected=None):
    # El menú nativo original mantiene las herramientas de gestión y selección.
    from heraldo_i18n import text as _t
    label = _t("text.038abcdd85c82f")
    return label, host["HeraldoTemplateSetupView"](guild_id, owner_id, selected)


class TemplateConfirmView(discord.ui.View):
    def __init__(self, editor, proposed):
        super().__init__(timeout=300)
        self.editor, self.proposed = editor, copy.deepcopy(proposed)
        self.guild_id, self.owner_id = editor.guild_id, editor.owner_id
        self.finished = False
        self.confirm.label, self.discard.label = tr("confirm"), tr("discard")

    @guild_context
    async def interaction_check(self, interaction):
        if self.finished:
            return False
        return await self.editor.interaction_check(interaction)

    @discord.ui.button(label="Confirmar cambios", style=discord.ButtonStyle.success)
    @guild_context
    async def confirm(self, interaction, button):
        editor = self.editor
        current = editor.host["heraldo_template_list"](self.guild_id)
        if current != editor.template_snapshot:
            await interaction.response.edit_message(content=tr("changed"),
                                                    view=editor, embeds=[])
            return
        if any(x["name"].casefold() == self.proposed["name"].casefold()
               and x["name"] != editor.original_name for x in current):
            await interaction.response.edit_message(content=tr("duplicate"),
                                                    view=editor, embeds=[])
            return
        items = [x for x in current if x["name"] != editor.original_name]
        if len(items) >= 25:
            await interaction.response.edit_message(content=tr("duplicate"),
                                                    view=editor, embeds=[])
            return
        items.append(copy.deepcopy(self.proposed))
        editor.host["heraldo_template_save"](self.guild_id, items)
        self.finished = True
        self.stop()
        # Mantener canal, rol, fecha y recurrencia del borrador para el paso
        # opcional Publicar / Programar. Guardar nunca ejecuta el envío.
        editor.original_template = copy.deepcopy(self.proposed)
        editor.original_name = self.proposed["name"]
        editor.template_snapshot = copy.deepcopy(items)
        editor.dirty = False
        await interaction.response.edit_message(
            content=tr("saved") + "\n\n" + editor.summary(),
            embeds=[], view=editor)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger)
    @guild_context
    async def discard(self, interaction, button):
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content=self.editor.summary(),
                                                embeds=[], view=self.editor)
