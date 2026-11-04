"""Selector manual por servidor, portado selectivamente de Pruebas a main.

Los textos se obtienen de los catálogos; cambiar la selección no guarda.
La conciliación del historial comienza únicamente después de confirmar.
"""
from __future__ import annotations

import asyncio
import discord
import heraldo_i18n as i18n

LANGUAGE_CHOICES = {
    "es-419": "Español (Latinoamérica)",
    "en-US": "English (US)",
    "pt-BR": "Português (Brasil)",
}


def language_panel_text(guild_id, current_language, selected=None):
    current = current_language(guild_id)
    text = (
        "**" + i18n.translate(current, "language.title") + "**\n\n"
        + i18n.translate(current, "language.description") + "\n\n"
        + "**" + i18n.translate(
            current, "language.current", language=LANGUAGE_CHOICES[current]
        ) + "**"
    )
    if selected and selected != current:
        text += "\n**" + i18n.translate(
            current, "language.pending", language=LANGUAGE_CHOICES[selected]
        ) + "**"
    return text


class LanguageSettingsView(discord.ui.View):
    """Navegación: Volver primero, Cerrar al final, sin autosave."""

    def __init__(self, guild_id, owner_id, host):
        super().__init__(timeout=900)
        self.guild_id, self.owner_id = guild_id, owner_id
        self.host = host
        self.original = host["get_language"](guild_id)
        self.pending = self.original
        language = self.original
        self.selector = discord.ui.Select(
            placeholder=i18n.translate(language, "language.select"),
            options=[
                discord.SelectOption(
                    label=LANGUAGE_CHOICES[key], value=key, default=(key == language),
                    description=(i18n.translate(key, "language.help")
                                 if key in i18n.PARTIAL_LOCALES else None),
                )
                for key in i18n.TARGET_LOCALES
            ],
            row=0,
        )
        self.selector.callback = self.select_language
        self.add_item(self.selector)
        self.back.label = i18n.translate(language, "language.back")
        self.save.label = i18n.translate(language, "language.save")
        self.discard.label = i18n.translate(language, "language.discard")
        self.close.label = i18n.translate(language, "setup.commands.close") if "setup.commands.close" in i18n.CATALOGS[language].messages else {
            "es-419": "Cerrar", "en-US": "Close", "pt-BR": "Fechar"
        }[language]
        self._refresh()

    def _refresh(self):
        for choice in self.selector.options:
            choice.default = choice.value == self.pending
        for button in (self.back, self.save, self.discard, self.close):
            self.remove_item(button)
        controls = ([self.back, self.save, self.discard, self.close]
                    if self.pending != self.original else [self.back, self.close])
        for button in controls:
            self.add_item(button)

    async def interaction_check(self, interaction):
        return await self.host["check_access"](
            interaction, self.guild_id, self.owner_id)

    async def select_language(self, interaction):
        if self.host["get_language"](self.guild_id) != self.original:
            await interaction.response.edit_message(
                content=i18n.translate(
                    self.host["get_language"](self.guild_id), "language.concurrent_change"
                ), view=None,
            )
            return
        values = (interaction.data or {}).get("values") or []
        chosen = str(values[0]) if values else ""
        if chosen not in i18n.SUPPORTED_LOCALES:
            await interaction.response.send_message(
                i18n.translate(self.original, "language.not_available"), ephemeral=True)
            return
        self.pending = chosen
        self._refresh()
        await interaction.response.edit_message(
            content=language_panel_text(self.guild_id, self.host["get_language"], chosen),
            view=self,
        )

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction, button):
        self.stop()
        await self.host["return_home"](interaction, self.guild_id, self.owner_id)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=1)
    async def save(self, interaction, button):
        previous = self.host["get_language"](self.guild_id)
        if previous != self.original:
            await interaction.response.edit_message(
                content=i18n.translate(previous, "language.concurrent_change"), view=None)
            return
        if self.pending == self.original:
            await interaction.response.edit_message(
                content=language_panel_text(self.guild_id, self.host["get_language"]),
                view=self,
            )
            return
        new_language = self.pending
        self.host["set_language"](self.guild_id, "language", new_language)
        self.stop()
        await interaction.response.edit_message(
            content=language_panel_text(self.guild_id, self.host["get_language"])
            + "\n\n**" + i18n.translate(new_language, "language.saved") + "**",
            view=LanguageSettingsView(self.guild_id, self.owner_id, self.host),
        )

        guild = interaction.guild
        if guild is not None:
            async def reconcile():
                try:
                    await self.host["on_changed"](guild, previous, new_language)
                except Exception as exc:
                    print(f"LANGUAGE_HISTORY_SYNC status=FAILED guild={self.guild_id} "
                          f"error={type(exc).__name__}", flush=True)
            asyncio.create_task(reconcile())

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=1)
    async def discard(self, interaction, button):
        self.pending = self.original
        self._refresh()
        await interaction.response.edit_message(
            content=language_panel_text(self.guild_id, self.host["get_language"]),
            view=self,
        )

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger, row=1)
    async def close(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(
            content=i18n.translate(
                self.host["get_language"](self.guild_id), "language.closed"
            ), view=None,
        )
