"""Honeypot: configuración contextual en /setup y purga segura tras expulsión."""
import asyncio
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

from test_safety_regressions import b, interaction


class HoneypotKickPurgeSetupTests(unittest.IsolatedAsyncioTestCase):
    def make_view(self, action="kick"):
        patches = [
            patch.object(b, "hp_traps", return_value={123: None}),
            patch.object(b, "honeypot_enabled", return_value=True),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "hp_action", return_value=action),
        ]
        for ctx in patches:
            ctx.start()
            self.addCleanup(ctx.stop)
        return b.HeraldoHoneypotSetupView(901, 10)

    def test_kick_purge_defaults_to_one_day_and_never_under(self):
        for raw, expected in [(None, 1440), ("", 1440), ("5", 1440),
                              ("-1", 1440), ("2880", 2880),
                              ("100000", 1440), ("bad", 1440)]:
            with self.subTest(raw=raw), patch.object(b, "hp_setting_get", return_value=raw):
                self.assertEqual(b.hp_kick_purge_minutes(901), expected)

    async def test_kick_purge_uses_shared_safe_purge_job_with_one_day_cutoff(self):
        member = NS(id=88, guild=NS(id=901), mention="<@88>")
        event = AsyncMock()
        with (
            patch.object(b, "hp_kick_purge_minutes", return_value=1440),
            patch.object(b, "run_purge_job", new=event),
        ):
            note = b.hp_start_kick_purge(member)
            await asyncio.sleep(0)
        event.assert_awaited_once()
        args, kwargs = event.await_args
        self.assertIs(args[0], member.guild)
        self.assertIs(args[1], member)
        self.assertEqual(kwargs["requested_by"], "Honeypot · Expulsión")
        self.assertIsNone(kwargs.get("limit"))
        self.assertGreaterEqual((b.datetime.now(b.timezone.utc) - kwargs["after"]).total_seconds(), 86390)
        self.assertLess((b.datetime.now(b.timezone.utc) - kwargs["after"]).total_seconds(), 86500)
        self.assertEqual(kwargs["purge_origin"], "honeypot")
        self.assertIn("sin archivo de evidencias", note)

    async def test_configure_measure_stages_kick_duration_in_main_draft(self):
        view = self.make_view()
        measure = b.HeraldoHoneypotParametersView(view)
        kick_select = [c for c in measure.children if isinstance(c, b.discord.ui.Select)]
        self.assertEqual(len(kick_select), 1)
        self.assertEqual({int(o.value) for o in kick_select[0].options}, {
            1440, 2880, 4320, 10080, 20160, 43200,
        })
        i = interaction()
        i.data = {"values": ["2880"]}
        with patch.object(b, "hp_setting_set") as save:
            await kick_select[0].callback(i)
        self.assertEqual(view.pending_kick_purge_minutes, 2880)
        save.assert_not_called()
        i.response.edit_message.assert_awaited_once()
        self.assertTrue(any("2 d" in line for line in view._pending_lines(i.guild)))

    async def test_discard_clears_kick_purge_draft_without_writes(self):
        view = self.make_view()
        view.pending_kick_purge_minutes = 10080
        with (
            patch.object(b, "hp_setting_set") as save,
            patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()),
        ):
            await view.discard_changes.callback(interaction())
        save.assert_not_called()
        self.assertIsNone(view.pending_kick_purge_minutes)

    async def test_save_kick_purge_requires_explicit_guarded_commit(self):
        view = self.make_view()
        view.pending_kick_purge_minutes = 4320
        i = interaction()
        with (
            patch.object(b, "hp_setting_set") as save,
            patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()),
        ):
            await view.save_changes.callback(i)
        save.assert_called_once_with(901, "honeypot_kick_purge_minutes", "4320")
        i.response.defer.assert_awaited_once()
        self.assertIsNone(view.pending_kick_purge_minutes)

    async def test_concurrent_changed_purge_blocks_save(self):
        with patch.object(b, "hp_kick_purge_minutes", side_effect=[1440, 2880]), \
             patch.object(b, "hp_traps", return_value={123: None}), \
             patch.object(b, "hp_action", return_value="kick"), \
             patch.object(b, "honeypot_enabled", return_value=True), \
             patch.object(b, "honeypot_paused", return_value=False):
            view = b.HeraldoHoneypotSetupView(901, 10)
            view.pending_kick_purge_minutes = 10080
            i = interaction()
            with patch.object(b, "hp_setting_set") as save:
                await view.save_changes.callback(i)
        save.assert_not_called()
        self.assertIn("configuración cambió", i.response.send_message.call_args.args[0])

    def test_ui_parameters_adapt_to_action_without_slash_dependency(self):
        for action, count in [("kick", 1), ("ban", 1), ("role", 1),
                              ("timeout", 2), ("log", 0)]:
            with self.subTest(action=action):
                view = self.make_view(action)
                editor = b.HeraldoHoneypotActionView(view)
                self.assertEqual(editor.parameters.disabled, action == "log")
                self.assertNotIn("`/honeypot setup`", editor._embed(NS(id=901)).description)
                params = b.HeraldoHoneypotParametersView(view)
                options = [c for c in params.children if isinstance(c, b.discord.ui.Select)]
                self.assertEqual(len(options), count)

    async def test_ban_and_timeout_can_be_staged_from_setup(self):
        view = self.make_view("ban")
        ban = b.HeraldoHoneypotParametersView(view)
        chooser = next(c for c in ban.children if isinstance(c, b.discord.ui.Select))
        i = interaction()
        i.data = {"values": ["1440"]}
        with patch.object(b, "hp_setting_set") as save:
            await chooser.callback(i)
        self.assertEqual(view.pending_ban_minutes, 1440)
        save.assert_not_called()

        view2 = self.make_view("timeout")
        timeout = b.HeraldoHoneypotParametersView(view2)
        selectors = [c for c in timeout.children if isinstance(c, b.discord.ui.Select)]
        i2 = interaction()
        i2.data = {"values": ["360"]}
        await selectors[0].callback(i2)
        self.assertEqual(view2.pending_timeout_minutes, 360)
        i3 = interaction()
        # Elegir el valor ya guardado (1 día) no genera borrador; cambiar a 3 días sí.
        i3.data = {"values": ["time:4320"]}
        await selectors[1].callback(i3)
        self.assertEqual(view2.pending_purge_spec, ("time", 4320))

    def test_ban_override_uses_separate_setting_from_global_moderation(self):
        with (
            patch.object(b, "hp_setting_get", return_value=None),
            patch.object(b, "moderation_default_ban_minutes", return_value=5),
        ):
            self.assertIsNone(b.hp_ban_override_minutes(901))
            self.assertEqual(b.hp_ban_duration_minutes(901), 5)
        with patch.object(b, "hp_setting_get", return_value="0"):
            self.assertEqual(b.hp_ban_override_minutes(901), 0)
            self.assertIsNone(b.hp_ban_duration_minutes(901))


if __name__ == "__main__":
    unittest.main()
