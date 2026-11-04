"""Draft, CAS save and cancellation for the historical structure scheduler."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import unittest

from test_safety_regressions import b, interaction
from server_structure_setup import FIELDS, MARKERS, ServerStructureSetupView, StructureScheduleModal, StructureSaveConfirmView, StructureSyncConfirmView, last_slot


class ServerStructureTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.guild_id=445566
        self.host=vars(b)
        self.original={"template_mode":"weekly","template_hour":"9","template_minute":"0","template_weekday":"3",
                       "template_monthday":"1","template_interval_minutes":"1440",
                       "template_last_run":"2026-10-01T09:00:00+00:00","template_last_slot":"2026-10-01T09:00:00-04:00"}
        for key,value in self.original.items():b.guild_config_set(self.guild_id,key,value)

    def view(self):
        return ServerStructureSetupView(self.host,self.guild_id,10)

    def snapshot(self):
        return {key:b.guild_config_get(self.guild_id,key) for key in (*FIELDS,*MARKERS)}

    async def test_choose_and_modal_edit_only_the_draft_and_keep_selection(self):
        view=self.view()
        self.assertTrue(view.save.disabled)
        i=interaction(guild_id=self.guild_id); i.data={"values":["daily"]}
        await view.choose(i)
        modal=StructureScheduleModal(view)
        for field,value in (("clock","6:15 p. m."),("weekday","2"),("monthday","14"),("interval","120")):
            getattr(modal,field)._value=value
        await modal.on_submit(i)
        self.assertEqual(view.values["template_hour"],"18")
        self.assertEqual(view.values["template_minute"],"15")
        self.assertEqual([x.value for x in view.chooser.options if x.default],["daily"])
        self.assertEqual(self.snapshot(),self.original)
        self.assertFalse(view.save.disabled)

    async def test_save_only_commits_after_confirmation_then_refreshes(self):
        view=self.view(); view.values["template_hour"]="12"
        i=interaction(guild_id=self.guild_id)
        await view.save.callback(i)
        self.assertEqual(self.snapshot(),self.original)
        confirmation=i.response.edit_message.call_args.kwargs["view"]
        await confirmation.confirm.callback(i)
        self.assertEqual(b.guild_config_get(self.guild_id,"template_hour"),"12")
        fresh=i.response.edit_message.call_args.kwargs["view"]
        self.assertIsInstance(fresh,ServerStructureSetupView)
        self.assertTrue(fresh.save.disabled)
        after=self.snapshot()
        await confirmation.confirm.callback(i)
        self.assertEqual(self.snapshot(),after)

    async def test_discard_close_and_back_do_not_save(self):
        view=self.view(); view.values["template_mode"]="daily"
        i=interaction(guild_id=self.guild_id)
        confirmation=StructureSaveConfirmView(view)
        await confirmation.back.callback(i)
        self.assertEqual(view.values["template_mode"],"daily")
        await view.discard.callback(i)
        self.assertEqual(view.values,view.initial)
        view.values["template_mode"]="interval"
        await view.close.callback(i)
        self.assertEqual(self.snapshot(),self.original)

    async def test_permission_revoked_blocks_confirmation(self):
        view=self.view(); view.values["template_mode"]="daily"
        confirmation=StructureSaveConfirmView(view)
        await confirmation.confirm.callback(interaction(False,self.guild_id))
        self.assertEqual(self.snapshot(),self.original)

    async def test_concurrent_schedule_tick_or_edit_cannot_be_overwritten(self):
        for key in ("template_last_run","template_hour"):
            self.setUp()
            view=self.view(); view.values["template_mode"]="interval"
            confirmation=StructureSaveConfirmView(view)
            b.guild_config_set(self.guild_id,key,"15" if key=="template_hour" else "2026-11-02T12:00:00+00:00")
            expected=self.snapshot()
            await confirmation.confirm.callback(interaction(guild_id=self.guild_id))
            self.assertEqual(self.snapshot(),expected)

    async def test_late_modal_and_invalid_ranges_do_not_change_settings(self):
        view=self.view(); modal=StructureScheduleModal(view)
        modal.clock._value="25:00"
        i=interaction(guild_id=self.guild_id)
        await modal.on_submit(i)
        self.assertEqual(self.snapshot(),self.original)
        modal.clock._value="12:00 PM"; view.stop()
        await modal.on_submit(i)
        self.assertEqual(view.values,view.initial)

    async def test_interval_starts_at_selected_clock_not_save_time(self):
        view=self.view()
        view.values.update({
            "template_mode":"interval", "template_hour":"18",
            "template_minute":"15", "template_interval_minutes":"360",
        })
        i=interaction(guild_id=self.guild_id)
        await StructureSaveConfirmView(view).confirm.callback(i)
        first=b.template_next_run(self.guild_id, datetime.now(timezone.utc))
        local=first.astimezone(b.STREAK_TZ)
        self.assertEqual((local.hour,local.minute),(18,15))
        self.assertFalse(i.response.send_message.await_count)

    async def test_sync_confirm_sends_link_to_owner_without_saving_schedule(self):
        guild_id = self.guild_id
        view = self.view()
        baseline = self.snapshot()
        i = interaction(guild_id=guild_id)
        i.guild.owner_id = 999
        await view.sync_now.callback(i)
        confirm = i.response.edit_message.call_args.kwargs["view"]
        self.assertIsInstance(confirm, StructureSyncConfirmView)
        self.assertEqual(baseline, self.snapshot())
        sent = AsyncMock()
        owner = type("Owner", (), {"send": sent})()
        report = b.discord.Embed(title="Copia de seguridad")
        with (patch.object(b, "sync_server_template", new=AsyncMock(return_value=(object(), False, None))) as sync,
              patch.object(b.bot, "fetch_user", new=AsyncMock(return_value=owner)) as fetch,
              patch.object(b, "template_report_embed", return_value=report),
              patch.object(b, "stamp_embed", side_effect=lambda embed, guild: embed),
              patch.object(b, "log_embed", new=AsyncMock())):
            await confirm.execute.callback(i)
            sync.assert_awaited_once_with(i.guild)
            fetch.assert_awaited_once_with(999)
            sent.assert_awaited_once()
            self.assertEqual(baseline, self.snapshot())
            self.assertIn("sincronizada", i.followup.send.call_args.args[0].lower())

    async def test_sync_with_unsaved_schedule_is_blocked(self):
        view = self.view()
        view.values["template_mode"] = "interval"
        i = interaction(guild_id=self.guild_id)
        await view.sync_now.callback(i)
        self.assertIsNone(i.response.edit_message.call_args)
        self.assertEqual(self.snapshot(), self.original)

    def test_monthly_slot_uses_previous_month_without_touching_a_database(self):
        slot=last_slot({"template_mode":"monthly","template_hour":"9","template_monthday":"28"},
                       datetime(2026,11,1,8,tzinfo=timezone.utc))
        self.assertEqual(slot,datetime(2026,10,28,9,tzinfo=timezone.utc))
