"""Navigation order in main; no Discord Gateway or production database."""
import unittest
from types import SimpleNamespace as NS

import discord

from panel_navigation import AdministrativeBack, AdministrativeClose, ensure_navigation_controls
from main_panel_navigation import remember_previous_panel, _source_view, _source_interaction


class Panel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.guild_id = 100
        self.owner_id = 200


class HeraldoSetupView(Panel):
    """Match the real root view type without importing bot.py."""


class NavigationOrderMainTests(unittest.TestCase):
    def test_root_setup_only_close_and_no_back_even_on_repeat(self):
        view = HeraldoSetupView()
        view.add_item(discord.ui.Select(
            placeholder="Selecciona",
            row=0,
            options=[discord.SelectOption(label="Logs", value="logs")],
        ))
        close = discord.ui.Button(label="Cerrar", row=1)
        view.add_item(close)
        view.add_item(discord.ui.Button(label="Volver", row=2))
        ensure_navigation_controls(view)
        ensure_navigation_controls(view)
        self.assertEqual(
            [x.label for x in view.children if isinstance(x, discord.ui.Button)],
            ["Cerrar"],
        )
        self.assertIs(view.children[-1], close)
        self.assertEqual(close.style, discord.ButtonStyle.danger)

    def test_two_buttons_share_row_back_first_close_last(self):
        view = Panel()
        ensure_navigation_controls(view)
        ensure_navigation_controls(view)
        buttons = [x for x in view.children if isinstance(x, discord.ui.Button)]
        self.assertEqual(len(buttons), 2)
        self.assertIsInstance(buttons[0], AdministrativeBack)
        self.assertIsInstance(buttons[1], AdministrativeClose)
        self.assertEqual(buttons[0]._rendered_row, buttons[1]._rendered_row)

    def test_existing_callbacks_are_not_replaced(self):
        view = Panel()
        back = discord.ui.Button(label="Volver", row=4)
        close = discord.ui.Button(label="Cerrar", row=3)
        view.add_item(close)
        view.add_item(back)
        view.add_item(discord.ui.Button(label="Volver", row=2))
        view.add_item(discord.ui.Button(label="Cerrar", row=1))
        ensure_navigation_controls(view)
        self.assertEqual(view.children, [back, close])
        self.assertEqual(view.children[0]._rendered_row, view.children[1]._rendered_row)
        self.assertEqual(back.style, discord.ButtonStyle.secondary)
        self.assertEqual(close.style, discord.ButtonStyle.danger)

    def test_capture_actual_previous_panel_without_loop(self):
        home = HeraldoSetupView()
        child = Panel()
        token_v = _source_view.set(home)
        token_i = _source_interaction.set(
            NS(message=NS(content="Inicio", embeds=[])))
        try:
            remember_previous_panel(child)
            remember_previous_panel(home)
        finally:
            _source_interaction.reset(token_i)
            _source_view.reset(token_v)
        self.assertIs(child._heraldo_back_target, home)
        self.assertEqual(child._heraldo_back_snapshot, {"content": "Inicio", "embed": None})
        self.assertFalse(hasattr(home, "_heraldo_back_target"))

    def test_public_personal_embed_is_not_given_administrative_buttons(self):
        view = Panel()
        view.personal = True
        ensure_navigation_controls(view)
        self.assertEqual(view.children, [])

    def test_back_and_close_fit_beside_existing_actions(self):
        view = Panel()
        for row in range(4):
            view.add_item(discord.ui.Select(
                placeholder="Opciones", row=row,
                options=[discord.SelectOption(label="A", value=str(row))]))
        for number in range(3):
            view.add_item(discord.ui.Button(label=f"Acción {number}", row=4))
        ensure_navigation_controls(view)
        fifth_row = [x for x in view.children if x._rendered_row == 4]
        self.assertEqual(len(fifth_row), 5)
        self.assertIsInstance(fifth_row[0], AdministrativeBack)
        self.assertIsInstance(fifth_row[-1], AdministrativeClose)


if __name__ == "__main__":
    unittest.main()
