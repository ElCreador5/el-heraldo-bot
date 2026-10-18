"""Regresiones de aislamiento y privacidad del backport Honeypot en main.

No importa bot.py ni conecta a Discord o SQLite productivos.
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).with_name("bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def definition(name):
    matches = [node for node in TREE.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    assert len(matches) == 1, (name, len(matches))
    return ast.get_source_segment(SOURCE, matches[0])


class HoneypotSelectiveMainTests(unittest.TestCase):
    def test_misfire_guard_precedes_message_deletion(self):
        func = definition("hp_handle_trigger")
        self.assertLess(func.index("if len(affected) >= HONEYPOT_MISFIRE_THRESHOLD"), func.index("await message.delete()"))
        self.assertIn("item[1] != guild.id", func)
        self.assertIn("guild_id == guild.id", func)

    def test_report_only_never_deletes_disparador(self):
        self.assertIn('if action != "log":', definition("hp_handle_trigger"))
        self.assertIn('if hp_action(message.guild.id) != "log":', SOURCE)

    def test_history_and_logs_do_not_capture_message(self):
        func = definition("hp_log_trigger")
        self.assertIn('channel_id, "", action', func)
        report = definition("hp_report")
        self.assertNotIn("message.content", report)
        self.assertNotIn('name="Mensaje"', report)
        self.assertNotIn("attachments", report)

    def test_honeypot_skips_evidence_without_skipping_cases(self):
        func = definition("_condemn_member_inner")
        self.assertIn('if origin == "honeypot":', func)
        self.assertIn("evidence_url, evidence_text = None, None", func)
        self.assertIn('include_message_history=(origin != "honeypot")', func)
        self.assertIn("moderation_case_create(", func)

    def test_existing_moderation_retains_history(self):
        func = definition("moderation_case_create")
        self.assertIn("include_message_history: bool = True", func)
        self.assertIn("if include_message_history else None", func)

    def test_inflight_is_guild_scoped(self):
        self.assertIn("key = (message.guild.id, member.id)", definition("honeypot_listener"))
        self.assertIn("_hp_busy.add(key)", definition("honeypot_listener"))
        self.assertIn("_hp_busy.discard(key)", definition("honeypot_listener"))


    def test_sanctions_require_explicit_storage(self):
        value = definition("hp_action")
        self.assertIn('"kick_enabled"', value)
        self.assertIn('"ban_enabled"', SOURCE)
        self.assertIn('return "role"', value)

    def test_kick_purges_by_author_without_discord_delete_messages(self):
        fn = definition("hp_punish")
        self.assertIn("await member.kick(reason=reason)", fn)
        self.assertIn("run_purge_job(", fn)
        self.assertIn("hp_kick_purge_minutes(guild.id)", fn)
        self.assertNotIn("delete_message_days", fn)

    def test_ban_explicit_duration_and_case(self):
        fn = definition("hp_punish")
        self.assertIn("hp_ban_override_minutes(guild.id)", fn)
        self.assertIn("if duration is None:", fn)
        self.assertIn("delete_message_seconds=0", fn)
        self.assertIn("include_message_history=False", fn)

    def test_sanction_permissions_and_hierarchy(self):
        fn = definition("hp_punish")
        self.assertIn("hp_sanction_permission_problem", fn)
        self.assertIn("member.id == guild.owner_id", fn)
        self.assertIn("member.top_role >= me.top_role", fn)

    def test_kick_purge_minimum_is_one_day(self):
        fn = definition("hp_kick_purge_minutes")
        self.assertIn("minutes if 1440 <= minutes <= 30 * 1440 else 1440", fn)


    def test_storage_values_are_safe_in_execution(self):
        code = compile(definition("hp_action"), "<isolated-honeypot-action>", "exec")
        for stored, wanted in (
            ("kick", "role"), ("ban", "role"), ("kick_enabled", "kick"),
            ("ban_enabled", "ban"), ("log", "log"), ("timeout", "timeout"),
            ("role", "role"), (None, "role"),
        ):
            namespace = {
                "hp_setting_get": lambda guild_id, name, value=stored: value,
                "HONEYPOT_DESTRUCTIVE_ACTION_STORAGE": {
                    "kick": "kick_enabled", "ban": "ban_enabled",
                },
            }
            exec(code, namespace)
            self.assertEqual(namespace["hp_action"](123), wanted)

    def test_setup_save_is_explicit_and_revalidated(self):
        panel = SOURCE[
            SOURCE.index("class HeraldoHoneypotSetupView("):
            SOURCE.index("class HoneypotPublishWarningConfirmView(")
        ]
        self.assertIn("Guardar cambios", panel)
        self.assertIn("Descartar cambios", panel)
        self.assertIn("pending_action", panel)
        self.assertIn("pending_ban_minutes", panel)
        self.assertIn("pending_kick_purge_minutes", panel)
        self.assertIn("self._snapshot() != self._original_config", panel)
        self.assertIn("hp_action_storage(self.pending_action)", panel)
        select = panel[panel.index("async def select_action"):panel.index("async def interaction_check")]
        self.assertNotIn("hp_setting_set(", select)

    def test_notice_publication_requires_confirmation_and_rechecks(self):
        code = SOURCE[
            SOURCE.index("class HoneypotPublishWarningConfirmView("):
            SOURCE.index("class HoneypotCreateChannelConfirmView(")
        ]
        self.assertIn("Confirmar publicación", code)
        self.assertIn("self.original_notice", code)
        self.assertIn("self.original_traps", code)
        self.assertIn("hp_sync_all_warnings(guild)", code)
        self.assertIn("self.finished = True", code)
        self.assertIn("read_message_history", code)
        self.assertIn("Cancelar", code)

    def test_notice_confirmation_ack_and_ownership_before_writes(self):
        code = SOURCE[
            SOURCE.index("class HoneypotPublishWarningConfirmView("):
            SOURCE.index("class HoneypotCreateChannelConfirmView(")
        ]
        confirm = code[code.index("async def confirm("):code.index("@discord.ui.button(label=\"Cancelar\"")]
        self.assertLess(confirm.index("await interaction.response.defer()"), confirm.index("hp_sync_all_warnings(guild)"))
        self.assertLess(confirm.index("self.finished = True"), confirm.index("await self._allowed(interaction)"))
        self.assertLess(confirm.index("await self._allowed(interaction)"), confirm.index("hp_setting_set("))
        allowed = code[code.index("async def _allowed("):code.index("@discord.ui.button(label=\"Confirmar publicación\"")]
        self.assertIn("guild.id != self.parent.guild_id", allowed)
        self.assertIn("interaction.user.id != self.parent.owner_id", allowed)
        self.assertIn("perms.manage_guild or perms.administrator", allowed)
        cancel = code[code.index("async def cancel("):]
        self.assertIn("await interaction.response.defer()", cancel)
        self.assertNotIn("hp_setting_set(", cancel)
        self.assertIn("await self._dismiss(interaction)", cancel)

    def test_new_channel_requires_confirmation_and_revalidates(self):
        code = SOURCE[
            SOURCE.index("class HoneypotCreateChannelConfirmView("):
            SOURCE.index("def heraldo_permissions_summary(")
        ]
        self.assertIn("Confirmar", code)
        self.assertIn("self.original_traps", code)
        self.assertIn("guild.create_text_channel(", code)
        self.assertIn("_setup_apply_system_channel(", code)
        self.assertIn("Cancelar", code)

    def test_notice_modals_only_prepare_confirmation(self):
        text = SOURCE[
            SOURCE.index("class HoneypotWarningModal("):
            SOURCE.index("class HoneypotSlashConfigConfirmView(")
        ]
        embed = SOURCE[
            SOURCE.index("class HoneypotWarningEmbedModal("):
            SOURCE.index("@honeypot_group.command(name=\"warning_embed\"")
        ]
        for modal in (text, embed):
            submit = modal[modal.index("async def on_submit"): ]
            self.assertIn("HoneypotNoticeEditConfirmView(", submit)
            self.assertNotIn("hp_setting_set(", submit)
            self.assertNotIn("hp_sync_all_warnings(", submit)
        confirm = SOURCE[
            SOURCE.index("class HoneypotNoticeEditConfirmView("):
            SOURCE.index("class HoneypotWarningModal(")
        ]
        self.assertIn("self.finished", confirm)
        self.assertIn("hp_setting_set(", confirm)
        self.assertIn("La configuración cambió", confirm)
        cancel = confirm[confirm.index("async def cancel"):]
        self.assertNotIn("hp_setting_set(", cancel)

    def test_warning_updates_are_serialized_by_channel(self):
        wrapper = definition("hp_sync_warning")
        worker = definition("_hp_sync_warning_locked")
        self.assertIn("key = (channel.guild.id, channel.id)", wrapper)
        self.assertIn("_hp_warning_locks.setdefault(key, asyncio.Lock())", wrapper)
        self.assertIn("async with lock:", wrapper)
        self.assertIn("await _hp_sync_warning_locked(channel)", wrapper)
        self.assertIn("channel.fetch_message(msg_id)", worker)
        self.assertIn("hp_set_warning_message(channel.guild.id, channel.id, message.id)", worker)
        self.assertLess(
            worker.index("hp_set_warning_message(channel.guild.id, channel.id, message.id)"),
            worker.index("await message.pin()"),
        )



# Pruebas funcionales del comportamiento real, aisladas del proceso de Discord.
# Extraen las funciones para ejecutarlas con dobles de SQLite/Discord; no importa bot.py.
import asyncio
import copy
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace as Namespace
from unittest.mock import AsyncMock, Mock


def isolated_function(name: str, namespace: dict):
    node = next(n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    standalone = copy.deepcopy(node)
    standalone.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[standalone], type_ignores=[]))
    exec(compile(module, "<isolated-honeypot-runtime>", "exec"), namespace)
    return namespace[name]


class HoneypotBehaviorTests(unittest.IsolatedAsyncioTestCase):
    async def _expiry_case(self, case_type: str, fail: str | None):
        class HttpError(Exception):
            pass

        class MissingError(HttpError):
            pass

        row = {
            "guild_id": 123,
            "user_id": 456,
            "case_number": 7,
            "type": case_type,
            "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat(),
        }
        connection = Mock()
        connection.execute.return_value.fetchall.return_value = [row]
        member = Namespace(timeout=AsyncMock())
        guild = Namespace(
            id=123,
            get_member=lambda user_id: member,
            unban=AsyncMock(),
        )
        action = member.timeout if case_type == "MUTE" else guild.unban
        if fail == "http":
            action.side_effect = HttpError()
        elif fail == "missing":
            action.side_effect = MissingError()
        close = Mock()
        ns = {
            "datetime": datetime,
            "timezone": timezone,
            "timedelta": timedelta,
            "db_connect": lambda: connection,
            "sqlite3": Namespace(Row=object),
            "bot": Namespace(get_guild=lambda guild_id: guild),
            "discord": Namespace(
                Object=lambda id: Namespace(id=id),
                NotFound=MissingError,
                HTTPException=HttpError,
            ),
            "moderation_case_code": lambda number, guild_id: "C000001",
            "moderation_case_close": close,
            "traceback": Namespace(print_exc=lambda: None),
        }
        function = isolated_function("moderation_case_expiry_loop", ns)
        await function()
        return action, close

    async def test_expired_ban_retries_when_discord_rejects_unban(self):
        action, close = await self._expiry_case("BAN", "http")
        action.assert_awaited_once()
        close.assert_not_called()

    async def test_expired_ban_closes_after_unban(self):
        action, close = await self._expiry_case("BAN", None)
        action.assert_awaited_once()
        close.assert_called_once_with(123, 7, closed_by=None, resolution="Expirado automáticamente")

    async def test_expired_ban_already_removed_is_idempotent(self):
        action, close = await self._expiry_case("BAN", "missing")
        action.assert_awaited_once()
        close.assert_called_once()

    async def test_expired_timeout_retries_when_discord_rejects(self):
        action, close = await self._expiry_case("MUTE", "http")
        action.assert_awaited_once()
        close.assert_not_called()

    async def test_purge_collects_only_infractor_messages(self):
        # Un mensaje de otra persona nunca entra en la lista que se envía a borrar.
        messages = [
            Namespace(id=1001, author=Namespace(id=777)),
            Namespace(id=1002, author=Namespace(id=888)),
            Namespace(id=1003, author=Namespace(id=777)),
        ]

        class Channel:
            async def history(self, **kwargs):
                for message in messages:
                    yield message

        ns = {"_purge_message_matches": lambda message, kind: True}
        collect = isolated_function("_collect_user_messages", ns)
        self.assertEqual(await collect(Channel(), 777, None, None, None), [1001, 1003])
        self.assertEqual(await collect(Channel(), 888, None, None, None), [1002])

    async def test_purge_scans_channels_without_storing_evidence(self):
        # Aislamiento: no se proporcionan funciones de archivo de evidencias.
        permissions = Namespace(view_channel=True, read_message_history=True, manage_messages=True)
        channels = [
            Namespace(id=4, permissions_for=lambda member: permissions),
            Namespace(id=5, permissions_for=lambda member: permissions),
        ]
        scanned_users = []

        async def collect(channel, user_id, after, before, limit, content_type):
            scanned_users.append(user_id)
            return [channel.id * 100 + 1]

        async def erase(channel, ids):
            return len(ids), 0

        ns = {
            "discord": Namespace(Guild=object),
            "datetime": datetime,
            "PurgeResult": lambda: Namespace(
                deleted=0, failed=0, channels_scanned=0, channels_skipped=0,
            ),
            "asyncio": asyncio,
            "purge_targets": AsyncMock(return_value=channels),
            "_collect_user_messages": collect,
            "_delete_ids": erase,
        }
        purge = isolated_function("purge_user_messages", ns)
        result = await purge(Namespace(me=object()), 777, after=datetime.now(timezone.utc) - timedelta(days=1))
        self.assertEqual(scanned_users, [777, 777])
        self.assertEqual(result.deleted, 2)
        self.assertEqual(result.channels_scanned, 2)
        self.assertEqual(result.channels_skipped, 0)


if __name__ == "__main__":
    unittest.main()
