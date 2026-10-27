"""Pruebas aisladas del lector real de Server Rules, sin credenciales ni red."""
import unittest
import json
from types import SimpleNamespace as NS
from unittest.mock import patch

from custodio_core import RulesUnavailable
from custodio_source import load_server_rules


class CustodioSourceTests(unittest.IsolatedAsyncioTestCase):
    def session(self,bodies):
        class Body:
            def __init__(self,raw):self.raw=raw
            async def iter_chunked(self,size):
                for start in range(0,len(self.raw),7):yield self.raw[start:start+7]
            async def read(self,*args):raise AssertionError('single read can return a partial body')
        class Response:
            status=200
            def __init__(self,raw):self.content=Body(raw)
            async def __aenter__(self):return self
            async def __aexit__(self,*args):return False
        class Session:
            def __init__(self,*args,**kwargs):self.calls=[]
            async def __aenter__(self):return self
            async def __aexit__(self,*args):return False
            def get(self,url,**kwargs):
                self.calls.append((url,kwargs))
                return Response(bodies[len(self.calls)-1])
        return Session

    async def test_real_http_adapter_accumulates_complete_fragmented_multibyte_rules(self):
        rule='No repetir mensajes. «ñ» '+ 'Texto legítimo. '*70
        bodies=[json.dumps({'features':['MEMBER_VERIFICATION_GATE_ENABLED'],'ignored':'x'*12000}).encode(),
                json.dumps({'form_fields':[{'field_type':'TERMS','values':[rule]}]},ensure_ascii=False).encode()]
        with patch('custodio_source.aiohttp.ClientSession',self.session(bodies)):
            result=await load_server_rules(1234,'synthetic-secret')
        self.assertEqual(result.rules,(rule,))

    async def test_real_http_adapter_rejects_oversized_or_broken_body_before_interpreting_rules(self):
        for raw,reason in [(b'x'*65537,'api_response_too_large'),(b'{broken','invalid_api_json')]:
            with patch('custodio_source.aiohttp.ClientSession',self.session([raw])):
                with self.assertRaises(RulesUnavailable) as error:
                    await load_server_rules(1234,'synthetic-secret')
            self.assertEqual(error.exception.reason,reason)

    async def test_reads_official_terms_through_exactly_two_get_paths(self):
        paths = []
        async def fake_read(path):
            paths.append(path)
            if path.endswith("/member-verification"):
                return 200, {"form_fields": [
                    {"field_type": "TERMS", "values": ["Norma primera", "Norma segunda"]},
                    {"field_type": "TEXT_INPUT", "values": ["No debe entrar"]},
                ]}
            return 200, {"features": ["COMMUNITY", "MEMBER_VERIFICATION_GATE_ENABLED"]}
        result = await load_server_rules(1234, "fake-test-token", fetcher=fake_read)
        self.assertEqual(result.rules, ("Norma primera", "Norma segunda"))
        self.assertEqual(paths, [
            "/guilds/1234",
            "/guilds/1234/member-verification",
        ])

    async def test_screening_disabled_must_not_request_rules(self):
        paths = []
        async def fake_read(path):
            paths.append(path)
            return 200, {"features": ["COMMUNITY"]}
        with self.assertRaises(RulesUnavailable) as ctx:
            await load_server_rules(1234, "fake-test-token", fetcher=fake_read)
        self.assertEqual(ctx.exception.reason, "screening_disabled_or_unknown")
        self.assertEqual(paths, ["/guilds/1234"])

    async def test_blocked_endpoint_is_not_treated_as_empty_rules(self):
        async def fake_read(path):
            if path.endswith("/member-verification"):
                return 403, {}
            return 200, {"features": ["MEMBER_VERIFICATION_GATE_ENABLED"]}
        with self.assertRaises(RulesUnavailable) as ctx:
            await load_server_rules(1234, "fake-test-token", fetcher=fake_read)
        self.assertEqual(ctx.exception.reason, "verification_unavailable")
        self.assertEqual(ctx.exception.http_status, 403)

    async def test_unavailable_guild_prevents_second_request(self):
        paths = []
        async def fake_read(path):
            paths.append(path)
            return 503, {}
        with self.assertRaises(RulesUnavailable) as ctx:
            await load_server_rules(1234, "fake-test-token", fetcher=fake_read)
        self.assertEqual(ctx.exception.http_status, 503)
        self.assertEqual(len(paths), 1)

    async def test_missing_credentials_and_invalid_guild_are_rejected(self):
        async def fake_read(path):
            raise AssertionError("network should not be reached")
        for guild, token in ((0, "fake-test-token"), (1234, ""), (True, "fake-test-token")):
            with self.subTest(guild=guild, token=bool(token)), self.assertRaises(ValueError):
                await load_server_rules(guild, token, fetcher=fake_read)


if __name__ == "__main__":
    unittest.main()
