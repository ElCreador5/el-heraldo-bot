"""Regresión estructural de tarjeta de condena, acciones y conversación privada."""
import ast
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")


class CondemnationCardTests(unittest.TestCase):
    def test_source_compiles(self):
        compile(SOURCE, "bot.py", "exec")

    def test_card_has_four_actions_and_permission_checks(self):
        view = SOURCE[SOURCE.index("class CondemnationPardonView"):SOURCE.index("async def condemnation_send_dm")]
        for label in ('label="Perdonar"', '"Advertir"', '"Banear"', '"Expulsar"'):
            self.assertIn(label, view)
        for flag in ("moderate_members", "ban_members", "kick_members"):
            self.assertIn(flag, view)
        self.assertIn("condemnation_linked_case_is_open(row)", view)
        self.assertIn("CondemnationCaseConfirmView(", view)
        self.assertIn("INSERT OR IGNORE INTO condemnation_case_actions", view)
        self.assertIn("await interaction.response.defer(", view)

    def test_pardon_edits_original_card(self):
        start = SOURCE.index("async def condemnation_update_pardoned_card(")
        end = SOURCE.index("\n\ndef condemnation_role_id", start)
        implementation = SOURCE[start:end]
        self.assertIn("await message.edit(", implementation)
        self.assertIn("view=None", implementation)
        self.assertNotIn("await message.delete(", implementation)
        self.assertNotIn("await channel.send(", implementation)

    def test_private_thread_is_named_and_restricted(self):
        start = SOURCE.index("async def condemnation_ensure_private_thread(")
        end = SOURCE.index("async def condemnation_close_private_thread(", start)
        implementation = SOURCE[start:end]
        self.assertIn("discord.ChannelType.private_thread", implementation)
        self.assertIn("Expediente {case_id}", implementation)
        self.assertIn("await thread.add_user(current_member)", implementation)
        self.assertIn("view_channel", implementation)
        self.assertNotIn("discord.ChannelType.public_thread", implementation)

    def test_closing_case_removes_live_buttons(self):
        self.assertIn("async def condemnation_mark_closed_card(", SOURCE)
        self.assertIn('name="Estado del expediente"', SOURCE)
        self.assertIn('view=None', SOURCE[SOURCE.index("async def condemnation_mark_closed_card("):
                                          SOURCE.index("async def condemnation_close_private_thread(")])
        self.assertIn('await condemnation_mark_closed_card(interaction.guild, condemned, "Expediente cerrado")', SOURCE)


if __name__ == "__main__":
    unittest.main()
