"""Comprobar el payload real enviado a Discord, con IDs y valores intactos."""
import asyncio
import copy
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, patch

import heraldo_command_i18n as commands
import heraldo_i18n as i18n
from test_safety_regressions import b
import test_i18n_runtime as runtime

ROOT = Path(__file__).resolve().parents[1]


def actual_payload():
    return [command.to_dict(b.bot.tree) for command in b.bot.tree.get_commands()]


def without_presentation(payload):
    result = copy.deepcopy(payload)
    for node, field, _ in commands.metadata_fields(result):
        node[field] = '<display>'
        node.pop(field + '_localizations', None)
    return result


class CommandSchemaTests(unittest.IsolatedAsyncioTestCase):
    async def test_every_registered_command_description_and_choice_uses_its_catalog_key(self):
        registry = json.loads((ROOT/'locales/command_schema.json').read_text())
        original = actual_payload()
        snapshot = json.dumps(original, ensure_ascii=False)
        fields = list(commands.metadata_fields(original))
        self.assertEqual({path for _, _, path in fields}, set(registry))
        for locale in i18n.TARGET_LOCALES:
            localized = commands.localize_schema(original, locale)
            self.assertEqual(without_presentation(localized), without_presentation(original))
            for node, field, path in commands.metadata_fields(localized):
                self.assertEqual(node[field], i18n.CATALOGS[locale].messages[registry[path]['key']])
                self.assertTrue(1 <= len(node[field]) <= 100, (locale, path))
        self.assertEqual(json.dumps(original, ensure_ascii=False), snapshot)

    async def test_new_or_changed_command_text_fails_coverage(self):
        for change in ['new_command', 'changed_description', 'changed_choice']:
            payload = actual_payload()
            if change == 'new_command':
                payload.append({'name': 'nuevo', 'description': 'Nueva función sin traducir', 'type': 1})
            elif change == 'changed_description':
                payload[0]['description'] = 'Descripción nueva sin clave'
            else:
                node, field, _ = next(row for row in commands.metadata_fields(payload) if row[1] == 'name')
                node[field] = 'Nueva opción'
            with self.assertRaises(i18n.TranslationUnavailable, msg=change):
                commands.localize_schema(payload, 'pt-BR')

    async def test_http_sync_is_isolated_per_guild_and_never_changes_global_commands(self):
        original = actual_payload()
        send, global_send = AsyncMock(return_value=[]), AsyncMock()
        http = NS(bulk_upsert_guild_commands=send, bulk_upsert_global_commands=global_send)
        commands.install(http, {10: 'en-US', 20: 'pt-BR'}.__getitem__)
        await asyncio.gather(http.bulk_upsert_guild_commands(1, 10, payload=original),
                             http.bulk_upsert_guild_commands(1, 20, payload=original))
        for call in send.await_args_list:
            guild_id = call.args[1]
            expected = commands.localize_schema(original, {10: 'en-US', 20: 'pt-BR'}[guild_id])
            self.assertEqual(call.kwargs['payload'], expected)
        global_send.assert_not_awaited()
        self.assertIs(http.bulk_upsert_global_commands, global_send)


class CommandLanguageSaveTests(unittest.IsolatedAsyncioTestCase):
    setUp = runtime.GuildLanguageRuntimeTests.setUp
    tearDown = runtime.GuildLanguageRuntimeTests.tearDown
    choose = runtime.GuildLanguageRuntimeTests.choose
    interaction = runtime.GuildLanguageRuntimeTests.interaction

    async def test_language_selection_never_synchronizes_commands_or_saves(self):
        self.choose('es-419')
        view = b.HeraldoLanguageView(self.guild.id, self.owner)
        interaction = self.interaction(locale='pt-BR')
        interaction.data = {'values': ['en-US']}
        with patch.object(b.bot.tree, 'sync', new=AsyncMock()) as sync:
            await view.select_language(interaction)
        sync.assert_not_awaited()
        self.assertEqual(b.guild_language(self.guild.id), 'es-419')

    async def test_save_syncs_only_the_origin_guild_and_can_retry_in_the_same_panel(self):
        self.choose('es-419')
        b.guild_config_set(self.other, 'language', 'pt-BR')
        view = b.HeraldoLanguageView(self.guild.id, self.owner)
        view.pending = 'en-US'
        interaction = self.interaction()
        with patch.object(b.bot, 'is_ready', return_value=True), \
             patch.object(b.bot.tree, 'sync', new=AsyncMock(side_effect=RuntimeError('synthetic'))) as sync:
            await view.save.callback(interaction)
            sync.assert_awaited_once_with(guild=self.guild)
            self.assertEqual(b.guild_language(self.guild.id), 'en-US')
            self.assertEqual(b.guild_language(self.other), 'pt-BR')
            self.assertIn(i18n.translate('en-US', 'language.command_sync_pending'),
                          interaction.edit_original_response.call_args.kwargs['content'])
            interaction.followup.send.assert_not_awaited()
            fresh = b.HeraldoLanguageView(self.guild.id, self.owner)
            sync.side_effect = None
            sync.return_value = []
            await fresh.save.callback(self.interaction())
            self.assertEqual(sync.await_count, 2)
