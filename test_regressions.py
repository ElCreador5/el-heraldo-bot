"""Offline regressions; uses a disposable SQLite database and never logs into Discord."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

temp = tempfile.TemporaryDirectory()
os.environ['DB_PATH'] = str(Path(temp.name) / 'audit.db')
spec = importlib.util.spec_from_file_location('heraldo_test', Path(__file__).with_name('bot.py'))
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)
b.db_init()
b.honeypot_db_init()
b.suggestion_db_init()


def interaction(guild):
    return SimpleNamespace(guild=guild, user=SimpleNamespace(id=99, mention='<@99>'),
        data={'values': []}, response=SimpleNamespace(send_message=AsyncMock(),
        edit_message=AsyncMock(), defer=AsyncMock(), send_modal=AsyncMock()), followup=SimpleNamespace(send=AsyncMock()),
        edit_original_response=AsyncMock())


def panel():
    return {'channel_id': 10, 'message_id': 20, 'existing': True,
            'roles': [{'emoji': '👍', 'add': [1], 'remove': []},
                      {'emoji': '👎', 'add': [2], 'remove': []}],
            'allowed_roles': [], 'max_reactions': 1}


class Regressions(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.guild = MagicMock(id=777)
        self.guild.get_role.return_value = None
        self.channel = MagicMock(spec=b.discord.TextChannel)
        self.message = SimpleNamespace(id=20, guild=self.guild, jump_url='https://discord.com/test',
            add_reaction=AsyncMock(), remove_reaction=AsyncMock(), clear_reaction=AsyncMock())
        self.channel.fetch_message = AsyncMock(return_value=self.message)
        self.guild.get_channel.return_value = self.channel
        self.member = SimpleNamespace(id=99, bot=False, roles=[], add_roles=AsyncMock(),
            remove_roles=AsyncMock())
        self.guild.get_member.return_value = self.member
        self.patch = patch.object(b.bot, 'get_guild', return_value=self.guild)
        self.patch.start()
        b._rr_rejected_removals.clear()
        b.reaction_role_panels_save(777, [])

    async def asyncTearDown(self):
        self.patch.stop()

    async def test_message_template_requires_explicit_save(self):
        b.heraldo_template_save(777, [])
        item = {"name": "Reglas", "title": "Reglas", "description": "Contenido",
                "image": "", "button_label": "", "button_url": "",
                "role_component": "", "role_component_mode": "ninguno"}
        view = b.HeraldoMessageConfirmView(
            777, 99, "template", {"old_name": None, "item": item})
        self.assertEqual(b.heraldo_template_list(777), [])
        i = interaction(self.guild)
        i.guild_id = 777
        await view.commit.callback(i)
        self.assertEqual(len(b.heraldo_template_list(777)), 1)
        self.assertEqual(b.heraldo_template_list(777)[0]["name"], "Reglas")

    async def test_message_confirmation_cancel_keeps_configuration(self):
        b.heraldo_template_save(777, [])
        view = b.HeraldoMessageConfirmView(777, 99, "template",
                 {"old_name": None, "item": {"name": "Sin guardar"}})
        i = interaction(self.guild)
        i.guild_id = 777
        await view.cancel.callback(i)
        self.assertEqual(b.heraldo_template_list(777), [])
        i.response.edit_message.assert_awaited_once()

    async def test_message_kit_conflict_does_not_overwrite_existing(self):
        old = {"name": "Reglas", "title": "Original", "description": "Texto"}
        b.heraldo_template_save(777, [old])
        view = b.HeraldoMessageConfirmView(777, 99, "kit",
            {"items": [{"name": "Reglas", "title": "Reemplazo"}]})
        i = interaction(self.guild)
        i.guild_id = 777
        await view.commit.callback(i)
        self.assertEqual(b.heraldo_template_list(777)[0]["title"], "Original")
        i.response.send_message.assert_awaited_once()

    async def test_message_confirm_rejects_other_admin_session(self):
        b.heraldo_template_save(777, [])
        view = b.HeraldoMessageConfirmView(777, 99, "template",
            {"old_name": None, "item": {"name": "Ajeno"}})
        i = interaction(self.guild)
        i.guild_id = 777
        i.user.id = 100
        self.assertFalse(await view.interaction_check(i))
        self.assertEqual(b.heraldo_template_list(777), [])

    async def test_orientation_check_does_not_duplicate_age_verification_log(self):
        role = SimpleNamespace(id=321)
        member = SimpleNamespace(id=99, mention="<@99>", roles=[role])
        self.guild.get_member.return_value = member
        with patch.object(b, 'get_eval_role_ids', return_value={321}), \\
             patch.object(b, 'hp_punish_role_id', return_value=0), \\
             patch.object(b, 'condemnation_get', return_value=None), \\
             patch.object(b, 'db_clear_tentado') as clear, \\
             patch.object(b, 'log_embed', new=AsyncMock()) as log:
            status = await b.evaluate_member(777, 99, report=True)
        self.assertEqual(status, "verificado")
        clear.assert_called_once_with(777, 99)
        log.assert_not_awaited()

    async def test_raid_setup_read_and_write(self):
        i = interaction(self.guild)
        await b.raid_config.callback(i)
        i.response.send_message.assert_awaited_once()
        with patch.object(b, 'log_embed', new=AsyncMock()):
            await b.raid_config.callback(i, ingresos=17)
        self.assertEqual(b.raid_threshold(777), 17)

    async def test_startup_layouts_and_serialization(self):
        self.assertEqual(b.validate_setup_view_layouts(777), [])
        for count in (0, 1, 20):
            p = panel()
            p['roles'] = [{'emoji': str(n), 'add': [], 'remove': []} for n in range(count)]
            view = b.HeraldoReactionRolesEditorView(777, 99, p, selected=19)
            rows = view.to_components()
            self.assertLessEqual(len(rows), 5)
            for row in rows:
                self.assertLessEqual(len(row['components']), 5)
                for component in row['components']:
                    self.assertLessEqual(len(component.get('options', [])), 25)
            json.dumps(rows)
            view.stop()

    async def test_editor_state_isolation(self):
        p = panel()
        a = b.HeraldoReactionRolesEditorView(777, 99, p)
        c = b.HeraldoReactionRolesEditorView(777, 99, p)
        a.panel['roles'][0]['add'].append(9)
        self.assertEqual(p['roles'][0]['add'], [1])
        self.assertEqual(c.panel['roles'][0]['add'], [1])

    async def test_database_restart_and_guild_isolation(self):
        b.guild_resource_set(777, 'role', 'old', 123)
        b.guild_resource_set(777, 'role', 'new', 123)
        b.guild_resource_set(888, 'role', 'old', 123)
        b.db_init()
        b.honeypot_db_init()
        b.suggestion_db_init()
        self.assertIsNone(b.guild_resource_get(777, 'role', 'old'))
        self.assertEqual(b.guild_resource_get(777, 'role', 'new'), 123)
        self.assertEqual(b.guild_resource_get(888, 'role', 'old'), 123)

    async def test_command_registration_payloads(self):
        commands = b.bot.tree.get_commands()
        self.assertLessEqual(len(commands), 100)
        self.assertEqual(len(commands), len({c.name for c in commands}))
        def check(data):
            self.assertLessEqual(len(data['name']), 32)
            self.assertLessEqual(len(data.get('description', '')), 100)
            self.assertLessEqual(len(data.get('options', [])), 25)
            for option in data.get('options', []):
                check(option)
        for command in commands:
            check(command.to_dict(b.bot.tree))

    async def test_save_keeps_active_reaction(self):
        view = b.HeraldoReactionRolesEditorView(777, 99, panel(), selected=1)
        i = interaction(self.guild)
        with patch.object(b, 'rr_valid_role', return_value=True):
            await view.save.callback(i)
        result = i.edit_original_response.call_args.kwargs
        self.assertEqual(result['view'].selected, 1)
        self.assertIn('👎 (2/2)', result['content'])

    async def test_create_role_for_active_reaction_and_cache_delay(self):
        for action in ('add', 'remove'):
            with self.subTest(action=action):
                role = b.discord.Role(guild=self.guild, state=MagicMock(), data={
                    'id': '333', 'name': 'Prueba', 'permissions': '0', 'position': 1,
                    'color': 0, 'hoist': False, 'managed': False, 'mentionable': False})
                self.guild.create_role = AsyncMock(return_value=role)
                view = b.HeraldoReactionRolesEditorView(777, 99, panel(), selected=1)
                modal = b.HeraldoReactionRoleCreateModal(view, action)
                modal.role_name._value = ' Prueba '
                i = interaction(self.guild)
                i.user.guild_permissions = b.discord.Permissions(manage_roles=True)
                await modal.on_submit(i)
                args = self.guild.create_role.call_args.kwargs
                self.assertEqual(args['name'], 'Prueba')
                self.assertEqual(args['permissions'].value, 0)
                self.assertFalse(args['mentionable'])
                result = i.edit_original_response.call_args.kwargs
                updated = result['view']
                self.assertEqual(updated.selected, 1)
                self.assertIn(333, updated.panel['roles'][1][action])
                self.assertNotIn(333, updated.panel['roles'][0][action])
                selector = next(c for c in updated.children if c.row == (1 if action == 'add' else 2))
                self.assertIn(333, [r.id for r in selector.default_values])
                self.assertIsNone(b.reaction_role_panel_find(777, 20))
                await modal.on_submit(i)
                self.guild.create_role.assert_awaited_once()

    async def test_create_role_guards(self):
        for case in ('wrong_owner', 'missing_user_permission', 'missing_bot_permission', 'empty_name', 'limit'):
            with self.subTest(case=case):
                p = panel()
                if case == 'limit':
                    p['roles'][0]['add'] = list(range(10))
                self.guild.me.guild_permissions.manage_roles = case != 'missing_bot_permission'
                self.guild.create_role = AsyncMock()
                view = b.HeraldoReactionRolesEditorView(777, 99, p)
                modal = b.HeraldoReactionRoleCreateModal(view, 'add')
                modal.role_name._value = ' ' if case == 'empty_name' else 'Prueba'
                i = interaction(self.guild)
                i.user.guild_permissions = b.discord.Permissions(manage_roles=case != 'missing_user_permission')
                if case == 'wrong_owner':
                    i.user.id = 12
                await modal.on_submit(i)
                self.guild.create_role.assert_not_awaited()
                i.response.send_message.assert_awaited_once()

    async def test_create_role_discord_error_preserves_draft(self):
        view = b.HeraldoReactionRolesEditorView(777, 99, panel())
        modal = b.HeraldoReactionRoleCreateModal(view, 'add')
        modal.role_name._value = 'Prueba'
        self.guild.create_role = AsyncMock(side_effect=b.discord.Forbidden(
            SimpleNamespace(status=403, reason='forbidden'), 'forbidden'))
        i = interaction(self.guild)
        i.user.guild_permissions = b.discord.Permissions(manage_roles=True)
        await modal.on_submit(i)
        i.followup.send.assert_awaited_once()
        self.assertEqual(view.panel['roles'][0]['add'], [1])
        self.assertFalse(modal.submitting)

    async def test_creation_menu_opens_modal_for_selected_reaction(self):
        view = b.HeraldoReactionRolesEditorView(777, 99, panel(), selected=1)
        i = interaction(self.guild)
        i.data['values'] = ['create_remove']
        await view.select_emoji(i)
        modal = i.response.send_modal.call_args.args[0]
        self.assertEqual(modal.action, 'remove')
        self.assertEqual(modal.editor.selected, 1)

    async def test_modal_updates_original_message(self):
        for cls, values in (
            (b.HeraldoReactionEmojiModal, {'emoji': '🔥'}),
            (b.HeraldoReactionOptionsModal, {'maximum': '2', 'mode': 'Todos', 'reverse_mode': 'No'}),
            (b.HeraldoReactionMessageModal, {'heading': 'Title', 'description': 'Description'}),
        ):
            with self.subTest(modal=cls.__name__):
                view = b.HeraldoReactionRolesEditorView(777, 99, panel(), selected=1)
                modal = cls(view)
                for name, value in values.items():
                    getattr(modal, name)._value = value
                i = interaction(self.guild)
                await modal.on_submit(i)
                i.response.edit_message.assert_awaited_once()
                i.response.send_message.assert_not_awaited()

    async def test_conflicting_role_actions_rejected(self):
        p = panel()
        p['roles'][0]['remove'] = [1]
        view = b.HeraldoReactionRolesEditorView(777, 99, p)
        i = interaction(self.guild)
        with patch.object(b, 'rr_valid_role', return_value=True):
            await view.save.callback(i)
        i.response.defer.assert_not_awaited()
        i.response.send_message.assert_awaited_once()

    async def test_deleted_message_can_be_unregistered(self):
        b.rr_panel_upsert(777, panel())
        error = b.discord.NotFound(SimpleNamespace(status=404, reason='missing'), 'missing')
        self.channel.fetch_message.side_effect = error
        modal = b.HeraldoReactionDeleteModal(777, 20)
        modal.confirmation._value = 'ELIMINAR'
        i = interaction(self.guild)
        await modal.on_submit(i)
        self.assertIsNone(b.reaction_role_panel_find(777, 20))
        i.response.defer.assert_awaited_once()
        i.edit_original_response.assert_awaited_once()

    async def test_rejected_reaction_removal_does_not_change_roles(self):
        await b.rr_reject_reaction(self.message, '👍', self.member)
        payload = SimpleNamespace(guild_id=777, message_id=20, channel_id=10,
            user_id=99, member=self.member, emoji='👍')
        with patch.object(b, 'reaction_role_panel_find', side_effect=AssertionError('must ignore removal')):
            await b.rr_handle_reaction(payload, False)
        self.member.add_roles.assert_not_awaited()
        self.member.remove_roles.assert_not_awaited()

    async def test_maximum_rejects_then_ignores_automatic_removal(self):
        b.rr_panel_upsert(777, panel())
        async def users():
            yield self.member
        self.message.reactions = [SimpleNamespace(emoji=e, users=users) for e in ('👍', '👎')]
        payload = SimpleNamespace(guild_id=777, message_id=20, channel_id=10,
            user_id=99, member=self.member, emoji='👎')
        await b.rr_handle_reaction(payload, True)
        self.message.remove_reaction.assert_awaited_once()
        await b.rr_handle_reaction(payload, False)
        self.member.add_roles.assert_not_awaited()
        self.member.remove_roles.assert_not_awaited()

    async def test_failed_rejection_does_not_ignore_future_removal(self):
        self.message.remove_reaction.side_effect = b.discord.Forbidden(
            SimpleNamespace(status=403, reason='forbidden'), 'forbidden')
        with self.assertRaises(b.discord.Forbidden):
            await b.rr_reject_reaction(self.message, '👍', self.member)
        self.assertEqual(b._rr_rejected_removals, {})

    async def test_reaction_add_remove_and_reverse(self):
        role = MagicMock(id=1)
        role.is_assignable.return_value = True
        self.guild.get_role.return_value = role
        for reverse in (False, True):
            for added in (False, True):
                with self.subTest(reverse=reverse, added=added):
                    p = panel()
                    p.update(max_reactions=0, reversed=reverse)
                    b.rr_panel_upsert(777, p)
                    do_add = added != reverse
                    self.member.roles = [] if do_add else [role]
                    self.member.add_roles.reset_mock()
                    self.member.remove_roles.reset_mock()
                    payload = SimpleNamespace(guild_id=777, message_id=20, channel_id=10,
                        user_id=99, member=self.member, emoji='👍')
                    await b.rr_handle_reaction(payload, added)
                    if do_add:
                        self.member.add_roles.assert_awaited_once()
                        self.member.remove_roles.assert_not_awaited()
                    else:
                        self.member.remove_roles.assert_awaited_once()
                        self.member.add_roles.assert_not_awaited()


    async def test_join_inline_creation_preserves_draft_and_cache_miss(self):
        for cls, kind in ((b.HeraldoJoinRolesBasicView, 'basic'), (b.HeraldoJoinRolesBotsView, 'bots'), (b.HeraldoJoinRolesUsersView, 'users')):
            with self.subTest(kind=kind):
                view = cls(777, 99)
                if kind == 'users':
                    view.selected_user_id = 99
                    view.selected_role_ids = [12]
                else:
                    view.pending_role_ids = [12]
                    view.pending_enabled = True
                i = interaction(self.guild)
                i.user.guild_permissions = b.discord.Permissions(manage_roles=True)
                self.guild.me.guild_permissions = b.discord.Permissions(manage_roles=True)
                self.guild.create_role = AsyncMock(return_value=SimpleNamespace(id=12345, mention='<@&12345>'))
                modal = b.JoinRolesCreateRoleModal(view, kind)
                modal.role_name._value = 'Nuevo'
                await modal.on_submit(i)
                ids = view.selected_role_ids if kind == 'users' else view.pending_role_ids
                self.assertEqual(ids, [12, 12345])
                if kind != 'users': self.assertTrue(view.pending_enabled)
                selector = next(c for c in view.children if isinstance(c, b.discord.ui.RoleSelect))
                self.assertEqual([v.id for v in selector.default_values], ids)
                self.assertEqual(self.guild.create_role.call_args.kwargs['permissions'].value, 0)
                i.response.defer.assert_awaited_once()
                await modal.on_submit(i)
                self.guild.create_role.assert_awaited_once()

    async def test_join_creation_denied_does_not_create(self):
        view = b.HeraldoJoinRolesBasicView(777, 99)
        modal = b.JoinRolesCreateRoleModal(view, 'basic')
        modal.role_name._value = 'Nuevo'
        self.guild.create_role = AsyncMock()
        await modal.on_submit(interaction(self.guild))
        self.guild.create_role.assert_not_awaited()

    async def test_join_discard_resets_visual_and_user_draft(self):
        b.set_join_role_ids(777, [10])
        view = b.HeraldoJoinRolesBasicView(777, 99)
        view.pending_role_ids = [20]
        b.join_role_selector_defaults(view, [20])
        await view.discard_changes.callback(interaction(self.guild))
        selector = next(c for c in view.children if isinstance(c, b.discord.ui.RoleSelect))
        self.assertEqual([v.id for v in selector.default_values], [10])
        users = b.HeraldoJoinRolesUsersView(777, 99)
        users.selected_user_id, users.selected_role_ids = 99, [20]
        await users.discard_changes.callback(interaction(self.guild))
        self.assertIsNone(users.selected_user_id)
        self.assertEqual(users.selected_role_ids, [])

    async def test_reports_summary_uses_draft_and_discard_resets_channel(self):
        b.set_moderation_report_channel_id(777, 10)
        view = b.HeraldoUserReportsSetupView(777, 99)
        view.pending_channel_id = 20
        view.pending_reactions = [{'emoji': '🧪', 'label': 'Borrador visible', 'action': 'report', 'threshold': 2}]
        view._rebuild_reaction_select()
        self.assertIn('Borrador visible', view._content(self.guild))
        self.assertNotIn('solo notifican', view._content(self.guild))
        await view.discard_changes.callback(interaction(self.guild))
        self.assertEqual(view.channel_select.default_values[0].id, 10)
        self.assertNotIn('Borrador visible', view._content(self.guild))

    async def test_rr_events_are_serial_and_locks_cleaned(self):
        import asyncio
        current = 0
        peak = 0
        async def handler(payload, added):
            nonlocal current, peak
            current += 1
            peak = max(peak, current)
            await asyncio.sleep(0)
            current -= 1
        payload = SimpleNamespace(guild_id=777, message_id=20, user_id=99)
        with patch.object(b, '_rr_handle_reaction_serial', side_effect=handler):
            await asyncio.gather(b.rr_handle_reaction(payload, True), b.rr_handle_reaction(payload, False))
        self.assertEqual(peak, 1)
        self.assertEqual(b._rr_event_locks, {})


    async def test_join_delay_is_draft_until_save(self):
        b.guild_config_set(777, 'join_roles_delay_seconds', '0')
        view = b.HeraldoJoinRolesBasicView(777, 99)
        modal = b.JoinRolesDelayModal(777, view)
        modal.delay._value = '15'
        await modal.on_submit(interaction(self.guild))
        self.assertEqual(b.get_join_roles_delay(777), 0)
        self.assertEqual(view.pending_delay, 15)
        await view.save_changes.callback(interaction(self.guild))
        self.assertEqual(b.get_join_roles_delay(777), 15)
        self.assertIsNone(view.pending_delay)

    async def test_join_creation_limit_and_http_failure_preserve_draft(self):
        view = b.HeraldoJoinRolesBasicView(777, 99)
        view.pending_role_ids = list(range(1, 26))
        i = interaction(self.guild)
        i.user.guild_permissions = b.discord.Permissions(manage_roles=True)
        self.guild.me.guild_permissions = b.discord.Permissions(manage_roles=True)
        self.guild.create_role = AsyncMock(side_effect=b.discord.Forbidden(SimpleNamespace(status=403, reason='denied'), 'denied'))
        modal = b.JoinRolesCreateRoleModal(view, 'basic')
        modal.role_name._value = 'Test'
        await modal.on_submit(i)
        self.guild.create_role.assert_not_awaited()
        view.pending_role_ids = [123]
        await modal.on_submit(i)
        self.assertEqual(view.pending_role_ids, [123])
        self.assertFalse(modal.submitting)
        i.followup.send.assert_awaited_once()

    async def test_simultaneous_reactions_keep_one_under_limit(self):
        import asyncio
        b.rr_panel_upsert(777, panel())
        async def users():
            yield self.member
        self.message.reactions = [SimpleNamespace(emoji=e, users=users) for e in ('👍', '👎')]
        role = MagicMock(id=2)
        role.is_assignable.return_value = True
        self.guild.get_role.return_value = role
        payloads = [SimpleNamespace(guild_id=777, message_id=20, channel_id=10, user_id=99, member=self.member, emoji=e) for e in ('👍', '👎')]
        await asyncio.gather(*(b.rr_handle_reaction(p, True) for p in payloads))
        self.message.remove_reaction.assert_awaited_once()
        self.member.add_roles.assert_awaited_once()


if __name__ == '__main__':
    try:
        unittest.main(verbosity=2)
    finally:
        temp.cleanup()
