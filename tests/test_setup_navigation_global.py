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

    async def test_close_deletes_transient_panel_without_receipt(self):
        view = ParentPanel()
        navigation.ensure_navigation_controls(view)
        close = next(x for x in view.children
                     if isinstance(x, navigation.AdministrativeClose))
        response = NS(is_done=lambda: False, defer=AsyncMock(),
                      edit_message=AsyncMock(), send_message=AsyncMock())
        i = NS(guild=NS(id=345),
               user=NS(id=6, guild_permissions=discord.Permissions(manage_guild=True)),
               response=response, delete_original_response=AsyncMock(),
               edit_original_response=AsyncMock())
        await close.callback(i)
        response.defer.assert_awaited_once()
        i.delete_original_response.assert_awaited_once()
        response.edit_message.assert_not_awaited()
        response.send_message.assert_not_awaited()

    async def test_fallback_close_clears_panel_without_status_card(self):
        response = NS(is_done=lambda: True, defer=AsyncMock())
        i = NS(response=response,
               delete_original_response=AsyncMock(
                   side_effect=discord.Forbidden(NS(status=403, reason="Forbidden"), "No access")),
               edit_original_response=AsyncMock())
        await navigation.dismiss_panel(i)
        response.defer.assert_not_awaited()
        i.edit_original_response.assert_awaited_once_with(
            content="\u200b", embed=None, view=None)

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


    async def test_two_navigation_buttons_share_a_row_in_left_to_right_order(self):
        view = ParentPanel()
        navigation.ensure_navigation_controls(view)
        rendered = sorted(view.children, key=lambda x: x._rendered_row)
        self.assertEqual(len(rendered), 2)
        self.assertIsInstance(rendered[0], navigation.AdministrativeBack)
        self.assertIsInstance(rendered[1], navigation.AdministrativeClose)
        self.assertEqual(rendered[0]._rendered_row, rendered[1]._rendered_row)

    async def test_setup_select_keeps_back_and_close_together_beneath_it(self):
        view = ParentPanel()
        view.add_item(discord.ui.Select(
            placeholder="Abrir módulo",
            options=[discord.SelectOption(label="Moderación", value="moderation")],
            row=0))
        original_close = discord.ui.Button(label="Cerrar", row=1)
        view.add_item(original_close)
        navigation.ensure_navigation_controls(view)
        navigation.ensure_navigation_controls(view)
        rendered = sorted(view.children, key=lambda x: x._rendered_row)
        self.assertIsInstance(rendered[0], discord.ui.Select)
        self.assertIsInstance(rendered[1], navigation.AdministrativeBack)
        self.assertIs(rendered[2], original_close)
        self.assertEqual([x._rendered_row for x in rendered], [0, 1, 1])
        self.assertEqual(original_close.style, discord.ButtonStyle.danger)

    async def test_duplicate_existing_controls_are_removed_without_replacing_callbacks(self):
        view = ParentPanel()
        own_back = discord.ui.Button(label="Volver", row=2)
        own_close = discord.ui.Button(label="Cerrar", row=3)
        for button in (own_close, discord.ui.Button(label="Cerrar", row=3),
                       own_back, discord.ui.Button(label="Volver", row=4)):
            view.add_item(button)
        navigation.ensure_navigation_controls(view)
        self.assertEqual(len(view.children), 2)
        self.assertIs(view.children[0], own_back)
        self.assertIs(view.children[1], own_close)
        self.assertEqual(view.children[0]._rendered_row, view.children[1]._rendered_row)

    async def test_navigation_stays_at_end_of_busy_fifth_row(self):
        view = ParentPanel()
        for row in range(4):
            view.add_item(discord.ui.Select(
                placeholder="Elegir",
                options=[discord.SelectOption(label="Opción", value=str(row))],
                row=row))
        for index in range(3):
            view.add_item(discord.ui.Button(label=f"Acción {index}", row=4))
        navigation.ensure_navigation_controls(view)
        fifth = [x for x in view.children if x._rendered_row == 4]
        self.assertIsInstance(fifth[0], navigation.AdministrativeBack)
        self.assertIsInstance(fifth[-1], navigation.AdministrativeClose)
        self.assertEqual(len(fifth), 5)
        self.assertEqual(len(view.children), 9)

    async def test_nearly_full_rows_keep_both_buttons_without_sacrificing_actions(self):
        view = ParentPanel()
        for row in range(5):
            for index in range(4):
                view.add_item(discord.ui.Button(label=f"Acción {row}-{index}", row=row))
        navigation.ensure_navigation_controls(view)
        self.assertEqual(len(view.children), 22)
        back = next(x for x in view.children if isinstance(x, navigation.AdministrativeBack))
        close = next(x for x in view.children if isinstance(x, navigation.AdministrativeClose))
        self.assertEqual((back._rendered_row, close._rendered_row), (3, 4))


    async def test_actual_setup_home_has_close_but_never_back(self):
        from test_safety_regressions import b
        home = b.HeraldoSetupView(345, 6)
        home._heraldo_back_target = ParentPanel()  # Even stale navigation state is ignored.
        navigation.ensure_navigation_controls(home)
        navigation.ensure_navigation_controls(home)
        self.assertIs(home.children[0], home.module_select)
        self.assertEqual(len(home.children), 2)
        self.assertFalse(any(isinstance(item, navigation.AdministrativeBack)
                             or getattr(item, "label", "") in navigation.variants("text.ab26ae7bca3621")
                             for item in home.children))
        self.assertIs(home.children[-1], home.close)
        self.assertEqual(home.close.style, discord.ButtonStyle.danger)

    async def test_setup_home_cleans_old_back_and_duplicate_close(self):
        from test_safety_regressions import b
        home = b.HeraldoSetupView(345, 6)
        home.add_item(navigation.AdministrativeBack(345, 6))
        home.add_item(discord.ui.Button(label="Cerrar", row=1))
        navigation.ensure_navigation_controls(home)
        buttons = [item for item in home.children if isinstance(item, discord.ui.Button)]
        self.assertEqual(buttons, [home.close])
        self.assertEqual(len(home.children), 2)



if __name__ == "__main__":
    unittest.main()
