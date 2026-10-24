import base64
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from zipfile import ZipFile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

spec = importlib.util.spec_from_file_location('handoff',
    Path(__file__).resolve().parents[1] / 'tools/issue23_key_handoff.py')
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)


class KeyHandoffTests(unittest.TestCase):
    def fixture(self, environment='heraldo-production'):
        key = os.urandom(32)
        database = b'synthetic test data'
        manifest = dict(environment=environment, result='verified',
                        sha256=hashlib.sha256(database).hexdigest())
        stream = io.BytesIO()
        with ZipFile(stream, 'w') as archive:
            archive.writestr('database.sqlite', database)
            archive.writestr('manifest.json', json.dumps(manifest))
        t = SimpleNamespace(PREFIX=b'fixture:', AAD=b'fixture', AESGCM=AESGCM)
        nonce = os.urandom(12)
        blob = t.PREFIX + nonce + AESGCM(key).encrypt(nonce, stream.getvalue(), t.AAD)
        return key, [('synthetic-object', blob)], t

    def test_only_authenticated_production_key_accepted(self):
        key, candidates, t = self.fixture()
        result = handoff.authenticate_key(base64.urlsafe_b64encode(key), candidates, t)
        self.assertEqual(result[:2], (key, 'synthetic-object'))
        self.assertEqual(result[2], hashlib.sha256(candidates[0][1]).hexdigest())

    def test_wrong_key_rejected(self):
        _, candidates, t = self.fixture()
        with self.assertRaises(ValueError):
            handoff.authenticate_key(base64.urlsafe_b64encode(os.urandom(32)), candidates, t)

    def test_tampering_rejected(self):
        key, candidates, t = self.fixture()
        blob = candidates[0][1]
        with self.assertRaises(ValueError):
            handoff.authenticate_key(base64.urlsafe_b64encode(key),
                                     [('synthetic-object', blob[:-1] + bytes([blob[-1] ^ 1]))], t)

    def test_test_key_cannot_be_mistaken_for_production(self):
        key, candidates, t = self.fixture('heraldo-test')
        with self.assertRaises(ValueError):
            handoff.authenticate_key(base64.urlsafe_b64encode(key), candidates, t)

    @unittest.skipUnless(os.name == 'nt', 'Windows DPAPI only')
    def test_dpapi_roundtrip_and_ciphertext_does_not_contain_plaintext(self):
        key = os.urandom(32)
        protected = handoff.dpapi(key)
        self.assertNotIn(key, protected)
        root = handoff.encrypted_temp()
        path = root / 'synthetic-key.dpapi'
        path.write_bytes(protected)
        self.assertEqual(handoff.dpapi(path.read_bytes(), decrypt=True), key)


if __name__ == '__main__':
    unittest.main()
