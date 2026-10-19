"""Callbacks reales + SQLite desechable. No Gateway, tokens ni miembros reales."""
import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from test_regressions import b


def http_error(kind=b.discord.HTTPException, status=500):
    return kind(NS(status=status, reason="test"), "test")


def permissions(**overrides):
    values = dict(manage_guild=True, administrator=False, kick_members=True,
                  ban_members=True, manage_channels=True, view_channel=True,
                  send_messages=True, embed_links=True, read_message_history=True,
                  manage_messages=True, manage_threads=True, moderate_members=True)
    return NS(**{**values, **overrides})


def interaction(guild, user, values=()):
    response = NS(done=False, send_modal=AsyncMock())

    async def ack(*args, **kwargs):
        if response.done:
            raise AssertionError("double acknowledgement")
        response.done = True

    response.defer = AsyncMock(side_effect=ack)
    response.send_message = AsyncMock(side_effect=ack)
    response.edit_message = AsyncMock(side_effect=ack)
    response.is_done = lambda: response.done
    return NS(guild=guild, user=user, data={"values": list(values)}, response=response,
              followup=NS(send=AsyncMock()), edit_original_response=AsyncMock(),
              delete_original_response=AsyncMock(), message=NS(edit=AsyncMock()))


async def press(view, item, i):
    # Ejecutar exactamente la barrera y el callback usados por discord.ui.View.
    if await view.interaction_check(i):
        child = next(child for child in view.children
                     if getattr(child, "label", None) == item or getattr(child, "placeholder", None) == item)
        await child.callback(i)


class HoneypotRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.gid = 91001
        conn = b.db_connect()
        for table in ("guild_settings", "guild_honeypot_channels", "guild_honeypot_exempt",
                      "moderation_message_cache", "guild_honeypot_history", "moderation_cases"):
            # El nombre exacto de historia varía entre versiones; no se precisa borrarlo.
            if conn.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone():
                conn.execute(f'DELETE FROM "{table}" WHERE guild_id=?', (self.gid,))
        conn.close()
        self.owner = NS(id=700, guild_permissions=permissions())
        self.guild = NS(id=self.gid, owner_id=900, me=NS(id=800, top_role=50, guild_permissions=permissions()),
                        text_channels=[], voice_channels=[], stage_channels=[], threads=[], forums=[],
                        active_threads=AsyncMock(return_value=[]), create_text_channel=AsyncMock())
        self.guild.get_member = lambda uid: self.owner if uid == self.owner.id else None
        self.guild.get_role = lambda rid: None
        self.channel = MagicMock(spec=b.discord.TextChannel)
        self.channel.id, self.channel.guild, self.channel.mention = 710, self.guild, "#lab"
        self.channel.name = "honeypot"
        self.channel.permissions_for.return_value = permissions()
        self.guild.get_channel = lambda cid: self.channel if cid == self.channel.id else None
        self.guild.text_channels = [self.channel]
        b.hp_add_trap(self.gid, self.channel.id)
        b.hp_setting_set(self.gid, "honeypot_action", "log")
        b.hp_setting_set(self.gid, "honeypot_enabled", "0")
        b._hp_warning_locks.clear()
        b._hp_veteran_hits.clear()
        self.member = NS(id=720, guild=self.guild, bot=False, top_role=5, roles=[], mention="<member>",
                         guild_permissions=permissions(manage_guild=False, kick_members=False,
                             ban_members=False, manage_messages=False, moderate_members=False),
                         joined_at=datetime.now(timezone.utc)-timedelta(days=1),
                         kick=AsyncMock(), ban=AsyncMock(), timeout=AsyncMock())
        self.views = []

    def tearDown(self):
        for view in self.views:
            view.stop()

    def panel(self):
        view = b.HeraldoHoneypotSetupView(self.gid, self.owner.id)
        self.views.append(view)
        return view

    def i(self, values=(), user=None):
        return interaction(self.guild, user or self.owner, values)

    async def test_every_panel_control_rejects_other_owner_and_revoked_admin(self):
        for user in (NS(id=999, guild_permissions=permissions()), self.owner):
            if user is self.owner:
                self.owner.guild_permissions.manage_guild = False
            panel = self.panel()
            for child in panel.children:
                i = self.i(user=user)
                self.assertFalse(await panel.interaction_check(i))
                i.response.send_message.assert_awaited_once()
            self.assertFalse(panel._has_pending())

    async def test_draft_save_discard_and_toggle_are_real_callbacks(self):
        panel = self.panel()
        await press(panel, "Configurar acción (no guarda)", self.i(["kick"]))
        self.assertEqual(b.hp_action(self.gid), "log")
        await press(panel, "Configurar duración o purga (no guarda)", self.i(["kick:2880"]))
        await press(panel, "Descartar cambios", self.i())
        self.assertFalse(panel._has_pending())
        self.assertEqual(b.hp_action(self.gid), "log")
        await press(panel, "Activar / Pausar", self.i())
        await press(panel, "Activar / Pausar", self.i())
        self.assertFalse(panel._has_pending())
        await press(panel, "Configurar acción (no guarda)", self.i(["kick"]))
        await press(panel, "Configurar duración o purga (no guarda)", self.i(["kick:2880"]))
        await press(panel, "Guardar cambios", self.i())
        self.assertEqual(b.hp_action(self.gid), "kick")
        self.assertEqual(b.hp_kick_purge_minutes(self.gid), 2880)
        self.assertFalse(panel._has_pending())

    async def test_save_rechecks_permissions_and_state_after_acknowledgement(self):
        for mutate in (lambda: setattr(self.owner.guild_permissions, "manage_guild", False),
                       lambda: b.hp_setting_set(self.gid, "honeypot_action", "timeout")):
            self.owner.guild_permissions.manage_guild = True
            b.hp_setting_set(self.gid, "honeypot_action", "log")
            panel = self.panel()
            panel.pending_action = "kick"
            i = self.i()
            async def defer():
                i.response.done = True
                mutate()
            i.response.defer.side_effect = defer
            await press(panel, "Guardar cambios", i)
            self.assertNotEqual(b.hp_action(self.gid), "kick")
            self.assertEqual(panel.pending_action, "kick")

    async def test_save_ban_requires_explicit_duration_and_permissions(self):
        panel = self.panel()
        panel.pending_action = "ban"
        await press(panel, "Guardar cambios", self.i())
        self.assertEqual(b.hp_action(self.gid), "log")
        panel.pending_ban_minutes = 1440
        self.owner.guild_permissions.ban_members = False
        await press(panel, "Guardar cambios", self.i())
        self.assertEqual(b.hp_action(self.gid), "log")
        self.owner.guild_permissions.ban_members = True
        await press(panel, "Guardar cambios", self.i())
        self.assertEqual(b.hp_action(self.gid), "ban")
        self.assertEqual(b.hp_ban_override_minutes(self.gid), 1440)

    async def test_save_settings_rolls_back_partial_database_failure(self):
        conn = b.db_connect()
        conn.execute("CREATE TEMP TRIGGER fail_hp BEFORE INSERT ON guild_settings "
                     "WHEN NEW.key = 'honeypot_ban_minutes' BEGIN SELECT RAISE(ABORT, 'test'); END")
        with patch.object(b, "db_connect", return_value=conn):
            with self.assertRaises(b.sqlite3.IntegrityError):
                b.hp_save_settings(self.gid, {"honeypot_action": "ban_enabled", "honeypot_ban_minutes": "5"})
        self.assertEqual(b.hp_action(self.gid), "log")

    async def test_text_and_embed_modals_require_owner_and_current_permissions(self):
        for cls in (b.HoneypotWarningModal, b.HoneypotWarningEmbedModal):
            modal = cls(self.gid, self.owner.id)
            self.views.append(modal)
            for i in (self.i(user=NS(id=999)), self.i()):
                if i.user is self.owner:
                    self.owner.guild_permissions.manage_guild = False
                await modal.on_submit(i)
                self.assertNotIn("view", i.response.send_message.call_args.kwargs)
            self.owner.guild_permissions.manage_guild = True

    async def test_modal_stale_since_open_is_rejected_without_write(self):
        modal = b.HoneypotWarningModal(self.gid, self.owner.id)
        self.views.append(modal)
        b.hp_setting_set(self.gid, "honeypot_warning_text", "newer")
        i = self.i()
        await modal.on_submit(i)
        self.assertNotIn("view", i.response.send_message.call_args.kwargs)
        self.assertEqual(b.hp_warning_text(self.gid), "newer")

    async def test_modal_confirm_updates_original_and_removes_secondary(self):
        panel, origin = self.panel(), self.i()
        panel._origin_interaction = origin
        modal = b.HoneypotWarningModal(self.gid, self.owner.id, panel, origin)
        self.views.append(modal)
        modal.text._value = "Texto nuevo"
        i = self.i()
        await modal.on_submit(i)
        confirm = i.response.send_message.call_args.kwargs["view"]
        self.views.append(confirm)
        self.assertNotEqual(b.hp_warning_text(self.gid), "Texto nuevo")
        final = self.i()
        await press(confirm, "Confirmar y guardar", final)
        self.assertEqual(b.hp_warning_text(self.gid), "Texto nuevo")
        origin.edit_original_response.assert_awaited_once()
        final.delete_original_response.assert_awaited_once()

    async def test_edit_cancel_cannot_race_and_overwrite_confirmed_result(self):
        panel, origin = self.panel(), self.i()
        panel._origin_interaction = origin
        confirm = b.HoneypotNoticeEditConfirmView(self.gid, self.owner.id,
                       {"honeypot_warning_text": "pending"}, panel, origin)
        self.views.append(confirm)
        await press(confirm, "Cancelar", self.i())
        await press(confirm, "Confirmar y guardar", self.i())
        self.assertNotEqual(b.hp_warning_text(self.gid), "pending")
        origin.edit_original_response.assert_awaited_once()

    async def test_publish_cancel_never_publishes_and_dismisses(self):
        panel, opening = self.panel(), self.i()
        with patch.object(b, "hp_sync_all_warnings", new=AsyncMock()) as sync:
            await press(panel, "Publicar aviso", opening)
            confirm = opening.response.send_message.call_args.kwargs["view"]
            self.views.append(confirm)
            i = self.i()
            await press(confirm, "Cancelar", i)
            sync.assert_not_awaited()
            i.delete_original_response.assert_awaited_once()

    async def test_publish_revalidates_all_channels_and_updates_parent_on_partial_error(self):
        for revoked, errors in ((True, []), (False, []), (False, ["partial"])):
            panel, origin = self.panel(), self.i()
            panel._origin_interaction = origin
            confirm = b.HoneypotPublishWarningConfirmView(panel, origin)
            self.views.append(confirm)
            self.channel.permissions_for.return_value.manage_messages = not revoked
            with patch.object(b, "hp_sync_all_warnings", new=AsyncMock(return_value=errors)) as sync:
                i = self.i()
                await press(confirm, "Confirmar publicación", i)
                if revoked:
                    sync.assert_not_awaited()
                else:
                    sync.assert_awaited_once()
                    origin.edit_original_response.assert_awaited_once()
                    self.assertIn("parcial" if errors else "actualizados", panel.last_publication_status)
                i.delete_original_response.assert_awaited_once()

    async def test_publish_failed_original_refresh_reports_failure(self):
        panel, origin = self.panel(), self.i()
        origin.message.edit.side_effect = http_error()
        confirm = b.HoneypotPublishWarningConfirmView(panel, origin)
        self.views.append(confirm)
        with patch.object(b, "hp_sync_all_warnings", new=AsyncMock(return_value=[])):
            i = self.i()
            await press(confirm, "Confirmar publicación", i)
            i.followup.send.assert_awaited_once()
            origin.edit_original_response.assert_not_awaited()

    async def test_create_cancel_and_permission_revocation_do_not_create(self):
        for cancel in (True, False):
            panel = self.panel()
            confirm = b.HoneypotCreateChannelConfirmView(panel, self.i(), None)
            self.views.append(confirm)
            self.guild.me.guild_permissions.manage_channels = False
            await press(confirm, "Cancelar" if cancel else "Confirmar", self.i())
            self.guild.create_text_channel.assert_not_awaited()

    async def test_slash_confirm_revalidates_and_cancel_does_not_persist(self):
        for cancel in (True, False):
            confirm = b.HoneypotSlashConfigConfirmView(self.gid, self.owner.id, {"honeypot_enabled": "1"})
            self.views.append(confirm)
            i = self.i()
            if not cancel:
                async def defer():
                    i.response.done = True
                    self.owner.guild_permissions.manage_guild = False
                i.response.defer.side_effect = defer
            await press(confirm, "Cancelar" if cancel else "Confirmar cambios", i)
            self.assertFalse(b.honeypot_enabled(self.gid))

    async def test_two_create_confirmations_create_and_bind_only_once(self):
        b.hp_remove_trap(self.gid, self.channel.id)
        panel = self.panel()
        self.guild.text_channels = []
        self.guild.default_role = object()
        async def create(*args, **kwargs):
            await asyncio.sleep(0)
            return self.channel
        self.guild.create_text_channel.side_effect = create
        async def bind(*args, **kwargs):
            b.hp_add_trap(self.gid, self.channel.id)
            return "Canal registrado"
        views = [b.HoneypotCreateChannelConfirmView(panel, self.i(), None) for _ in range(2)]
        self.views.extend(views)
        with patch.object(b, "_setup_apply_system_channel", new=AsyncMock(side_effect=bind)), \
             patch.object(b, "hp_protected_channel_reason", return_value=None):
            await asyncio.gather(*(press(view, "Confirmar", self.i()) for view in views))
        self.guild.create_text_channel.assert_awaited_once()
        self.assertEqual(set(b.hp_traps(self.gid)), {self.channel.id})

    def warning_message(self):
        return NS(id=10001, author=NS(id=self.guild.me.id), pinned=False,
                  edit=AsyncMock(), pin=AsyncMock(), delete=AsyncMock())

    async def test_warning_pin_failure_retry_and_restart_reuse_same_message(self):
        message = self.warning_message()
        message.pin.side_effect = [http_error(), None]
        self.channel.send = AsyncMock(return_value=message)
        self.channel.fetch_message = AsyncMock(return_value=message)
        with patch.object(b, "hp_warning_embed", return_value=b.discord.Embed(title="aviso")):
            self.assertIsNotNone(await b.hp_sync_warning(self.channel))
            b._hp_warning_locks.clear()  # El recibo sobrevive al estado en memoria.
            self.assertIsNone(await b.hp_sync_warning(self.channel))
        self.channel.send.assert_awaited_once()
        message.edit.assert_awaited_once()
        self.assertEqual(b.hp_traps(self.gid)[self.channel.id], message.id)

    async def test_ambiguous_warning_send_or_database_failure_never_repeats(self):
        for save_failure in (False, True):
            b.hp_setting_set(self.gid, f"honeypot_warning_pending_{self.channel.id}", "")
            b.hp_set_warning_message(self.gid, self.channel.id, None)
            self.channel.send = AsyncMock(return_value=self.warning_message(),
                                           side_effect=None if save_failure else http_error())
            with patch.object(b, "hp_warning_embed", return_value=b.discord.Embed()), \
                 patch.object(b, "hp_set_warning_message", side_effect=RuntimeError("db")):
                self.assertIsNotNone(await b.hp_sync_warning(self.channel))
            b._hp_warning_locks.clear()
            self.assertIn("conciliación", await b.hp_sync_warning(self.channel))
            self.channel.send.assert_awaited_once()

    async def test_warning_revoked_read_permission_or_missing_channel_never_succeeds(self):
        self.channel.permissions_for.return_value.read_message_history = False
        self.assertIsNotNone(await b.hp_sync_warning(self.channel))
        self.channel.send.assert_not_called()
        self.guild.get_channel = lambda cid: None
        self.assertTrue(await b.hp_sync_all_warnings(self.guild))

    async def test_lost_warning_response_reconciles_the_message_from_discord(self):
        embed = b.discord.Embed(title="aviso", description="texto de laboratorio")
        message = self.warning_message()
        message.embeds = [embed]
        self.channel.send = AsyncMock(side_effect=http_error())
        async def history(**kwargs):
            yield message
        self.channel.history = history
        with patch.object(b, "hp_warning_embed", return_value=embed):
            self.assertIsNotNone(await b.hp_sync_warning(self.channel))
            b._hp_warning_locks.clear()
            self.assertIsNone(await b.hp_sync_warning(self.channel))
        self.channel.send.assert_awaited_once()
        message.edit.assert_awaited_once()
        message.pin.assert_awaited_once()
        self.assertEqual(b.hp_traps(self.gid)[self.channel.id], message.id)

    async def test_lost_image_warning_recovers_despite_discord_media_metadata(self):
        embed = b.discord.Embed(title="aviso", description="texto de laboratorio")
        embed.set_image(url="https://example.org/aviso.png")
        embed.set_thumbnail(url="https://example.org/miniatura.png")
        embed.set_footer(text="El Heraldo", icon_url="https://example.org/icono.png")
        received = embed.to_dict()
        for field in ("image", "thumbnail"):
            received[field] = {**received[field], "proxy_url": "https://proxy.example.org/image",
                               "width": 512, "height": 256, "content_type": "image/png",
                               "placeholder": "server-data", "flags": 0}
        received["footer"] = {**received["footer"], "proxy_icon_url": "https://proxy.example.org/icon"}
        message = self.warning_message()
        message.embeds = [b.discord.Embed.from_dict(received)]
        self.channel.send = AsyncMock(side_effect=http_error())
        async def history(**kwargs):
            yield message
        self.channel.history = history
        with patch.object(b, "hp_warning_embed", return_value=embed):
            self.assertIsNotNone(await b.hp_sync_warning(self.channel))
            b._hp_warning_locks.clear()
            self.assertIsNone(await b.hp_sync_warning(self.channel))
        self.channel.send.assert_awaited_once()
        message.edit.assert_awaited_once()
        message.pin.assert_awaited_once()
        self.assertEqual(b.hp_traps(self.gid)[self.channel.id], message.id)
        self.assertNotIn("proxy_url", embed.to_dict()["image"])

    async def test_warning_recovery_blocks_different_image_and_multiple_matches(self):
        embed = b.discord.Embed(title="aviso").set_image(url="https://example.org/aviso.png")
        for multiple in (False, True):
            b.hp_setting_set(self.gid, f"honeypot_warning_pending_{self.channel.id}", "")
            message = self.warning_message()
            other = embed.copy().set_image(url="https://example.org/otro.png")
            message.embeds = [embed if multiple else other]
            self.channel.send = AsyncMock(side_effect=http_error())
            async def history(**kwargs):
                yield message
                if multiple:
                    yield NS(id=10002, author=message.author, embeds=[embed])
            self.channel.history = history
            with patch.object(b, "hp_warning_embed", return_value=embed):
                self.assertIsNotNone(await b.hp_sync_warning(self.channel))
                b._hp_warning_locks.clear()
                self.assertIn("conciliación", await b.hp_sync_warning(self.channel))
            self.channel.send.assert_awaited_once()
            message.edit.assert_not_awaited()
            message.pin.assert_not_awaited()
            self.assertIsNone(b.hp_traps(self.gid)[self.channel.id])

    async def test_kick_and_ban_block_protected_hierarchy_and_missing_bot_permission(self):
        for action in ("kick", "ban"):
            for problem in ("owner", "exempt", "hierarchy", "permission"):
                with self.subTest(action=action, problem=problem):
                    self.member.id = self.guild.owner_id if problem == "owner" else 720
                    self.member.top_role = 50 if problem == "hierarchy" else 5
                    self.member.guild_permissions.manage_guild = problem == "exempt"
                    self.guild.me.guild_permissions.kick_members = problem != "permission"
                    self.guild.me.guild_permissions.ban_members = problem != "permission"
                    ok, _ = await b.hp_punish(self.member, action)
                    self.assertFalse(ok)
                    self.member.kick.assert_not_awaited()
                    self.member.ban.assert_not_awaited()

    async def test_kick_purges_minimum_day_after_success_without_case_history(self):
        b.hp_setting_set(self.gid, "honeypot_kick_purge_minutes", "1")
        with patch.object(b, "run_purge_job", new=AsyncMock()) as purge, \
             patch.object(b, "moderation_case_create", return_value=1) as case:
            ok, _ = await b.hp_punish(self.member, "kick")
            await asyncio.sleep(0)
            self.assertTrue(ok)
            self.member.kick.assert_awaited_once()
            self.assertTrue(purge.call_args.kwargs["honeypot"])
            age = datetime.now(timezone.utc) - purge.call_args.kwargs["after"]
            self.assertGreaterEqual(age, timedelta(days=1))
            self.assertFalse(case.call_args.kwargs["include_message_history"])

    async def test_failed_kick_does_not_purge_or_create_case(self):
        self.member.kick.side_effect = http_error()
        with patch.object(b, "run_purge_job", new=AsyncMock()) as purge, \
             patch.object(b, "moderation_case_create") as case:
            ok, _ = await b.hp_punish(self.member, "kick")
            self.assertFalse(ok)
            purge.assert_not_called()
            case.assert_not_called()

    async def test_ban_expiry_and_no_implicit_purge_or_message_history(self):
        b.hp_setting_set(self.gid, "honeypot_ban_minutes", "1440")
        ok, _ = await b.hp_punish(self.member, "ban")
        self.assertTrue(ok)
        self.assertEqual(self.member.ban.call_args.kwargs["delete_message_seconds"], 0)
        conn = b.db_connect()
        row = conn.execute("SELECT duration_minutes, expires_at, message_history FROM moderation_cases "
                           "WHERE guild_id=? AND user_id=?", (self.gid, self.member.id)).fetchone()
        conn.close()
        self.assertEqual(row[0], 1440)
        self.assertTrue(row[1])
        self.assertIn(row[2], (None, "", "[]"))

    async def test_database_failure_before_ban_blocks_the_sanction(self):
        b.hp_setting_set(self.gid, "honeypot_ban_minutes", "5")
        with patch.object(b, "moderation_case_create", side_effect=RuntimeError("db")):
            ok, _ = await b.hp_punish(self.member, "ban")
        self.assertFalse(ok)
        self.member.ban.assert_not_awaited()

    async def test_ambiguous_ban_keeps_expiry_and_blocks_duplicate_request(self):
        b.hp_setting_set(self.gid, "honeypot_ban_minutes", "5")
        self.member.ban.side_effect = http_error()
        ok, _ = await b.hp_punish(self.member, "ban")
        self.assertFalse(ok)
        self.assertTrue(b.hp_setting_get(self.gid, f"honeypot_ban_pending_{self.member.id}"))
        ok, _ = await b.hp_punish(self.member, "ban")
        self.assertFalse(ok)
        self.member.ban.assert_awaited_once()
        conn = b.db_connect()
        row = conn.execute("SELECT expires_at, open FROM moderation_cases WHERE guild_id=? AND user_id=?",
                           (self.gid, self.member.id)).fetchone()
        conn.close()
        self.assertTrue(row[0])
        self.assertEqual(row[1], 1)

    async def test_honeypot_expiry_does_not_remove_a_replacement_ban(self):
        row = {"user_id": 720, "case_number": 1}
        self.guild.fetch_ban = AsyncMock(return_value=NS(reason="Otra sanción"))
        self.guild.unban = AsyncMock()
        self.assertTrue(await b.hp_expire_ban_case(self.guild, row))
        self.guild.unban.assert_not_awaited()
        self.guild.fetch_ban.return_value.reason = "Honeypot: escribió en un canal trampa · Expediente " + b.moderation_case_code(1, self.gid)
        self.guild.unban.side_effect = http_error()
        self.assertFalse(await b.hp_expire_ban_case(self.guild, row))
        self.guild.unban.side_effect = None
        self.assertTrue(await b.hp_expire_ban_case(self.guild, row))
        self.guild.fetch_ban.side_effect = http_error(b.discord.NotFound, 404)
        self.assertTrue(await b.hp_expire_ban_case(self.guild, row))

    async def test_condemnation_privacy_exception_preserves_every_other_origin(self):
        for origin in ("honeypot", "command", "reaction", "role", "raid"):
            with self.subTest(origin=origin), \
                 patch.object(b, "condemnation_get", return_value=None), \
                 patch.object(b, "condemnation_role_id", return_value=55), \
                 patch.object(b, "condemnation_sync_roles", new=AsyncMock(return_value=(True, [], "ok"))), \
                 patch.object(b, "condemnation_archive_evidence", new=AsyncMock(return_value=("https://proof", "evidence"))) as archive, \
                 patch.object(b, "moderation_verified_proof", new=AsyncMock(return_value="proof")) as proof, \
                 patch.object(b, "moderation_case_create", return_value=1) as case, \
                 patch.object(b, "condemnation_send_dm", new=AsyncMock(return_value=True)) as dm, \
                 patch.object(b, "log_embed", new=AsyncMock()):
                ok, _ = await b._condemn_member_inner(
                    self.member, reason="test", duration_minutes=5, purge_spec=None,
                    origin=origin, applied_by=None, preserve_role_ids=[],
                    source_message_url="https://discord.com/channels/1/2/3", source_channel_id=710,
                    send_dm=True, announce=False,
                )
                self.assertTrue(ok)
                if origin == "honeypot":
                    archive.assert_not_awaited()
                    proof.assert_not_awaited()
                    self.assertIsNone(case.call_args.kwargs["proof"])
                    self.assertIsNone(dm.call_args.kwargs["source_message_url"])
                else:
                    archive.assert_awaited_once()
                    self.assertEqual(case.call_args.kwargs["proof"], "https://proof")
                self.assertEqual(case.call_args.kwargs["include_message_history"], origin != "honeypot")

    async def test_report_only_and_third_veteran_never_delete_or_sanction(self):
        message = NS(channel=self.channel, delete=AsyncMock())
        with patch.object(b, "hp_report", new=AsyncMock()), patch.object(b, "log_embed", new=AsyncMock()), \
             patch.object(b, "hp_log_trigger"), patch.object(b, "hp_punish", new=AsyncMock(return_value=(True, "ok"))) as punish:
            await b.hp_handle_trigger(message, self.member)
            message.delete.assert_not_awaited()
            self.assertEqual(punish.call_args.args[1], "log")
            punish.reset_mock()
            b.hp_setting_set(self.gid, "honeypot_action", "kick_enabled")
            self.member.joined_at = datetime.now(timezone.utc)-timedelta(days=40)
            b._hp_veteran_hits.extend([(datetime.now(timezone.utc), self.gid, 1),
                                      (datetime.now(timezone.utc), self.gid, 2),
                                      (datetime.now(timezone.utc), 91002, 3)])
            await b.hp_handle_trigger(message, self.member)
            message.delete.assert_not_awaited()
            punish.assert_not_awaited()
            self.assertTrue(b.honeypot_paused(self.gid))
            self.assertEqual(len(b._hp_veteran_hits), 1)

    async def test_honeypot_cache_is_empty_other_channel_history_is_preserved(self):
        message = NS(guild=self.guild, author=self.member, channel=self.channel, id=140,
                     content="private test text", attachments=[], created_at=datetime.now(timezone.utc))
        await b.moderation_cache_recent_messages(message)
        message.id, message.channel = 141, NS(id=999)
        await b.moderation_cache_recent_messages(message)
        conn = b.db_connect()
        rows = conn.execute("SELECT message_id FROM moderation_message_cache WHERE guild_id=?", (self.gid,)).fetchall()
        conn.close()
        self.assertEqual(rows, [(141,)])

    async def test_private_joined_threads_not_truncated_by_archive_date_order(self):
        cutoff = datetime.now(timezone.utc)-timedelta(days=1)
        threads = [NS(id=1, archive_timestamp=cutoff-timedelta(days=2)),
                   NS(id=2, archive_timestamp=cutoff+timedelta(hours=1))]
        calls = []
        async def archived(**kwargs):
            calls.append(kwargs)
            for t in threads:
                yield t
        self.channel.archived_threads = archived
        self.channel.permissions_for.return_value.manage_threads = False
        result, omitted = await b.hp_extend_purge_targets(self.guild, [], None, cutoff)
        self.assertEqual([t.id for t in result], [2])
        self.assertEqual(calls, [dict(private=True, joined=True, limit=None)])
        self.assertEqual(omitted, 0)

    async def test_purge_revalidates_author_window_guild_and_permissions(self):
        now = datetime.now(timezone.utc)
        messages = [NS(id=1, author=NS(id=720), created_at=now, guild=self.guild, channel=self.channel, delete=AsyncMock()),
                    NS(id=2, author=NS(id=721), created_at=now, guild=self.guild, channel=self.channel, delete=AsyncMock()),
                    NS(id=3, author=NS(id=720), created_at=now-timedelta(days=2), guild=self.guild, channel=self.channel, delete=AsyncMock())]
        self.channel.fetch_message = AsyncMock(side_effect=messages)
        result = await b.hp_delete_ids(self.channel, [1, 2, 3], self.gid, 720, now-timedelta(days=1), None)
        self.assertEqual(result, (1, 2))
        messages[0].delete.assert_awaited_once()
        messages[1].delete.assert_not_awaited()
        messages[2].delete.assert_not_awaited()
        self.channel.fetch_message.side_effect = [messages[0]]
        self.channel.permissions_for.return_value.manage_messages = False
        self.assertEqual(await b.hp_delete_ids(self.channel, [1], self.gid, 720, None, None), (0, 1))

    async def test_archived_thread_is_rearchived_even_when_delete_fails(self):
        thread = MagicMock(spec=b.discord.Thread)
        thread.id, thread.guild, thread.archived = 44, self.guild, True
        thread.permissions_for.return_value = permissions()
        message = NS(id=1, author=NS(id=720), guild=self.guild, channel=thread,
                     created_at=datetime.now(timezone.utc), delete=AsyncMock(side_effect=http_error()))
        thread.fetch_message = AsyncMock(return_value=message)
        async def edit(**kwargs):
            thread.archived = kwargs['archived']
            return thread
        thread.edit = AsyncMock(side_effect=edit)
        self.assertEqual(await b.hp_delete_ids(thread, [1], self.gid, 720, None, None), (0, 1))
        self.assertEqual([call.kwargs['archived'] for call in thread.edit.call_args_list], [False, True])
        self.assertTrue(thread.archived)


if __name__ == "__main__":
    unittest.main()
