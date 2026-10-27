"""La sonda nunca confunde un saludo, respuesta inválida o entorno ajeno con inferencia válida."""
from dataclasses import replace
import json
import os
import unittest
from unittest.mock import AsyncMock,patch
from tools import custodio_analysis_health as health
from test_custodio_runtime_integration import SNAPSHOT,approved_plan


class AnalysisHealthTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.snap=replace(SNAPSHOT,guild_id=int(health.GUILD_ID))
        self.loader=AsyncMock(return_value=self.snap)
        self.context=AsyncMock(return_value=({},set()))
        self.env=patch.dict(os.environ,{'RAILWAY_PROJECT_ID':health.PROJECT,
            'RAILWAY_ENVIRONMENT_ID':health.ENVIRONMENT,'DISCORD_TOKEN':'synthetic-secret'},clear=True)
        self.env.start();self.addCleanup(self.env.stop)

    async def test_lab_guard_precedes_all_network_calls(self):
        with patch.dict(os.environ,{'RAILWAY_PROJECT_ID':'unrelated'}):
            result,success=await health.probe(loader=self.loader)
        self.assertFalse(success);self.assertEqual(result['status'],'LAB_ONLY_GUARD')
        self.loader.assert_not_awaited()

    async def test_valid_real_contract_reports_only_metadata_and_never_saves(self):
        async def analyzer(snap,**kwargs):
            self.assertTrue(kwargs['administrator_requested'])
            await kwargs['budget'].take(1,10**20)
            return approved_plan(snap)
        with patch.object(health.BUDGET,'take',new=AsyncMock()):
            result,success=await health.probe(loader=self.loader,context_loader=self.context,analyzer=analyzer)
        self.assertTrue(success);self.assertEqual(result['requests_reserved'],1)
        self.assertFalse(result['saved']);self.assertFalse(result['enabled_changed']);self.assertFalse(result['discord_interactive'])
        serialized=json.dumps(result)
        self.assertNotIn(self.snap.rules[0],serialized);self.assertNotIn('synthetic-secret',serialized)

    async def test_greeting_without_provider_or_invalid_proposal_cannot_claim_success(self):
        for invalid in (False,True):
            async def analyzer(snap,**kwargs):
                plan=approved_plan(snap)
                if invalid:
                    await kwargs['budget'].take(1,10**20)
                    return replace(plan,rules=(replace(plan.rules[0],status='clarification',limitations=('invalid_interpretation',)),))
                return replace(plan,rules=(replace(plan.rules[0],status='no_prohibition'),))
            with patch.object(health.BUDGET,'take',new=AsyncMock()):
                result,success=await health.probe(loader=self.loader,context_loader=self.context,analyzer=analyzer)
            self.assertFalse(success)

    async def test_foreign_snapshot_and_external_error_do_not_expose_sensitive_details(self):
        for loader in (AsyncMock(return_value=SNAPSHOT),AsyncMock(side_effect=ValueError('synthetic-secret'))):
            result,success=await health.probe(loader=loader,context_loader=self.context)
            self.assertFalse(success);self.assertNotIn('synthetic-secret',json.dumps(result))
        self.context.assert_not_awaited()
