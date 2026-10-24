import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import unittest
from datetime import datetime, timezone
from zipfile import ZipFile

import supabase_backup as cloud

spec = importlib.util.spec_from_file_location('external',
    Path(__file__).resolve().parents[1] / 'tools/issue23_verify_external.py')
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
external = importlib.util.module_from_spec(spec)
spec.loader.exec_module(external)


class ExternalMemoryTests(unittest.TestCase):
    def fixture(self):
        connection = sqlite3.connect(':memory:')
        connection.execute('CREATE TABLE sample(id INTEGER PRIMARY KEY, value TEXT)')
        connection.execute("INSERT INTO sample(value) VALUES('synthetic')")
        connection.commit()
        info = external.inspect_memory(connection)
        database = connection.serialize(); connection.close()
        manifest = {k: v for k, v in info.items() if k != 'content'}
        manifest.update(environment='heraldo-test', revision='a' * 40, result='verified',
                        size=len(database), sha256=hashlib.sha256(database).hexdigest(),
                        created_at=datetime.now(timezone.utc).isoformat())
        stream = io.BytesIO()
        with ZipFile(stream, 'w') as archive:
            archive.writestr('database.sqlite', database)
            archive.writestr('manifest.json', json.dumps(manifest))
        key, nonce = os.urandom(32), os.urandom(12)
        blob = cloud.PREFIX + nonce + cloud.AESGCM(key).encrypt(nonce, stream.getvalue(), cloud.AAD)
        return key, blob, manifest

    def test_download_restores_in_isolation_without_plaintext_file(self):
        key, blob, manifest = self.fixture()
        self.assertEqual(external.restore_in_memory(blob, key, 'heraldo-test', 'a' * 40, cloud), manifest)

    def test_wrong_key_and_tampering_rejected(self):
        key, blob, _ = self.fixture()
        for data, secret in ((blob, os.urandom(32)),
                             (blob[:-1] + bytes([blob[-1] ^ 1]), key)):
            with self.assertRaises(cloud.InvalidTag):
                external.restore_in_memory(data, secret, 'heraldo-test', 'a' * 40, cloud)

    def test_wrong_environment_or_revision_rejected(self):
        key, blob, _ = self.fixture()
        for env, revision in (('heraldo-production', 'a' * 40), ('heraldo-test', 'b' * 40)):
            with self.assertRaises(ValueError):
                external.restore_in_memory(blob, key, env, revision, cloud)


if __name__ == '__main__':
    unittest.main()
