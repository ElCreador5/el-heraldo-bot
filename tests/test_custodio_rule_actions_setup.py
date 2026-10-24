"""Regresiones del editor de acciones de Custodio; no necesita Gateway."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from custodio_rule_actions import DEFAULT_ACTIONS, SETTING_KEY, decode_actions
from custodio_rule_actions_setup import CustodioRuleActionsView


class RuleActionsSetupTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = {}
        self.writes = []
        self.get = lambda guild_id, key: self.db.get((guild_id, key))

        def save_atomic(guild_id, old, new):
            self.writes.append((guild_id, old.copy(), new.copy()))
            if any(self.get(guild_id, key) != value for key, value in old.items()):
                return False
            for key, value in new.items():
                self.db[(guild_id, key)] = value
            return True

        self.parent = SimpleNamespace(
            guild_id=123, owner_id=456, get_setting=self.get,
            save_atomic=save_atomic,
            access_check=AsyncMock(return_value=True),
            _sync_controls=lambda: None,
            summary=lambda: "Modo Custodio",
        )
        self.view = CustodioRuleActionsView(self.parent)
        self.interaction = SimpleNamespace(
            response=SimpleNamespace(
                edit_message=AsyncMock(), defer=AsyncMock(),
            ),
            edit_original_response=AsyncMock(),
        )

    async def test_opening_and_selecting_never_write(self):
        self.assertEqual(self.db, {})
        self.assertFalse(self.view._dirty())
        self.assertTrue(self.view.save_button.disabled)
        self.assertIn("sin expulsiones ni baneos automáticos", self.view.summary())
        self.view.selected_category = "scams"
        self.view.action_selector._values = ["ban"]
        await self.view.choose_action(self.interaction)
        self.assertTrue(self.view._dirty())
        self.assertEqual(self.writes, [])
        self.assertEqual(self.db, {})

    async def test_direct_save_is_inactive_and_per_guild(self):
        self.view.selected_category = "scams"
        self.view.pending_actions["scams"] = "ban"
        self.view._sync_controls()
        await self.view.save_changes(self.interaction)
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(self.writes[0][1], {SETTING_KEY: None})
        policy, valid = decode_actions(self.db[(123, SETTING_KEY)])
        self.assertTrue(valid)
        self.assertEqual(policy["scams"], "ban")
        self.assertFalse(self.view._dirty())
        self.assertTrue(self.view.save_button.disabled)
        self.assertIsNone(self.get(999, SETTING_KEY))
        self.interaction.response.defer.assert_awaited_once()

    async def test_discard_and_back_do_not_save(self):
        self.view.pending_actions["threats"] = "ban"
        await self.view.back(self.interaction)
        self.assertEqual(self.writes, [])
        self.interaction.response.edit_message.assert_awaited()
        self.assertIn("Guarde o descarte", self.interaction.response.edit_message.call_args.kwargs["content"])
        await self.view.discard_changes(self.interaction)
        await self.view.back(self.interaction)
        self.assertEqual(self.db, {})
        self.assertEqual(self.interaction.response.edit_message.call_args.kwargs["content"], "Modo Custodio")

    async def test_concurrent_editor_uses_cas_and_does_not_overwrite(self):
        self.view.pending_actions["scams"] = "ban"
        other = DEFAULT_ACTIONS.copy()
        other["harassment"] = "kick"
        from custodio_rule_actions import encode_actions
        raw = encode_actions(other)
        self.db[(123, SETTING_KEY)] = raw
        await self.view.save_changes(self.interaction)
        self.assertEqual(self.db[(123, SETTING_KEY)], raw)
        self.assertEqual(self.view.pending_actions, other)
        self.assertFalse(self.view._dirty())

    async def test_user_permission_checked_by_parent(self):
        self.assertTrue(await self.view.interaction_check(self.interaction))
        self.parent.access_check.assert_awaited_once_with(self.interaction, 123, 456)


if __name__ == "__main__":
    unittest.main()
