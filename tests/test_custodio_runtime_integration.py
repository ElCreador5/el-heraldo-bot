"""Motor y callbacks reales, con Discord aislado y SQLite sintética."""
import asyncio
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, Mock, patch

import discord
from custodio_core import RulesSnapshot, RulesUnavailable
from custodio_detection import LocalDetector, KINDS, image_fingerprint
from custodio_policy import ObservePolicy, RuleBinding, KEY
from custodio_runtime import CustodioRuntime
from custodio_observe_setup import CustodioObserveSetupView
from custodio_setup import CustodioRulesView
from custodio_detection_setup import CustodioDetectionView
from custodio_interpretation import KEY as PLAN_KEY, InterpretationPlan, RuleInterpretation, fingerprint
from custodio_ai_runtime import analyze_rule, request_payload, validate_proposal, AIUnavailable, _last
from heraldo_evidence import LiteralEvidence, make_evidence_embeds, evidence_batches
from heraldo_i18n import set_locale_resolver, CATALOGS

SNAPSHOT = RulesSnapshot(101, ("No publicar spam ni mensajes repetidos.",), "a" * 64)


def approved_plan(snapshot=SNAPSHOT):
    rules=tuple(RuleInterpretation(n,fingerprint(text),'watchable','prohibition',('exact_text',),
        ((0,len(text)),),prohibitions=((0,len(text)),)) for n,text in enumerate(snapshot.rules,1))
    return InterpretationPlan(snapshot.guild_id,snapshot.revision,rules,1700000000).approve(999)


class DetectorTests(unittest.TestCase):
    def signal(self, detector, number, **changes):
        args = dict(guild_id=101, channel_id=202, actor_id=303,
                    message_id=number, now=float(number), content="Mensaje idéntico reiterado",
                    kinds=KINDS)
        args.update(changes)
        return detector.inspect(**args)

    def test_repeat_cross_channel_and_duplicate_delivery(self):
        d = LocalDetector()
        self.assertFalse(self.signal(d, 1, channel_id=1))
        self.assertFalse(self.signal(d, 2, channel_id=2))
        self.assertEqual({x.kind for x in self.signal(d, 3, channel_id=3)}, {"repeat", "cross_channel"})
        self.assertFalse(self.signal(d, 3, now=4))
        self.assertFalse(self.signal(d, 5, now=100))

    def test_actor_guild_and_short_conversation_do_not_trigger_repeat(self):
        d = LocalDetector()
        for n in range(1, 9):
            self.assertFalse(self.signal(d, n, actor_id=n, content="Hola"))
        self.assertFalse(self.signal(d, 9, guild_id=999))

    def test_rule_histories_and_delivery_deduplication_are_independent(self):
        detector = LocalDetector()
        self.assertFalse(self.signal(detector, 1, rule_number=1))
        self.assertFalse(self.signal(detector, 2, rule_number=1))
        self.assertFalse(self.signal(detector, 3, rule_number=2))
        self.assertIn('repeat', {d.kind for d in self.signal(detector, 3, rule_number=1)})
        self.assertFalse(self.signal(detector, 3, rule_number=1))
        self.assertEqual(len(detector.events), 4)

    def test_multiple_rules_reuse_fingerprints_without_merging_their_histories(self):
        from custodio_detection import text_sketch
        detector = LocalDetector()
        text = 'Cinco palabras diferentes para comparar mensajes de prueba'
        with patch('custodio_detection.text_sketch', wraps=text_sketch) as sketch:
            for rule in range(1, 17):
                self.assertFalse(self.signal(detector, 1, rule_number=rule, content=text))
            self.assertEqual(sketch.call_count, 1)
            self.signal(detector, 2, rule_number=1, content=text)
            self.assertEqual(sketch.call_count, 2)
        self.assertEqual(len(detector.events), 17)

    def test_similar_text_and_repeated_links_are_reportable_indicators(self):
        d = LocalDetector()
        for n in range(1, 4):
            result = self.signal(d, n, content=f"Oferta especial para todos nuestros miembros https://example.com/product {n}")
        self.assertIn("links", {x.kind for x in result})
        self.assertIn("similar_text", {x.kind for x in result})

    def test_mass_mentions_and_flood_require_thresholds(self):
        d = LocalDetector()
        self.assertFalse(self.signal(d, 1, content="Hola", mention_count=7))
        self.assertEqual(self.signal(d, 2, content="Hola", mention_count=8)[0].kind, "mentions")
        d = LocalDetector()
        for n in range(1, 9):
            result = self.signal(d, n, content=f"{n}", now=n / 2)
        self.assertEqual([x.kind for x in result], ["flood"])

    def test_advertising_is_only_an_indicator_when_bound_to_a_real_rule(self):
        for text in ['Buy now https://example.com','Compre aqui https://example.com','Oferta discord.gg/example']:
            d=LocalDetector()
            self.assertFalse(self.signal(d,1,content=text,kinds=frozenset({'repeat'})))
            self.assertEqual(self.signal(d,2,content=text,kinds=frozenset({'advertising'}))[0].kind,'advertising')
        self.assertFalse(self.signal(LocalDetector(),1,content='Documentación https://example.com',kinds=frozenset({'advertising'})))

    def test_coordinated_does_not_blame_an_actor_with_one_message(self):
        d = LocalDetector()
        for n, actor in enumerate([1, 2, 1, 2, 3, 3], 1):
            result = self.signal(d, n, actor_id=actor)
            if n < 6:
                self.assertNotIn("coordinated", {x.kind for x in result})
        self.assertIn("coordinated", {x.kind for x in result})

    def test_capacity_expiration_and_only_fingerprints(self):
        d = LocalDetector(capacity=8)
        for n in range(1, 14):
            self.signal(d, n)
        self.assertEqual(len(d.events), 8)
        self.assertNotIn("Mensaje", repr(d.events))
        d.expire(200)
        self.assertFalse(d.events)
        for bad in [float("nan"), float("inf"), -1, True]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.signal(d, 1000, now=bad)

    def test_images_are_bounded_and_solid_colors_are_not_similar_evidence(self):
        import io
        from PIL import Image
        out = io.BytesIO()
        Image.new("RGB", (12, 12), "red").save(out, format="PNG")
        digest, sketch = image_fingerprint(out.getvalue())
        self.assertEqual(len(digest), 64)
        self.assertIsNone(sketch)
        d = LocalDetector()
        for n in range(1, 4):
            result = self.signal(d, n, content="", images=((digest, sketch),))
        self.assertEqual([x.kind for x in result], ["images"])
        with self.assertRaises(ValueError):
            image_fingerprint(b"x" * (1024 * 1024 + 1))


class PolicyTests(unittest.TestCase):
    def test_revision_changes_disable_observation_and_keep_no_text(self):
        p = ObservePolicy(SNAPSHOT.revision, True, bindings=(RuleBinding(1, frozenset({"repeat"})),))
        raw = p.encode(1)
        self.assertNotIn(SNAPSHOT.rules[0], raw)
        self.assertTrue(ObservePolicy.decode(raw, SNAPSHOT).enabled)
        self.assertFalse(ObservePolicy.decode(raw, replace(SNAPSHOT, revision="b" * 64)).enabled)
        self.assertFalse(ObservePolicy.decode('{"enabled":true}', SNAPSHOT).enabled)

    def test_owner_staff_and_global_and_per_rule_exemptions(self):
        p = ObservePolicy(SNAPSHOT.revision, True, frozenset({8}), frozenset({9}),
                          (RuleBinding(1, frozenset({"repeat"}), frozenset({10}), frozenset({11})),))
        for args in [dict(owner=True), dict(staff=True), dict(role_ids={8}), dict(channel_id=9)]:
            self.assertFalse(p.eligible(**{**dict(role_ids=set(), channel_id=1), **args}))
        self.assertFalse(p.allowed_bindings(role_ids={10}, channel_id=1))
        self.assertFalse(p.allowed_bindings(role_ids=set(), channel_id=11))


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.p = ObservePolicy(SNAPSHOT.revision, True, bindings=(RuleBinding(1, frozenset({"repeat"})),))
        self.values = {PLAN_KEY:approved_plan().encode(SNAPSHOT), KEY: self.p.encode(1), "custodio_reports_channel_id": "404"}
        self.clock = [100.0]
        self.loader, self.publisher = AsyncMock(return_value=SNAPSHOT), AsyncMock(return_value="report")
        self.engine = CustodioRuntime({"guild_config_get": lambda gid,key:self.values.get(key),
             "bot": NS(intents=NS(message_content=True)), "LAB_FOOTER_TEXT":"El Heraldo's Labs 🧪"},
             clock=lambda:self.clock[0], loader=self.loader, publisher=self.publisher)
        self.engine.honeypot = Mock(return_value=False)
        guild = NS(id=101, owner_id=999, me=NS(id=99), default_role=NS(id=1), name="Lab", icon=None)
        author = Mock(spec=discord.Member)
        author.id, author.guild, author.bot, author.roles = 303, guild, False, []
        author.guild_permissions = discord.Permissions.none()
        channel = Mock(spec=discord.TextChannel)
        channel.id, channel.guild = 202, guild
        channel.is_nsfw.return_value = False
        channel.permissions_for.return_value = discord.Permissions(view_channel=True, read_message_history=True)
        self.message = NS(guild=guild, channel=channel, author=author, webhook_id=None,
                          content="Mensaje repetido deliberadamente", id=1, mentions=[], role_mentions=[],
                          mention_everyone=False, attachments=[])
        self.safe = patch("custodio_runtime._get_safe_existing", return_value=NS(guild=guild,is_nsfw=lambda:False))
        self.safe.start(); self.addCleanup(self.safe.stop)

    async def repeat(self):
        for n in range(1,4):
            self.clock[0] = 100 + n
            self.message.id = n
            await self.engine.process(self.message)

    async def test_real_message_pipeline_reports_without_any_sanction(self):
        await self.repeat()
        self.publisher.assert_awaited_once()
        args = self.publisher.call_args.kwargs
        self.assertEqual(args['rule_text'], SNAPSHOT.rules[0])
        self.assertEqual(args['rule_number'], 1)
        self.assertEqual(self.loader.await_count, 2)

    async def test_disabled_owner_staff_private_and_honeypot_are_excluded(self):
        for case in ['disabled','owner','staff','private','honeypot']:
            with self.subTest(case=case):
                self.setUp()
                if case=='disabled': self.values[KEY]=replace(self.p,enabled=False).encode(1)
                if case=='owner': self.message.author.id=999
                if case=='staff': self.message.author.guild_permissions.manage_messages=True
                if case=='private': self.message.channel.permissions_for.return_value=discord.Permissions.none()
                if case=='honeypot': self.engine.honeypot.return_value=True
                await self.repeat()
                self.publisher.assert_not_awaited()
                self.loader.assert_not_awaited()

    async def test_changed_rules_and_revoked_configuration_fail_closed_before_report(self):
        self.loader.side_effect=[SNAPSHOT, replace(SNAPSHOT, revision='b'*64)]
        await self.repeat()
        self.publisher.assert_not_awaited()

    async def test_per_rule_exempt_messages_do_not_contribute_to_another_rules_threshold(self):
        snapshot = replace(SNAPSHOT, rules=SNAPSHOT.rules + ('No saturar los canales.',))
        self.loader.return_value = snapshot
        self.values[KEY] = ObservePolicy(snapshot.revision, True, bindings=(
            RuleBinding(1, frozenset({'repeat'}), channels=frozenset({202})),
            RuleBinding(2, frozenset({'flood'})),
        )).encode(2)
        for number, channel_id in ((1, 202), (2, 202), (3, 203)):
            self.message.id = number
            self.message.channel.id = channel_id
            self.clock[0] = 100 + number
            await self.engine.process(self.message)
        self.publisher.assert_not_awaited()

    async def test_unavailable_rules_are_backed_off_and_memory_expires(self):
        self.loader.side_effect=RulesUnavailable('unavailable')
        for n in range(3):
            with self.assertRaises(RulesUnavailable): await self.engine.process(self.message)
        self.loader.assert_awaited_once()
        self.clock[0]=300
        self.engine.cleanup()
        self.assertFalse(self.engine.detector.events)


class EvidenceAndAITests(unittest.IsolatedAsyncioTestCase):
    async def test_manual_ai_adapter_runs_transport_and_validates_the_real_response_contract(self):
        proposal={'rule_number':1,'rule_quote':SNAPSHOT.rules[0],'interpretation':'Requiere aclaración humana del alcance.','needs_clarification':True}
        transport=AsyncMock(return_value={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(proposal)}}]})
        _last.pop(SNAPSHOT.guild_id,None)
        with patch.dict(os.environ,{'CUSTODIO_AI_FREE_PROVIDER':'groq','CUSTODIO_GROQ_API_KEY':'synthetic-test-key'}):
            result=await analyze_rule(SNAPSHOT,0,administrator_requested=True,transport=transport)
        self.assertEqual(result,proposal)
        transport.assert_awaited_once()
        self.assertEqual(set(json.loads(transport.call_args.args[0]['messages'][1]['content'])),{'rule_number','rule_quote'})
        _last.pop(SNAPSHOT.guild_id,None)

    async def test_long_evidence_is_complete_and_each_discord_request_fits(self):
        text='á\n\\n @everyone «texto»' * 500
        evidence=LiteralEvidence('actor','Lab','canal',datetime.now(timezone.utc),text,
                                 rule_quote='r'*2048,rule_number=1)
        embeds=make_evidence_embeds(evidence,footer="El Heraldo's Labs 🧪")
        batches=evidence_batches(embeds)
        self.assertGreater(len(batches),1)
        self.assertTrue(all(sum(len(e) for e in batch)<=6000 and len(batch)<=10 for batch in batches))
        rule_title=CATALOGS['es-419'].messages['text.6bbb7c3704b1b8']
        self.assertEqual(''.join(e.fields[-1].value for e in embeds if str(e.title)!=rule_title),text)

    async def test_ai_requires_manual_admin_request_and_configured_free_provider(self):
        transport=AsyncMock()
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(AIUnavailable):
                await analyze_rule(SNAPSHOT,0,administrator_requested=True,transport=transport)
        transport.assert_not_awaited()
        payload=request_payload(SNAPSHOT,0)
        self.assertEqual(json.loads(payload['messages'][1]['content'])['rule_quote'],SNAPSHOT.rules[0])
        self.assertNotIn('tools',payload)

    async def test_ai_proposal_is_untrusted_and_cannot_rewrite_rule_or_include_action(self):
        value={'rule_number':1,'rule_quote':SNAPSHOT.rules[0],'interpretation':'Propuesta de revisión','needs_clarification':True}
        validate_proposal(value,SNAPSHOT,0)
        for changes in [dict(rule_quote='otra norma'),dict(rule_number=True),dict(action='ban')]:
            with self.assertRaises(ValueError):validate_proposal({**value,**changes},SNAPSHOT,0)


class SetupTests(unittest.IsolatedAsyncioTestCase):
    async def test_inflight_save_keeps_its_proposal_and_navigation_until_completion(self):
        from custodio_server_rule_actions_setup import CustodioServerRuleActionsView
        for panel in (CustodioObserveSetupView, CustodioServerRuleActionsView):
            with self.subTest(panel=panel.__name__):
                values = {}
                def save(gid, old, new):
                    values.update(new)
                    return True
                parent = NS(guild_id=101, owner_id=303, get_setting=lambda gid,key:values.get(key),
                    save_atomic=Mock(side_effect=save), access_check=AsyncMock(return_value=True),
                    _sync_controls=Mock(), summary=lambda:'parent')
                view = panel(parent, SNAPSHOT)
                is_observation = panel is CustodioObserveSetupView
                if is_observation:
                    view.update(roles=frozenset({707}))
                else:
                    view.pending[0] = 'temp_ban'
                started, finish = asyncio.Event(), asyncio.Event()
                async def fetch(*args):
                    started.set()
                    await finish.wait()
                    return SNAPSHOT
                interaction = NS(guild=NS(get_role=lambda rid:NS(id=rid)),response=NS(defer=AsyncMock(),edit_message=AsyncMock()),
                                  edit_original_response=AsyncMock())
                module = 'custodio_observe_setup' if is_observation else 'custodio_source'
                with patch(module+'.load_server_rules',new=fetch):
                    task = asyncio.create_task(view.save(interaction))
                    await started.wait()
                    try:
                        if is_observation:
                            view.role_select._values = [NS(id=808)]
                            await view.select_roles(interaction)
                            self.assertEqual(view.pending.roles, {707})
                        else:
                            view.actions_select._values = ['ban']
                            await view.select_action(interaction)
                            self.assertEqual(view.pending, ['temp_ban'])
                        await view.back(interaction)
                        parent._sync_controls.assert_not_called()
                        parent.save_atomic.assert_not_called()
                    finally:
                        finish.set()
                        await task
                parent.save_atomic.assert_called_once()

    async def test_general_preference_save_is_direct_and_uses_the_opened_draft_version(self):
        from custodio_setup import CustodioSetupView
        from custodio_preferences import DEFAULTS, KEY_SENSITIVITY
        values = DEFAULTS.copy()
        def save(gid, old, new):
            if any(values.get(key) != value for key,value in old.items()):
                return False
            values.update(new)
            return True
        parent = CustodioSetupView(101, 303, get_setting=lambda gid,key:values.get(key),
            save_atomic=Mock(side_effect=save), access_check=AsyncMock(return_value=True),
            parent_factory=lambda:None)
        interaction = NS(response=NS(defer=AsyncMock()), edit_original_response=AsyncMock())
        parent.pending_sensitivity = 'strict'
        await parent.save_changes(interaction)
        self.assertEqual(values[KEY_SENSITIVITY], 'strict')
        self.assertIs(interaction.edit_original_response.call_args.kwargs['view'], parent)
        parent.save_atomic.assert_called_once()
        parent.pending_sensitivity = 'balanced'
        values[KEY_SENSITIVITY] = 'conservative'
        await parent.save_changes(interaction)
        self.assertEqual(values[KEY_SENSITIVITY], 'conservative')
        self.assertEqual(parent.pending_sensitivity, 'balanced')

    async def test_back_keeps_drafts_in_detection_exemptions_and_rule_actions(self):
        from custodio_setup import CustodioSetupView
        parent = CustodioSetupView(101, 303, get_setting=lambda gid,key:None,
            save_atomic=Mock(return_value=True), access_check=AsyncMock(return_value=True),
            parent_factory=lambda:None)
        interaction = NS(response=NS(defer=AsyncMock(), edit_message=AsyncMock()),
                         edit_original_response=AsyncMock())
        with patch('custodio_setup.load_server_rules', new=AsyncMock(return_value=SNAPSHOT)):
            for exemptions in (False, True):
                await parent.open_observation(interaction, exemptions=exemptions)
                view = interaction.edit_original_response.call_args.kwargs['view']
                view.update(roles=frozenset({707})) if exemptions else setattr(view,'pending',approved_plan().correct(0,reason='false_positive',note='Corrección sintética',administrator_id=303))
                pending = view.pending
                await view.back(interaction)
                self.assertIs(interaction.response.edit_message.call_args.kwargs['view'], parent)
                await parent.open_observation(interaction, exemptions=exemptions)
                self.assertIs(interaction.edit_original_response.call_args.kwargs['view'], view)
                self.assertEqual(view.pending, pending)
            await parent.open_rule_actions(interaction)
            actions = interaction.edit_original_response.call_args.kwargs['view']
            actions.pending[0], actions.durations[0] = 'temp_ban', 1440
            await actions.back(interaction)
            self.assertIs(interaction.response.edit_message.call_args.kwargs['view'], parent)
            await parent.open_rule_actions(interaction)
            self.assertIs(interaction.edit_original_response.call_args.kwargs['view'], actions)
            self.assertEqual((actions.pending, actions.durations), (['temp_ban'], [1440]))
        parent.save_atomic.assert_not_called()

    async def test_new_rules_do_not_reuse_an_old_rule_draft(self):
        from custodio_setup import CustodioSetupView
        parent = CustodioSetupView(101, 303, get_setting=lambda gid,key:None,
            save_atomic=Mock(), access_check=AsyncMock(return_value=True), parent_factory=lambda:None)
        interaction = NS(response=NS(defer=AsyncMock()), edit_original_response=AsyncMock())
        with patch('custodio_setup.load_server_rules', new=AsyncMock(side_effect=[SNAPSHOT, replace(SNAPSHOT, revision='b'*64)])):
            await parent.open_observation(interaction, exemptions=False)
            old = interaction.edit_original_response.call_args.kwargs['view']
            old.pending=approved_plan()
            await parent.open_observation(interaction, exemptions=False)
            current = interaction.edit_original_response.call_args.kwargs['view']
            self.assertIsNot(current, old)
            self.assertIsNone(current.pending)
        parent.save_atomic.assert_not_called()

    async def test_all_new_panels_serialize_within_limits_in_three_languages(self):
        import heraldo_i18n as i18n
        from custodio_server_rule_actions_setup import CustodioServerRuleActionsView
        from custodio_review import CustodioReviewPanel
        from custodio_discipline import ReviewedIncident
        maximum=replace(SNAPSHOT,rules=('ñ'*2048,)*16)
        policy=ObservePolicy(maximum.revision,False,frozenset(range(10**18,10**18+25)),
                              frozenset(range(10**18+50,10**18+75)),
                              tuple(RuleBinding(n,frozenset(KINDS)) for n in range(1,17)))
        parent=NS(guild_id=101,owner_id=303,get_setting=lambda gid,key:policy.encode(16) if key==KEY else None,
                  access_check=AsyncMock(return_value=True),save_atomic=Mock())
        for locale in i18n.TARGET_LOCALES:
            with patch.object(i18n,'_locale_resolver',lambda gid,locale=locale:locale),i18n.use_guild(101):
                views=[CustodioDetectionView(parent,maximum),CustodioObserveSetupView(parent,maximum,exemptions=True),
                       CustodioRulesView(parent,maximum),CustodioServerRuleActionsView(parent,maximum),
                       CustodioReviewPanel({'guild_config_get':parent.get_setting},303,maximum,
                                          ReviewedIncident(101,200,300,1,maximum.revision,'https://discord.com/channels/101/5/6'))]
                for view in views:
                    with self.subTest(locale=locale,view=type(view).__name__):
                        self.assertLessEqual(len(view.summary()),2000)
                        for row in view.to_components():
                            self.assertLessEqual(len(row['components']),5)
                            for item in row['components']:
                                if 'label' in item:self.assertLessEqual(len(str(item['label'])),80)
                                if 'placeholder' in item:self.assertLessEqual(len(str(item['placeholder'])),150)
                                for option in item.get('options',[]):
                                    self.assertLessEqual(len(str(option['label'])),100)
                                    self.assertLessEqual(len(str(option.get('description',''))),100)

    async def test_main_activate_and_pause_save_only_state_and_preserve_other_drafts(self):
        from custodio_setup import CustodioSetupView
        values={PLAN_KEY:approved_plan().encode(SNAPSHOT),
                KEY:ObservePolicy(SNAPSHOT.revision,bindings=(RuleBinding(1,frozenset({'repeat'})),)).encode(1),
                'custodio_reports_channel_id':'404'}
        def save(gid,old,new):
            if any(values.get(k)!=v for k,v in old.items()):return False
            values.update(new);return True
        parent=CustodioSetupView(101,303,get_setting=lambda gid,key:values.get(key),
                  access_check=AsyncMock(return_value=True),save_atomic=Mock(side_effect=save),parent_factory=lambda:None)
        parent.pending_sensitivity='strict'
        interaction=NS(client=NS(intents=NS(message_content=True)),guild=NS(id=101),
                       response=NS(defer=AsyncMock()),edit_original_response=AsyncMock())
        with patch('custodio_setup.load_server_rules',new=AsyncMock(return_value=SNAPSHOT)) as source,\
             patch('custodio_reports._get_safe_existing'):
            await parent.activate_observation(interaction)
            stored=ObservePolicy.decode(values[KEY],SNAPSHOT)
            self.assertTrue(stored.enabled)
            self.assertEqual(stored.bindings[0].kinds,{'repeat'})
            self.assertEqual(parent.pending_sensitivity,'strict')
            self.assertNotIn('custodio_sensitivity',values)
            source.reset_mock()
            await parent.pause_observation(interaction)
            self.assertFalse(ObservePolicy.decode(values[KEY],SNAPSHOT).enabled)
            source.assert_not_awaited()

    async def test_temp_ban_duration_is_draft_until_saved_and_discard_reads_current_saved_value(self):
        from custodio_server_rule_actions_setup import CustodioServerRuleActionsView,encode,SETTING_KEY,decode_durations
        values={SETTING_KEY:encode(SNAPSHOT,['temp_ban'],[15])}
        parent=NS(guild_id=101,owner_id=303,get_setting=lambda gid,key:values.get(key),access_check=AsyncMock(return_value=True))
        view=CustodioServerRuleActionsView(parent,SNAPSHOT)
        view.duration_select._values=['1440']
        interaction=NS(response=NS(edit_message=AsyncMock()))
        await view.select_duration(interaction)
        self.assertEqual(decode_durations(values[SETTING_KEY],SNAPSHOT),[15])
        values[SETTING_KEY]=encode(SNAPSHOT,['temp_ban'],[60])
        await view.discard(interaction)
        self.assertEqual(view.durations,[60])

    async def test_all_rule_text_is_available_and_navigation_keeps_draft(self):
        rule='Texto literal con «ñ» y \\n visible.\n'*48
        snap=replace(SNAPSHOT,rules=(rule,))
        parent=NS(guild_id=101,owner_id=303,access_check=AsyncMock(return_value=True),_sync_controls=Mock(),summary=lambda:'parent')
        view=CustodioRulesView(parent,snap)
        self.assertEqual(''.join(view.fragments()),rule)
        for n,fragment in enumerate(view.fragments()):
            view.part=n
            self.assertIn(fragment,view.summary())
            self.assertLessEqual(len(view.summary()),2000)

    async def test_exemption_selection_and_discard_never_save_and_retain_defaults(self):
        values={}
        parent=NS(guild_id=101,owner_id=303,get_setting=lambda gid,key:values.get(key),
                  access_check=AsyncMock(return_value=True),save_atomic=Mock(),_sync_controls=Mock(),summary=lambda:'parent')
        view=CustodioObserveSetupView(parent,SNAPSHOT,exemptions=True)
        view.role_select._values=[NS(id=707)]
        interaction=NS(response=NS(edit_message=AsyncMock()))
        await view.select_roles(interaction)
        self.assertEqual([v.id for v in view.role_select.default_values],[707])
        self.assertFalse(values)
        parent.save_atomic.assert_not_called()
        await view.discard(interaction)
        self.assertFalse(view.pending.roles)


if __name__=='__main__':unittest.main()
