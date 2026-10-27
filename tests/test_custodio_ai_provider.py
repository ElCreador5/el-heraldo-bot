"""Contrato HTTP con fragmentos reales simulados; nunca usa credenciales reales."""
import asyncio
from contextlib import redirect_stdout
from dataclasses import replace
import io
import json
import os
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, patch

import custodio_ai_runtime as ai
from custodio_core import RulesSnapshot
from tools.custodio_ai_health import check

RULE = 'No repetir mensajes que saturen los canales.'
SNAPSHOT = RulesSnapshot(123456, (RULE,), 'a' * 64)
PROPOSAL = {'rule_number': 1, 'rule_quote': RULE, 'interpretation': 'Observación de repetición.',
            'needs_clarification': False}
ENV = {'CUSTODIO_AI_FREE_PROVIDER': 'groq', 'CUSTODIO_GROQ_API_KEY': 'synthetic-secret'}


def completion(proposal=PROPOSAL, finish='stop'):
    return {'choices': [{'finish_reason': finish, 'message': {'content': json.dumps(proposal)}}]}


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, ENV, clear=True)
        self.env.start(); self.addCleanup(self.env.stop)
        ai._last.clear(); ai._busy.clear()

    def session(self, body, status=200):
        async def chunks(_size):
            for index in range(0, len(body), 7):
                yield body[index:index + 7]
        response = NS(status=status, content=NS(iter_chunked=chunks))
        class Session:
            requests = []
            def __init__(self, **kwargs): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            def post(self, url, **kwargs):
                self.requests.append((url, kwargs))
                class Context:
                    async def __aenter__(self): return response
                    async def __aexit__(self, *args): pass
                return Context()
        return Session

    async def test_fragmented_http_body_and_multibyte_quote_are_validated_in_full(self):
        long_rule = ('Regla auténtica: no inundar canales. ' * 50)[:2048]
        snap = replace(SNAPSHOT, rules=(long_rule,))
        proposal = {**PROPOSAL, 'rule_quote': long_rule}
        session = self.session(json.dumps(completion(proposal), ensure_ascii=False).encode())
        with patch.object(ai.aiohttp, 'ClientSession', session):
            result = await ai.analyze_rule(snap, 0, administrator_requested=True)
        self.assertEqual(result, proposal)
        self.assertEqual(len(session.requests), 1)
        url, request = session.requests[0]
        self.assertEqual(url, ai.ENDPOINT)
        self.assertIs(request['allow_redirects'], False)

    async def test_long_rule_budget_and_strict_schema_replace_retired_model(self):
        payload = ai.request_payload(replace(SNAPSHOT, rules=('ñ' * 2048,)), 0)
        self.assertEqual(payload['model'], 'openai/gpt-oss-20b')
        self.assertGreaterEqual(payload['max_completion_tokens'], 2048)
        self.assertLessEqual(payload['max_completion_tokens'], 4096)
        self.assertIs(payload['response_format']['json_schema']['strict'], True)
        self.assertFalse(payload['response_format']['json_schema']['schema']['additionalProperties'])
        self.assertNotIn('tools', payload)

    async def test_incomplete_or_refused_completion_never_becomes_a_proposal(self):
        for reason in ['length', 'content_filter', 'tool_calls', None]:
            with self.subTest(reason=reason), self.assertRaisesRegex(ai.AIUnavailable, 'incomplete_response'):
                await ai.request_completion(ai.request_payload(SNAPSHOT, 0),
                                            transport=AsyncMock(return_value=completion(finish=reason)))

    async def test_provider_errors_are_bounded_and_never_echo_response_or_secret(self):
        for status, reason in [(400, 'invalid_request'), (401, 'invalid_api_key'),
                               (403, 'invalid_api_key'), (429, 'rate_limited'),
                               (500, 'provider_unavailable'), (302, 'provider_unavailable')]:
            session = self.session(b'synthetic-secret private provider response', status)
            with self.subTest(status=status), patch.object(ai.aiohttp, 'ClientSession', session):
                with self.assertLogs(ai.log, level='WARNING') as captured:
                    with self.assertRaisesRegex(ai.AIUnavailable, reason):
                        await ai.request_completion(ai.request_payload(SNAPSHOT, 0))
                self.assertNotIn('synthetic-secret', str(captured.output))
                self.assertNotIn('private provider response', str(captured.output))
                self.assertEqual(len(session.requests), 1)

    async def test_oversized_and_malformed_response_fail_closed(self):
        for body in [b'x' * (ai.MAX_RESPONSE_BYTES + 1), b'{broken']:
            with self.subTest(size=len(body)), patch.object(ai.aiohttp, 'ClientSession', self.session(body)):
                with self.assertRaises(ai.AIUnavailable):
                    await ai.request_completion(ai.request_payload(SNAPSHOT, 0))

    async def test_timeout_releases_manual_request_lock_and_is_not_retried(self):
        transport = AsyncMock(side_effect=asyncio.TimeoutError)
        with self.assertRaisesRegex(ai.AIUnavailable, 'provider_unavailable'):
            await ai.analyze_rule(SNAPSHOT, 0, administrator_requested=True, transport=transport)
        self.assertNotIn(SNAPSHOT.guild_id, ai._busy)
        transport.assert_awaited_once()

    async def test_wrong_quote_and_extra_action_are_rejected_even_with_valid_json(self):
        for proposal in [{**PROPOSAL, 'rule_quote': 'Otra regla'}, {**PROPOSAL, 'action': 'ban'}]:
            ai._last.clear()
            with self.assertRaisesRegex(ai.AIUnavailable, 'invalid_response'):
                await ai.analyze_rule(SNAPSHOT, 0, administrator_requested=True,
                                      transport=AsyncMock(return_value=completion(proposal)))

    async def test_health_probe_emits_only_metadata_and_does_not_claim_success_on_failure(self):
        for side_effect, expected in [(None, 'REAL_INFERENCE_VALIDATED'),
                                      (ai.AIUnavailable('invalid_api_key'), 'UNAVAILABLE')]:
            buffer = io.StringIO()
            with patch('tools.custodio_ai_health.analyze_rule',
                       new=AsyncMock(return_value=PROPOSAL, side_effect=side_effect)), redirect_stdout(buffer):
                code = await check()
            output = buffer.getvalue()
            self.assertEqual(code, 0 if side_effect is None else 1)
            self.assertIn(expected, output)
            self.assertNotIn(RULE, output)
            self.assertNotIn(PROPOSAL['interpretation'], output)
            self.assertNotIn('synthetic-secret', output)
