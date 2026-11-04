"""Navegación global en paneles de configuración de El Heraldo."""
import asyncio
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

import discord
import panel_navigation as navigation
import setup_interactions as runtime


class ParentPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.guild_id = 345
        self.owner_id = 6
        self.interaction_check = AsyncMock(return_value=True)


class NavigationTests(unittest.IsolatedAsyncioTestCase):
    async def test_panel_has_both_controls_without_duplicates(self):
        child = ParentPanel()
        navigation.ensure_navigation_controls(child)
        navigation.ensure_navigation_controls(child)
        self.assertEqual(sum(isinstance(x, navigation.AdministrativeBack)
                             for x in child.children), 1)
        self.assertEqual(sum(isinstance(x, navigation.AdministrativeClose)
                             for x in child.children), 1)

    async def test_back_returns_actual_previous_panel(self):
        parent, child = ParentPanel(), ParentPanel()
        child._heraldo_back_target = parent
        child._heraldo_back_snapshot = {"content": "Anterior", "embed": None}
        navigation.ensure_navigation_controls(child)
        action = next(x for x in child.children
                      if isinstance(x, navigation.AdministrativeBack))
        interaction = NS(response=NS(edit_message=AsyncMock()))
        await action.callback(interaction)
        interaction.response.edit_message.assert_awaited_once_with(
            content="Anterior", embed=None, view=parent)

    async def test_navigation_captures_parent_but_never_reverses_ancestor(self):
        parent, child = ParentPanel(), ParentPanel()
        current = runtime.source_view.set(parent)
        try:
            runtime.prepare_navigation(child, NS(message=NS(content="Inicio", embeds=[])))
        finally:
            runtime.source_view.reset(current)
        self.assertIs(child._heraldo_back_target, parent)
        self.assertEqual(child._heraldo_back_snapshot["content"], "Inicio")
        current = runtime.source_view.set(child)
        try:
            runtime.prepare_navigation(parent, NS(message=NS(content="Subpanel", embeds=[])))
        finally:
            runtime.source_view.reset(current)
        self.assertFalse(hasattr(parent, "_heraldo_back_target"))

    async def test_existing_back_is_not_duplicated(self):
        view = ParentPanel()
        view.add_item(discord.ui.Button(label="Volver", row=4))
        navigation.ensure_navigation_controls(view)
        self.assertFalse(any(isinstance(x, navigation.AdministrativeBack)
                             for x in view.children))


if __name__ == "__main__":
    unittest.main()
