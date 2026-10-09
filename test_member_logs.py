"""Regresiones sin conexión a Discord. Base SQLite desechable."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
import sys

_tmp = tempfile.TemporaryDirectory()
os.environ["DB_PATH"] = str(Path(_tmp.name) / "logs.db")
spec = importlib.util.spec_from_file_location("heraldo_member_logs_test", Path(__file__).with_name("bot.py"))
bot_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bot_module
spec.loader.exec_module(bot_module)
bot_module.db_init()

class MemberLogRegressions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        for gid in (777, 888):
            for event in bot_module.MEMBER_LOG_EVENTS:
                bot_module.guild_config_set(gid, f"log_member.enabled.{event}", "0")

    async def test_disabled_by_default_and_separate_per_server(self):
        self.assertFalse(bot_module.log_member_event_enabled(777, "member_warn"))
        bot_module.guild_config_set(777, "log_member.enabled.member_warn", "1")
        self.assertTrue(bot_module.log_member_event_enabled(777, "member_warn"))
        self.assertFalse(bot_module.log_member_event_enabled(888, "member_warn"))
        self.assertFalse(bot_module.log_member_event_enabled(777, "member_ban"))

    async def test_channel_per_event(self):
        bot_module.guild_config_set(777, "log_member.channel.member_leave", "12345")
        bot_module.guild_config_set(777, "log_member.channel.member_kick", "67890")
        self.assertEqual(bot_module.log_member_channel_id(777, "member_leave"), 12345)
        self.assertEqual(bot_module.log_member_channel_id(777, "member_kick"), 67890)

    async def test_event_category(self):
        for key, title in bot_module.LOG_EVENT_CATALOG["members"]:
            self.assertEqual(bot_module.log_event_category(title), "members")
            self.assertEqual(bot_module.log_event_key(title, "members"), key)

    async def test_editor_draft_does_not_save_immediately(self):
        original = bot_module.log_template_get(777, "members", "title", "member_leave")
        view = bot_module.LogTemplateSaveConfirmView(
            777, 99, "members", "member_leave",
            {"title": "Salida personalizada"}, "messages_setup")
        self.assertEqual(bot_module.log_template_get(777, "members", "title", "member_leave"), original)
        view.stop()

if __name__ == "__main__":
    unittest.main()
