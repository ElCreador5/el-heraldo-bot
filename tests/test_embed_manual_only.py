"""Embed building is manual; announcements keep their independent scheduler."""
import ast
from pathlib import Path
import unittest

from test_safety_regressions import b


class ManualEmbedsTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_scheduling_controls_or_registered_scheduling_command(self):
        self.assertFalse(hasattr(b.EmbedHubView(10,901), "schedules"))
        self.assertFalse(hasattr(b.EmbedEditorView(10,901,"draft",{}), "schedule_embed"))
        self.assertIsNone(b.embed_group.get_command("programaciones"))
        self.assertIsNotNone(b.bot.tree.get_command("anuncios"))
        self.assertIsInstance(b.message_automation_engine,b.message_automation.ScheduledMessages)

    def test_retired_embed_worker_is_not_started_or_registered_as_listener(self):
        tree=ast.parse(Path(b.__file__).read_text())
        ready=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=="on_ready")
        self.assertNotIn("scheduled_embeds_loop.start",ast.unparse(ready))
        listeners=b.bot.extra_events.get("on_message",[])
        self.assertNotIn("scheduled_embeds_message_counter",[f.__name__ for f in listeners])
