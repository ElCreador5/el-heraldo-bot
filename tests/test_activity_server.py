import unittest
from pathlib import Path
import activity_server

class TestActivityFiles(unittest.TestCase):
    def test_page_contains_carl_sections(self):
        html = (activity_server.ROOT / "index.html").read_text(encoding="utf-8")
        for section in ("Canal", "Mensaje", "Mostrar editor de embed", "Fecha",
                        "Rol para mencionar", "Repetir cada", "Crear mensaje"):
            self.assertIn(section, html)

    def test_sdk_uses_mapped_same_origin(self):
        js = (activity_server.ROOT / "main.js").read_text(encoding="utf-8")
        self.assertIn("import('/sdk/@discord/embedded-app-sdk@2.5.0')", js)
        self.assertNotIn("import('https://esm.sh/", js)

    def test_no_browser_bot_secrets(self):
        for path in ("main.js", "index.html"):
            content = (activity_server.ROOT / path).read_text(encoding="utf-8")
            self.assertNotIn("DISCORD_TOKEN", content)
            self.assertNotIn("DISCORD_ACTIVITY_CLIENT_SECRET", content)

    def test_pkce_supported_and_no_secret_required(self):
        js = (activity_server.ROOT / "main.js").read_text(encoding="utf-8")
        self.assertIn("crypto.getRandomValues(new Uint8Array(48))", js)
        self.assertIn("crypto.subtle.digest('SHA-256'", js)
        self.assertIn("code_challenge:pkce.challenge", js)
        self.assertIn("code_challenge_method:'S256'", js)
        self.assertIn("code_verifier:pkce.verifier", js)
        self.assertNotIn("DISCORD_ACTIVITY_CLIENT_SECRET", activity_server.__file__)
        self.assertTrue(activity_server.valid_code_verifier("a" * 43))
        self.assertFalse(activity_server.valid_code_verifier("a" * 42))
        self.assertFalse(activity_server.valid_code_verifier("a" * 129))
        self.assertFalse(activity_server.valid_code_verifier("e" * 42 + " "))
        self.assertFalse(activity_server.valid_code_verifier(None))

    def test_assets_exist(self):
        for name in ("style.css", "main.js"):
            self.assertTrue((activity_server.ROOT / name).exists())

if __name__ == "__main__":
    unittest.main()

class TestPkceEndpoint(unittest.IsolatedAsyncioTestCase):
    async def test_token_exchange_excludes_client_secret(self):
        from types import SimpleNamespace
        class Response:
            status = 200
            async def json(self):
                return {"access_token": "mock_access", "expires_in": 3600}
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return False
        class Session:
            def __init__(self):
                self.data = None
            def post(self, url, data):
                self.data = data
                return Response()
        session = Session()
        bot = SimpleNamespace(application_id=123456, user=None)
        class Request:
            headers = {}
            host = "worker-lab.up.railway.app"
            app = {"bot": bot, "session": session}
            async def json(self):
                return {"code": "sample-code", "code_verifier": "v" * 64}
        result = await activity_server.oauth(Request())
        self.assertEqual(result.status, 200)
        self.assertEqual(session.data["client_id"], "123456")
        self.assertEqual(session.data["code_verifier"], "v" * 64)
        self.assertEqual(session.data["redirect_uri"], "https://127.0.0.1")
        self.assertNotIn("client_secret", session.data)

    async def test_bad_verifier_rejected_without_discord_call(self):
        from types import SimpleNamespace
        class Request:
            headers = {}
            host = "worker-lab.up.railway.app"
            app = {"bot": SimpleNamespace(application_id=123, user=None),
                   "session": None}
            async def json(self):
                return {"code": "sample-code", "code_verifier": "abc"}
        result = await activity_server.oauth(Request())
        self.assertEqual(result.status, 400)
