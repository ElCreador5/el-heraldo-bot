"""Pruebas sobre código y payloads reales, sin la vista semántica de tests heredados."""
import asyncio
import ast
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, patch

import heraldo_i18n as i18n
from test_safety_regressions import b
from test_ux_panel_matrix import guild_fixture, sqlite_snapshot
from tools.i18n_audit import audit, findings
from heraldo_evidence import LiteralEvidence, make_evidence_embeds

ROOT = Path(__file__).resolve().parents[1]


def labels(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {'label', 'description', 'placeholder', 'title'} and isinstance(value, str):
                yield key, value
            elif isinstance(value, (dict, list)):
                yield from labels(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from labels(value)


class CatalogAndSourceTests(unittest.TestCase):
    def test_all_referenced_keys_exist_in_all_languages(self):
        report = audit()
        for locale in i18n.TARGET_LOCALES:
            missing = set(report['used_keys']) - set(i18n.CATALOGS[locale].messages)
            self.assertFalse(missing, (locale, missing))
        i18n.verify_catalogs()

    def test_new_untranslated_spanish_fails_the_gate(self):
        source = 'async def panel(interaction):\n    await interaction.response.send_message("Nueva función sin traducción.")\n'
        self.assertTrue(findings(source, 'new_module.py'))

    def test_no_unreviewed_literal_exemptions(self):
        approved = json.loads((ROOT/'locales/technical_literals.json').read_text())
        actual = audit()['literals']
        self.assertFalse([row for row in actual if row['id'] not in approved])
        self.assertFalse([row for row in approved.values() if row['reason'].startswith('PENDIENTE')])

    def test_missing_keys_and_mismatched_variables_are_rejected(self):
        with self.assertRaises(i18n.TranslationUnavailable):
            i18n.translate('en-US', 'missing.key')
        catalog = i18n.CATALOGS['pt-BR']
        altered = dict(catalog.messages)
        altered['language.current'] = '{different_variable}'
        with patch.dict(i18n.CATALOGS, {'pt-BR': i18n.Catalog('pt-BR', altered)}):
            with self.assertRaises(i18n.TranslationUnavailable):
                i18n.verify_catalogs()

    def test_no_personal_discord_locale_is_used(self):
        for file in ROOT.glob('*.py'):
            if file.name.startswith('test'):
                continue
            tree = ast.parse(file.read_text())
            self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                              and n.attr in {'locale', 'guild_locale'}
                              and isinstance(n.value, ast.Name) and n.value.id == 'interaction'], file.name)

    def test_protocol_identifiers_do_not_depend_on_translations(self):
        for file in ROOT.glob('*.py'):
            if file.name.startswith('test') or file.name == 'heraldo_i18n.py':
                continue
            for node in ast.walk(ast.parse(file.read_text())):
                if isinstance(node, ast.keyword) and node.arg in {'custom_id', 'filename'}:
                    self.assertNotIn('_t(', ast.unparse(node.value), (file.name, node.lineno))


    def test_static_discord_text_limits_in_all_locales(self):
        for file in ROOT.glob('*.py'):
            if file.name.startswith('test') or file.name == 'heraldo_i18n.py':
                continue
            tree = ast.parse(file.read_text())
            parents = {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
            for node in ast.walk(tree):
                if not isinstance(node, ast.keyword) or not isinstance(node.value, ast.Call):
                    continue
                value = node.value
                if not (isinstance(value.func, ast.Name) and value.func.id == '_t') or value.keywords:
                    continue
                owner = parents[id(node)]
                name = ast.unparse(owner.func) if isinstance(owner, ast.Call) else ''
                limit = None
                if name.endswith('TextInput'):
                    limit = {'label': 45, 'placeholder': 100}.get(node.arg)
                elif name.endswith('SelectOption'):
                    limit = {'label': 100, 'description': 100}.get(node.arg)
                elif name.endswith(('.button', '.Button')) and node.arg == 'label':
                    limit = 80
                elif 'Select' in name and node.arg == 'placeholder':
                    limit = 150
                elif node.arg == 'title':
                    cls = owner
                    while cls is not None and not isinstance(cls, ast.ClassDef):
                        cls = parents.get(id(cls))
                    if cls and any('Modal' in ast.unparse(base) for base in cls.bases):
                        limit = 45
                if limit is not None:
                    for locale in i18n.TARGET_LOCALES:
                        text = i18n.CATALOGS[locale].messages[value.args[0].value]
                        self.assertLessEqual(len(text), limit, (file.name, node.lineno, locale, text))


class GuildLanguageRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.resolver = i18n._locale_resolver
        i18n.set_locale_resolver(b.guild_language)
        self.guild = guild_fixture()
        self.guild.id = 884001
        self.other = 884002
        self.owner = 10

    def tearDown(self):
        for gid in [self.guild.id, self.other]:
            b.guild_config_set(gid, 'language', 'es-419')
        b.guild_config_set(self.guild.id, 'personality_recovery_dm_template', '')
        i18n.set_locale_resolver(self.resolver)

    def choose(self, locale):
        b.guild_config_set(self.guild.id, 'language', locale)

    def interaction(self, *, locale='es-ES'):
        return NS(guild=self.guild, guild_id=self.guild.id, locale=locale, user=NS(id=self.owner),
                  data={}, extras={}, response=NS(send_message=AsyncMock(), edit_message=AsyncMock(),
                                                 send_modal=AsyncMock(), defer=AsyncMock(), is_done=lambda: False),
                  followup=NS(send=AsyncMock()), edit_original_response=AsyncMock())

    async def test_setup_selector_uses_guild_language_and_keeps_module_ids(self):
        expected = {row[0] for row in b.HeraldoSetupView.MODULES} - {'role_connections'}
        for locale in i18n.TARGET_LOCALES:
            self.choose(locale)
            view = b.HeraldoSetupView(self.guild.id, self.owner)
            self.assertEqual({option.value for option in view.module_select.options}, expected)
            self.assertEqual(view.module_select.placeholder, i18n.translate(locale, 'setup.select_module'))
            for option in view.module_select.options:
                self.assertEqual(option.label, i18n.translate(locale, f'setup.module.{option.value}.label'))
                self.assertEqual(option.description, i18n.translate(locale, f'setup.module.{option.value}.description'))

    async def test_every_main_panel_builds_in_each_language_without_saving(self):
        for locale in i18n.TARGET_LOCALES:
            self.choose(locale)
            baseline = sqlite_snapshot()
            for option in b.HeraldoSetupView(self.guild.id, self.owner).module_select.options:
                with self.subTest(locale=locale, module=option.value):
                    interaction = self.interaction(locale='ja')
                    interaction.data = {'values': [option.value]}
                    await b.HeraldoSetupView(self.guild.id, self.owner).select_module(interaction)
                    payload = interaction.response.edit_message.call_args.kwargs
                    wire = json.loads(json.dumps(payload['view'].to_components(), ensure_ascii=False))
                    self.assertTrue(wire)
                    for kind, value in labels(wire):
                        limit = 80 if kind == 'label' else 150 if kind == 'placeholder' else 100
                        self.assertLessEqual(len(value), limit, (locale, option.value, value))
                    self.assertEqual(sqlite_snapshot(), baseline)

    async def test_language_select_and_discard_never_save(self):
        self.choose('es-419')
        view = b.HeraldoLanguageView(self.guild.id, self.owner)
        interaction = self.interaction()
        interaction.data = {'values': ['pt-BR']}
        await view.select_language(interaction)
        self.assertEqual(b.guild_language(self.guild.id), 'es-419')
        await view.discard.callback(self.interaction())
        self.assertEqual(b.guild_language(self.guild.id), 'es-419')

    async def test_stale_language_panel_uses_the_new_server_language(self):
        self.choose('es-419')
        view = b.HeraldoLanguageView(self.guild.id, self.owner)
        self.choose('pt-BR')
        interaction = self.interaction()
        interaction.data = {'values': ['en-US']}
        await view.select_language(interaction)
        payload = interaction.response.edit_message.call_args.kwargs
        self.assertEqual(payload['content'], i18n.translate('pt-BR', 'language.concurrent_change'))
        self.assertIsNone(payload['view'])
        self.assertEqual(b.guild_language(self.guild.id), 'pt-BR')

    async def test_save_is_shared_and_does_not_affect_other_servers(self):
        self.choose('es-419')
        b.guild_config_set(self.other, 'language', 'en-US')
        view = b.HeraldoLanguageView(self.guild.id, self.owner)
        view.pending = 'pt-BR'
        await view.save.callback(self.interaction())
        self.assertEqual(b.guild_language(self.guild.id), 'pt-BR')
        self.assertEqual(b.guild_language(self.other), 'en-US')
        self.assertIn(i18n.translate('pt-BR', 'language.title'), b.language_panel_text(self.guild.id))
        self.assertIn(i18n.translate('pt-BR', 'setup.select_module'),
                      json.dumps(b.HeraldoSetupView(self.guild.id, self.owner).to_components(), ensure_ascii=False))

    async def test_modal_payload_translates_class_decorators(self):
        for locale in i18n.TARGET_LOCALES:
            self.choose(locale)
            for modal in [b.HoneypotWarningModal(self.guild.id), b.AgeVerificationTimeModal(self.guild.id),
                          b.PersonalityVerificationTimeModal(self.guild.id), b.ExitCommentModal(123, self.guild.id)]:
                wire = json.loads(json.dumps(modal.to_dict(), ensure_ascii=False))
                self.assertLessEqual(len(wire['title']), 45)
                self.assertTrue(wire['components'])
                for kind, value in labels(wire):
                    self.assertLessEqual(len(value), 45 if kind in {'title', 'label'} else 100)

    async def test_automatic_dm_uses_guild_and_preserves_custom_text(self):
        for locale in ['en-US', 'pt-BR']:
            self.choose(locale)
            text = b.render_personality_recovery_dm(self.guild, 'https://example.com/invite')
            self.assertIn('https://example.com/invite', text)
            self.assertNotIn('Aviso de Verificación de personalidad', text)
            custom = 'Texto personalizado: {servidor}; {invitacion}'
            b.guild_config_set(self.guild.id, 'personality_recovery_dm_template', custom)
            self.assertEqual(b.render_personality_recovery_dm(self.guild, 'URL'),
                             f'Texto personalizado: {self.guild.name}; URL')
            b.guild_config_set(self.guild.id, 'personality_recovery_dm_template', '')

    async def test_persistent_departure_dm_retains_origin_for_its_modal(self):
        self.choose('pt-BR')
        with closing(b.db_connect()) as conn:
            b.exit_comments.init_storage(conn)
            b.exit_comments.create_pending(conn, guild_id=self.guild.id, user_id=self.owner,
                                          channel_id=123, log_message_id=70001)
            b.exit_comments.attach_dm(conn, guild_id=self.guild.id, log_message_id=70001, dm_message_id=70002)
            conn.commit()
        interaction = self.interaction()
        interaction.guild = interaction.guild_id = None
        interaction.message = NS(id=70002)
        await b.ExitCommentDMView().respond.callback(interaction)
        modal = interaction.response.send_modal.call_args.args[0]
        self.assertEqual(modal.guild_id, self.guild.id)
        self.assertEqual(str(modal.to_dict()['title']), i18n.translate('pt-BR', 'text.81fa939a59b76b'))

    async def test_context_isolated_between_concurrent_automatic_tasks(self):
        self.choose('en-US')
        b.guild_config_set(self.other, 'language', 'pt-BR')
        @i18n.guild_context
        async def render(row):
            await asyncio.sleep(0)
            return i18n.current_locale(), str(i18n.text('language.save'))
        results = await asyncio.gather(render({'guild_id': self.guild.id}), render({'guild_id': self.other}))
        self.assertEqual(results, [('en-US', 'Save changes'), ('pt-BR', 'Salvar alterações')])
        self.assertIsNone(i18n.current_guild_id())

    async def test_evidence_quotes_remain_exact_in_translated_reports(self):
        self.choose('en-US')
        quote = 'Texto del miembro, sin traducir ni reinterpretar.'
        evidence = LiteralEvidence('Member', 'Community', '#channel', datetime.now(timezone.utc), quote)
        with i18n.use_guild(self.guild.id):
            embeds = make_evidence_embeds(evidence, footer=b.LAB_FOOTER_TEXT)
        self.assertIn(quote, [field.value for field in embeds[0].fields])
        self.assertEqual(embeds[0].footer.text, "El Heraldo's Labs 🧪")
        self.assertEqual(embeds[0].title, 'El Heraldo · Evidence')
        fields = {field.name: field.value for field in embeds[0].fields}
        self.assertEqual(fields['Conduct'], 'Conduct pending review')
        self.assertEqual(fields['Outcome'], 'Report only')

    async def test_translated_form_values_keep_internal_contracts(self):
        for locale, boolean, mode, action in [('en-US', 'Yes', 'Allowlist', 'toggle'), ('pt-BR', 'Sim', 'Lista de permissões', 'alternar')]:
            self.choose(locale)
            self.assertEqual(i18n.bool_input(boolean), 'si')
            self.assertEqual(i18n.canonical_fixed(mode), 'Lista blanca')
            self.assertEqual(i18n.canonical_fixed(action), 'alternar')

    async def test_language_permissions_use_existing_access_guard(self):
        view = b.HeraldoLanguageView(self.guild.id, self.owner)
        with patch.object(b, 'configuration_access', new=AsyncMock(return_value=False)):
            self.assertFalse(await view.interaction_check(self.interaction()))
        self.assertEqual(b.guild_language(self.guild.id), 'es-419')
