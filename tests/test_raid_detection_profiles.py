"""Comportamiento del editor de Raid Protection sin Discord Gateway."""
import unittest
from unittest.mock import AsyncMock, patch
from test_safety_regressions import b, interaction

class RaidDetectionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.gid = 991032
        for key, value in zip(b.RAID_FIELDS, (11, 40, 2 * 86400, 45, 700)):
            b.guild_config_set(self.gid, key, str(value))

    def view(self):
        return b.HeraldoRaidDetectionView(b.HeraldoRaidSetupView(self.gid, 10))

    def i(self):
        return interaction(guild_id=self.gid)

    async def test_current_settings_are_preserved(self):
        v = self.view()
        self.assertEqual(v.active_profile(), "personalizada")
        self.assertEqual(v.draft["raid_threshold"], 11)
        self.assertTrue(any(x.default and x.value == "11"
                            for x in v.selectors["raid_threshold"].options))
        self.assertEqual(b.raid_threshold(self.gid), 11)

    async def test_preset_changes_draft_only(self):
        v = self.view()
        v.profile_select._values = ["equilibrada"]
        with patch.object(b, "guild_config_set") as write:
            await v.profile_select.callback(self.i())
        write.assert_not_called()
        self.assertEqual(v.active_profile(), "equilibrada")
        self.assertEqual(b.raid_threshold(self.gid), 11)
        self.assertEqual(v.draft["raid_threshold"], 10)

    async def test_advanced_discard_and_back(self):
        p = b.HeraldoRaidSetupView(self.gid, 10)
        p.pending_action = "log"
        v = b.HeraldoRaidDetectionView(p)
        v.draft = dict(zip(b.RAID_FIELDS, b.RAID_PRESETS["estricta"]))
        v.rebuild()
        await v.next_page(self.i())
        self.assertEqual(set(v.selectors), set(b.RAID_FIELDS[3:]))
        with patch.object(b, "guild_config_set") as write:
            await v.discard(self.i())
        write.assert_not_called()
        self.assertEqual(v.draft, v.original)
        await v.back(self.i())
        self.assertEqual(p.pending_action, "log")

    async def test_save_opens_only_explicit_confirmation(self):
        v = self.view()
        v.draft["raid_threshold"] = 15
        with patch.object(b, "confirm_configuration", new_callable=AsyncMock) as confirm, \
             patch.object(b, "guild_config_set") as write:
            await v.save(self.i())
        confirm.assert_awaited_once()
        self.assertEqual(confirm.call_args.args[2], {"raid_threshold": "15"})
        write.assert_not_called()

    async def test_invalid_combination_and_concurrent_change_block_save(self):
        v = self.view()
        v.draft["raid_min_age_seconds"] = 0
        with patch.object(b, "confirm_configuration", new_callable=AsyncMock) as confirm:
            await v.save(self.i())
        confirm.assert_not_awaited()
        v = self.view()
        v.draft["raid_threshold"] = 15
        b.guild_config_set(self.gid, "raid_threshold", "17")
        with patch.object(b, "confirm_configuration", new_callable=AsyncMock) as confirm:
            await v.save(self.i())
        confirm.assert_not_awaited()
        self.assertEqual(b.raid_threshold(self.gid), 17)

    async def test_custom_option_opens_modal_without_writing(self):
        v = self.view()
        sel = v.selectors["raid_window_seconds"]
        sel._values = ["custom"]
        i = self.i()
        i.response.send_modal = AsyncMock()
        with patch.object(b, "guild_config_set") as write:
            await sel.callback(i)
        write.assert_not_called()
        self.assertIsInstance(i.response.send_modal.call_args.args[0], b.HeraldoRaidCustomModal)

    def test_range_validation_and_safe_labels(self):
        self.assertEqual(b.raid_parse_choice("raid_window_seconds", "2m"), 120)
        self.assertEqual(b.raid_parse_choice("raid_min_age_seconds", "0"), 0)
        for key, value in (("raid_threshold", "1"),
                           ("raid_new_account_ratio", "101"),
                           ("raid_duration_seconds", "1s")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.raid_parse_choice(key, value)
        for options in (self.view().profile_select.options,
                        self.view().selectors["raid_threshold"].options):
            self.assertTrue(all(len(o.label) <= 100 and
                                len(o.description or "") <= 100 for o in options))

if __name__ == "__main__":
    unittest.main()
