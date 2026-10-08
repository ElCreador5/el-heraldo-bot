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
        edit_message=AsyncMock(), defer=AsyncMock()), followup=SimpleNamespace(send=AsyncMock()),
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


if __name__ == '__main__':
    try:
        unittest.main(verbosity=2)
    finally:
        temp.cleanup()
