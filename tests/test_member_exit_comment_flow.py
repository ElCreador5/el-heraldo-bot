"""Contrato conductual de la encuesta de salidas sin Discord Gateway."""
import ast
import unittest
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SRC)


def source(name):
    fn = next(n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name)
    return ast.get_source_segment(SRC, fn)


class ExitCommentsFlowTests(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertIn('guild_config_get(guild_id, "exit_comments_enabled") == "1"',
                      source("exit_comments_enabled"))

    def test_only_departure_logs_with_successful_audit_can_send_dm(self):
        handler = source("heraldo_member_departure")
        self.assertIn('kind == "member_leave"', handler)
        self.assertIn("original is not None", handler)
        self.assertIn('uncertainty.startswith("Salida observada;', handler)
        audit = source("classify_member_departure")
        self.assertIn("audit_checked = False", audit)
        self.assertIn("if not audit_checked:", audit)

    def test_one_dm_and_original_card_reference(self):
        sender = source("exit_comment_request")
        self.assertIn("exit_comments.create_pending", sender)
        self.assertIn("exit_comments.attach_dm", sender)
        self.assertIn("message.id", sender)
        self.assertIn("exit_comment_private(channel)", sender)
        self.assertIn("allowed_mentions=discord.AllowedMentions.none()", sender)

    def test_persistent_button_and_modal(self):
        button = source("ExitCommentDMView")
        self.assertIn("timeout=None", button)
        self.assertIn("heraldo:exitcomment:v1", button)
        self.assertIn("exit_comments.find_by_dm", button)
        modal = source("ExitCommentModal")
        self.assertIn("max_length=500", modal)
        self.assertIn("exit_comments.submit_comment", modal)

    def test_existing_card_edited_not_reposted(self):
        editor = source("exit_comment_apply")
        self.assertIn("channel.fetch_message", editor)
        self.assertIn("original.edit", editor)
        self.assertNotIn("channel.send(", editor)
        self.assertIn("exit_comments.mark_applied", editor)

    def test_retry_cleanup_and_private_overwrite_guard(self):
        audit = source("exit_comment_audit_safe")
        self.assertIn("await asyncio.sleep(4)", audit)
        self.assertIn("guild.audit_logs(", audit)
        self.assertIn("except (discord.Forbidden, discord.HTTPException)", audit)
        sender = source("exit_comment_request")
        self.assertIn("exit_comment_audit_safe(member)", sender)
        self.assertIn("await sent.edit(view=None)", sender)
        guard = source("exit_comment_private")
        self.assertIn("channel.overwrites.items()", guard)
        self.assertIn("verification_is_exempt(target)", guard)
        loop = source("exit_comment_maintenance_loop")
        self.assertIn("exit_comments.purge_expired(conn)", loop)
        self.assertIn("await exit_comment_retry()", loop)

    def test_nh_explicit_save_and_discard(self):
        view = source("ExitCommentSetupView")
        self.assertIn('label="Guardar cambios"', view)
        self.assertIn('label="Descartar cambios"', view)
        self.assertIn("self.pending = None", view)
        self.assertIn('guild_config_set(self.guild_id, "exit_comments_enabled"', view)
        self.assertIn("view_audit_log", view)
        self.assertIn("exit_comment_private(channel)", view)

    def test_views_registered_and_backwards_compatible(self):
        on_ready = source("on_ready")
        self.assertIn("exit_comments.init_storage(conn)", on_ready)
        self.assertIn("bot.add_view(ExitCommentDMView())", on_ready)
        self.assertIn("await exit_comment_retry()", on_ready)
        self.assertIn("exit_comment_maintenance_loop.start()", on_ready)
        self.assertIn("log_member_event_enabled", source("heraldo_member_departure"))


if __name__ == "__main__":
    unittest.main()
