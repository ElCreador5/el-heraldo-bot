"""Recorridos ejecutables del planificador, permisos y los tres idiomas; sin Discord real."""
import asyncio
from dataclasses import replace
import json
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, Mock, patch
import discord
import heraldo_i18n as i18n
from custodio_setup import CustodioSetupView
from custodio_detection_setup import (CustodioDetectionView,CustodioInterpretationView,
    CustodioCorrectionView,CustodioCorrectionModal)
from custodio_observe_setup import CustodioObserveSetupView
from custodio_interpretation import KEY as PLAN_KEY, InterpretationPlan
from custodio_policy import KEY, ObservePolicy
from test_custodio_runtime_integration import SNAPSHOT,approved_plan
import test_custodio_runtime_integration as runtime_fixtures


class PlannerUITests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.values={}
        def save(gid,old,new):
            if any(self.values.get(key)!=value for key,value in old.items()):
                return False
            self.values.update(new);return True
        self.parent=CustodioSetupView(101,303,get_setting=lambda gid,key:self.values.get(key),
            save_atomic=Mock(side_effect=save),access_check=AsyncMock(return_value=True),parent_factory=lambda:None)
        self.interaction=NS(guild_id=101,guild=NS(id=101,owner_id=999,text_channels=[],roles=[],
            get_role=lambda rid:NS(id=rid)),user=NS(id=303,guild_permissions=discord.Permissions(administrator=True)),
            locale="es-419",client=NS(intents=NS(message_content=True)),
            response=NS(defer=AsyncMock(),edit_message=AsyncMock(),send_modal=AsyncMock()),
            edit_original_response=AsyncMock())
        self.source=patch('custodio_detection_setup.load_server_rules',new=AsyncMock(return_value=SNAPSHOT))
        self.source.start();self.addCleanup(self.source.stop)

    async def test_analysis_callback_acknowledges_before_provider_and_never_saves(self):
        view=CustodioDetectionView(self.parent,SNAPSHOT)
        async def analyze(*args,**kwargs):
            self.interaction.response.defer.assert_awaited_once()
            self.assertTrue(view.busy)
            self.assertTrue(all(child.disabled for child in view.children))
            return replace(approved_plan(),approved_by=0)
        with patch('custodio_detection_setup.analyze_snapshot',new=AsyncMock(side_effect=analyze)) as provider:
            await view.analyze(self.interaction)
        self.assertTrue(provider.call_args.kwargs['administrator_requested'])
        self.assertTrue(view.pending.rules[0].kinds)
        self.assertFalse(self.values)
        self.parent.save_atomic.assert_not_called()
        self.assertFalse(view.save_button.disabled)

    async def test_save_derives_detectors_without_manual_mapping_and_remains_paused(self):
        view=CustodioDetectionView(self.parent,SNAPSHOT);view.pending=replace(approved_plan(),approved_by=0)
        await view.save(self.interaction)
        self.assertEqual(ObservePolicy.decode(self.values[KEY],SNAPSHOT).bindings[0].kinds,{'repeat'})
        self.assertFalse(ObservePolicy.decode(self.values[KEY],SNAPSHOT).enabled)
        self.assertEqual(InterpretationPlan.decode(self.values[PLAN_KEY],SNAPSHOT).approved_by,303)
        self.assertEqual(set(self.parent.save_atomic.call_args.args[2]),{KEY,PLAN_KEY})
        self.assertTrue(view.save_button.disabled)

    async def test_save_correction_preserves_global_state_and_all_manual_exemptions(self):
        policy=ObservePolicy.empty(SNAPSHOT)
        policy=replace(policy,enabled=True,roles=frozenset({707}),channels=frozenset({808}),
            bindings=(replace(policy.bindings[0],roles=frozenset({909}),kinds=frozenset({'repeat'})),))
        self.values.update({KEY:policy.encode(1),PLAN_KEY:approved_plan().encode(SNAPSHOT)})
        view=CustodioDetectionView(self.parent,SNAPSHOT)
        view.pending=view.saved.correct(0,reason='allowed',note='Nota propia sin traducción.',administrator_id=303)
        await view.save(self.interaction)
        current=ObservePolicy.decode(self.values[KEY],SNAPSHOT)
        self.assertTrue(current.enabled)
        self.assertEqual((current.roles,current.channels,current.bindings[0].roles),({707},{808},{909}))
        self.assertFalse(current.bindings[0].kinds)
        self.assertEqual(view.saved.rules[0].clarification,'Nota propia sin traducción.')

    async def test_concurrent_configuration_and_changed_rules_block_save_without_overwrite(self):
        for stale in ('policy','plan','rules'):
            self.values.clear();self.parent.save_atomic.reset_mock()
            view=CustodioDetectionView(self.parent,SNAPSHOT);view.pending=approved_plan()
            if stale=='policy':self.values[KEY]='another saved draft'
            if stale=='plan':self.values[PLAN_KEY]='another saved plan'
            source=replace(SNAPSHOT,revision='b'*64) if stale=='rules' else SNAPSHOT
            with patch('custodio_detection_setup.load_server_rules',new=AsyncMock(return_value=source)):
                await view.save(self.interaction)
            self.parent.save_atomic.assert_not_called()

    async def test_reanalysis_save_and_correction_require_current_administrator(self):
        view=CustodioDetectionView(self.parent,SNAPSHOT);view.pending=approved_plan()
        self.interaction.user.guild_permissions=discord.Permissions(manage_guild=True)
        with patch('custodio_detection_setup.analyze_snapshot',new=AsyncMock()) as provider:
            await view.analyze(self.interaction);await view.save(self.interaction)
        provider.assert_not_awaited();self.parent.save_atomic.assert_not_called()
        correction=CustodioCorrectionView(CustodioInterpretationView(view));correction.reason='disable'
        await correction.apply(self.interaction)
        self.assertEqual(view.pending,approved_plan())

    async def test_correction_modal_and_navigation_only_change_the_draft_then_discard_restores(self):
        self.values[PLAN_KEY]=approved_plan().encode(SNAPSHOT)
        detection=CustodioDetectionView(self.parent,SNAPSHOT)
        detail=CustodioInterpretationView(detection);correction=CustodioCorrectionView(detail)
        await correction.edit_note(self.interaction)
        modal=self.interaction.response.send_modal.call_args.args[0]
        modal.note_input._value='Excepción administrativa propia.'
        await modal.on_submit(self.interaction)
        correction.selector._values=['false_positive'];await correction.choose(self.interaction)
        await correction.apply(self.interaction)
        self.assertFalse(detection.pending.rules[0].kinds)
        self.assertTrue(detection.saved.rules[0].kinds)
        await detail.back(self.interaction)
        self.assertIs(self.interaction.response.edit_message.call_args.kwargs['view'],detection)
        await detection.discard(self.interaction)
        self.assertEqual(detection.pending,detection.saved)
        self.parent.save_atomic.assert_not_called()

    async def test_busy_analysis_blocks_navigation_and_parallel_save(self):
        view=CustodioDetectionView(self.parent,SNAPSHOT)
        started,finish=asyncio.Event(),asyncio.Event()
        async def analyze(*args,**kwargs):
            started.set();await finish.wait();return approved_plan()
        with patch('custodio_detection_setup.analyze_snapshot',new=analyze):
            task=asyncio.create_task(view.analyze(self.interaction));await started.wait()
            try:
                await view.back(self.interaction);await view.discard(self.interaction);await view.save(self.interaction)
                self.parent.save_atomic.assert_not_called()
                self.assertTrue(view.busy)
            finally:
                finish.set();await task

    async def test_panels_components_modal_and_full_rule_use_server_language(self):
        for locale in i18n.TARGET_LOCALES:
            with patch.object(i18n,'_locale_resolver',lambda gid:locale),i18n.use_guild(101):
                detection=CustodioDetectionView(self.parent,SNAPSHOT);detection.pending=approved_plan()
                detail=CustodioInterpretationView(detection)
                correction=CustodioCorrectionView(detail)
                exemptions=CustodioObserveSetupView(self.parent,SNAPSHOT,exemptions=True)
                self.assertIn(i18n.CATALOGS[locale].messages['text.custodio.analysis.review'],
                              [str(child.label) for child in detection.children])
                self.assertNotIn(i18n.CATALOGS[locale].messages['text.custodio.activate'],
                              [str(child.label) for child in detection.children])
                self.assertFalse(hasattr(detection,'kind_select'))
                self.assertFalse(hasattr(exemptions,'kind_select'))
                self.assertEqual(str(CustodioCorrectionModal(correction).title),
                                 i18n.CATALOGS[locale].messages['text.custodio.correction.note'])
                self.assertIn(SNAPSHOT.rules[0],''.join(detail.fragments()))
                for view in (detection,detail,correction,exemptions):
                    self.assertLessEqual(len(view.summary()),2000)
                    for row in view.to_components():
                        self.assertLessEqual(len(row['components']),5)
                        for child in row['components']:
                            for option in child.get('options',[]):
                                self.assertLessEqual(len(str(option['description'])),100)

    async def test_long_rule_and_admin_note_are_fully_available_in_paged_review(self):
        source='No spam. '+('Texto original ñ.\n'*100)
        snapshot=replace(SNAPSHOT,rules=(source,))
        detection=CustodioDetectionView(self.parent,snapshot)
        detection.pending=approved_plan(snapshot).correct(0,reason='disable',note='A'*1000,administrator_id=303)
        detail=CustodioInterpretationView(detection)
        all_text=''.join(detail.fragments())
        self.assertIn(source,all_text);self.assertIn('A'*1000,all_text)
        self.assertGreater(len(detail.fragments()),1)
        for part in range(len(detail.fragments())):
            detail.part=part;self.assertLessEqual(len(detail.summary()),2000)

    async def test_legacy_detector_configuration_cannot_activate_without_an_approved_plan(self):
        self.values.update({KEY:replace(ObservePolicy.empty(SNAPSHOT),bindings=(replace(
            ObservePolicy.empty(SNAPSHOT).bindings[0],kinds=frozenset({'repeat'})),)).encode(1),
            'custodio_reports_channel_id':'404'})
        with patch('custodio_setup.load_server_rules',new=AsyncMock(return_value=SNAPSHOT)):
            await self.parent.activate_observation(self.interaction)
        self.parent.save_atomic.assert_not_called()
        self.assertFalse(ObservePolicy.decode(self.values[KEY],SNAPSHOT).enabled)


class ApprovedRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        runtime_fixtures.RuntimeTests.setUp(self)

    async def repeat(self):
        return await runtime_fixtures.RuntimeTests.repeat(self)

    async def test_legacy_policy_and_unapproved_plan_never_inspect_content(self):
        for value in (None,replace(approved_plan(),approved_by=0).encode(SNAPSHOT)):
            self.values[PLAN_KEY]=value
            with patch.object(self.engine.detector,'inspect') as inspect:
                await self.repeat()
            inspect.assert_not_called()
        self.publisher.assert_not_awaited()

    async def test_report_guard_rechecks_pause_plan_roles_and_destination_after_detection(self):
        await self.repeat()
        guard=self.publisher.call_args.kwargs['authorization_check']
        self.assertTrue(await guard())
        self.values[KEY]=replace(self.p,enabled=False).encode(1)
        self.assertFalse(await guard())
        self.values[KEY]=self.p.encode(1)
        previous=self.values[PLAN_KEY];self.values[PLAN_KEY]=None
        self.assertFalse(await guard());self.values[PLAN_KEY]=previous
        self.message.author.guild_permissions.manage_messages=True
        self.assertFalse(await guard());self.message.author.guild_permissions.manage_messages=False
        self.values['custodio_reports_channel_id']='405'
        self.assertFalse(await guard())

    async def test_rule_scope_excludes_allowed_channel_before_local_inspection(self):
        from test_custodio_interpretation import proposal
        from custodio_interpretation import validate_rule
        snap=replace(SNAPSHOT,rules=('Spam solo en <#202>.',))
        value=proposal(snap,normative='restriction',permissions=[snap.rules[0]],scope='outside_allowed_channels')
        rule=validate_rule(value,snap,0,channels={202:'permitido'})
        self.loader.return_value=snap
        self.values[PLAN_KEY]=replace(approved_plan(snap),rules=(rule,)).encode(snap)
        with patch.object(self.engine.detector,'inspect') as inspect:
            await self.repeat()
        inspect.assert_not_called();self.publisher.assert_not_awaited()

    async def test_normal_reply_mentions_are_not_counted_as_explicit_targeted_pings(self):
        from test_custodio_interpretation import proposal
        from custodio_interpretation import validate_rule
        snap=replace(SNAPSHOT,rules=('No hacer menciones insistentes.',))
        rule=validate_rule(proposal(snap,category='directed_mentions'),snap,0)
        self.loader.return_value=snap
        self.values[PLAN_KEY]=replace(approved_plan(snap),rules=(rule,)).encode(snap)
        self.values[KEY]=replace(self.p,bindings=(replace(self.p.bindings[0],kinds=rule.kinds),)).encode(1)
        self.message.mentions=[NS(id=777)]
        for number in range(1,7):
            self.message.id=number;self.clock[0]=100+number
            self.message.content=f'Una respuesta normal en la conversación {number}'
            await self.engine.process(self.message)
        self.publisher.assert_not_awaited()
        for number in range(7,13):
            self.message.id=number;self.clock[0]=100+number
            self.message.content=f'<@777> ping explícito {number}'
            await self.engine.process(self.message)
        self.publisher.assert_awaited_once()


if __name__=='__main__':unittest.main()
