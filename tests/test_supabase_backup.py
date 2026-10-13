"""Regresiones offline: sin red, tokens reales ni datos de miembros."""
import base64
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import supabase_backup as cloud
from sqlite_recovery import create_backup


class CloudBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        database = root / "source.db"
        with sqlite3.connect(database) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE private_values (id INTEGER PRIMARY KEY, secret TEXT)")
            conn.execute("INSERT INTO private_values VALUES (1, 'texto-confidencial')")
            conn.commit()
        self.package = create_backup(database, root / "local", environment="lab", revision="test-sha")
        self.encryption_key = os.urandom(32)

    def test_encrypted_roundtrip_h03_and_no_plaintext(self):
        blob, manifest = cloud._bundle(self.package, "lab", self.encryption_key)
        self.assertNotIn(b"texto-confidencial", blob)
        self.assertNotIn(b"manifest.json", blob)
        with cloud._unpack(blob, "lab", self.encryption_key) as unpacked:
            from sqlite_recovery import validate_backup
            self.assertEqual(validate_backup(unpacked, environment="lab")["sha256"], manifest["sha256"])

    def test_wrong_key_and_tampering_fail_closed(self):
        blob, _ = cloud._bundle(self.package, "lab", self.encryption_key)
        with self.assertRaises(cloud.CloudBackupError):
            with cloud._unpack(blob, "lab", os.urandom(32)):
                pass
        corrupted = bytearray(blob)
        corrupted[-1] ^= 1
        with self.assertRaises(cloud.CloudBackupError):
            with cloud._unpack(bytes(corrupted), "lab", self.encryption_key):
                pass

    def test_cross_environment_rejected(self):
        blob, _ = cloud._bundle(self.package, "lab", self.encryption_key)
        with self.assertRaises(Exception):
            with cloud._unpack(blob, "prod", self.encryption_key):
                pass
        with self.assertRaises(cloud.CloudBackupError):
            cloud._object_key("prod/20261013/" + "1" * 32 + ".h03e", "lab")
        with self.assertRaises(cloud.CloudBackupError):
            cloud._object_key("lab/../../private.h03e", "lab")

    def test_roundtrip_upload_verify_with_fake_transport(self):
        key = base64.urlsafe_b64encode(self.encryption_key).decode()
        token = { "HERALDO_BACKUP_ENCRYPTION_KEY": key }
        remote_object = {}
        def fake_http(url, *, method, headers, payload=None, limit=None):
            if method == "POST":
                remote_object["blob"] = payload
                return b"{}"
            if method == "GET":
                return remote_object["blob"]
            raise AssertionError("Unexpected method")
        with patch.dict(os.environ, token), patch.object(cloud, "_storage", return_value=("https://fake.invalid/", {"Authorization": "Bearer fake"})), patch.object(cloud, "_http", side_effect=fake_http):
            published = cloud.upload(self.package, "lab")
            self.assertEqual(published["status"], "uploaded")
            checked = cloud.download_verify(published["object"], "lab")
            self.assertEqual(checked["plaintext_sha256"], published["plaintext_sha256"])
            out = cloud.download_verify(published["object"], "lab", destination=str(Path(self.temp.name) / "downloads"))
            self.assertTrue(Path(out["local_package"]).is_dir())

    def test_no_config_no_network_and_size_guard(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(cloud.CloudBackupError):
                cloud._config()
        with patch.object(cloud, "MAX_UPLOAD_BYTES", 100):
            with self.assertRaises(cloud.CloudBackupError):
                cloud._bundle(self.package, "lab", self.encryption_key)

    def test_auth_sub_must_match_configured_user(self):
        jwt_payload = base64.urlsafe_b64encode(json.dumps({"sub": "other-user"}).encode()).decode().rstrip("=")
        with patch.object(cloud, "_http", return_value=json.dumps({"access_token": "eyJhbGciOiJIUzI1NiJ9." + jwt_payload + ".sig"}).encode()):
            with self.assertRaises(cloud.CloudBackupError):
                cloud._session("https://some.supabase.co", "public", "test@example.invalid", "password", "expected-user")

    def test_url_restricts_offsite_hosts(self):
        config = {"SUPABASE_BACKUP_URL": "https://external.example.org",
                  "SUPABASE_BACKUP_PUBLISHABLE_KEY": "pub",
                  "SUPABASE_BACKUP_EMAIL": "backup@example.invalid",
                  "SUPABASE_BACKUP_PASSWORD": "not-real",
                  "SUPABASE_BACKUP_USER_ID": "123e4567-e89b-12d3-a456-426614174000"}
        with patch.dict(os.environ, config):
            with self.assertRaises(cloud.CloudBackupError):
                cloud._config()


if __name__ == "__main__":
    unittest.main()
