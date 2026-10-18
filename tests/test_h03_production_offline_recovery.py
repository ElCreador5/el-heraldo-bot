"""Regresiones de recuperación productiva aislada, siempre con SQLite sintética.

NO prueba la copia real ni la custodia original. La ejecución productiva exige
credenciales AES originales en un entorno offline independiente.
"""
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from sqlite_recovery import create_backup, validate_backup
from tools import verify_h03_production_recovery as verifier


class ProductionRecoveryOfflineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="h03-prod-verifier-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "private"
        self.workspace.mkdir(mode=0o700)
        self.db = self.root / "synthetic.sqlite"
        with sqlite3.connect(self.db) as con:
            con.execute("CREATE TABLE synthetic (marker TEXT NOT NULL)")
            con.execute("INSERT INTO synthetic VALUES ('NO_REAL_USER_DATA')")
            con.commit()
        self.package = create_backup(
            self.db, self.root / "generations",
            environment="heraldo-production", revision="offline-synthetic")
        self.object_name = "heraldo-production/20261018/" + "a" * 32 + ".h03e"

    def _fetch_fixture(self, object_name, environment, destination):
        self.assertEqual(object_name, self.object_name)
        self.assertEqual(environment, "heraldo-production")
        folder = Path(destination)
        folder.mkdir(mode=0o700, parents=True)
        remote = folder / "package"
        shutil.copytree(self.package, remote)
        manifest = validate_backup(remote, environment=environment)
        return {"local_package": str(remote),
                "plaintext_sha256": manifest["sha256"]}

    def test_restores_synthetic_sqlite_isolated_and_cleans_up(self):
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID": ""}), patch.object(
                verifier, "download_verify", side_effect=self._fetch_fixture) as fetch:
            self.assertTrue(verifier.verify_historical_recovery(self.object_name, self.workspace))
        fetch.assert_called_once()
        self.assertEqual(list(self.workspace.iterdir()), [])
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute("SELECT marker FROM synthetic").fetchone()[0],
                             "NO_REAL_USER_DATA")

    def test_mismatched_remote_digest_blocks(self):
        def wrong(*args, **kwargs):
            result = self._fetch_fixture(*args, **kwargs)
            result["plaintext_sha256"] = "f" * 64
            return result
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID": ""}), patch.object(
                verifier, "download_verify", side_effect=wrong):
            with self.assertRaisesRegex(verifier.VerificationBlocked, "manifest_digest_mismatch"):
                verifier.verify_historical_recovery(self.object_name, self.workspace)
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_bad_remote_object_is_rejected_without_network(self):
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID": ""}), patch.object(
                verifier, "download_verify") as fetch:
            with self.assertRaises(Exception):
                verifier.verify_historical_recovery(
                    "heraldo-test/20261018/" + "a"*32 + ".h03e", self.workspace)
        fetch.assert_not_called()

    def test_railway_container_is_always_forbidden(self):
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID": "fake-railway"}, clear=False):
            with patch.object(verifier, "download_verify") as fetch:
                with self.assertRaisesRegex(verifier.VerificationBlocked, "railway_environment_forbidden"):
                    verifier.verify_historical_recovery(self.object_name, self.workspace)
            fetch.assert_not_called()

    def test_insecure_or_symlink_workspace_rejected(self):
        public = self.root / "public"
        public.mkdir(mode=0o755)
        alias = self.root / "alias"
        alias.symlink_to(self.workspace, target_is_directory=True)
        for path in (public, alias, self.root / "absent"):
            with self.subTest(path=str(path)), patch.dict(os.environ, {"RAILWAY_PROJECT_ID": ""}):
                with patch.object(verifier, "download_verify") as fetch:
                    with self.assertRaises(verifier.VerificationBlocked):
                        verifier.verify_historical_recovery(self.object_name, path)
                    fetch.assert_not_called()

    def test_cli_fails_closed_without_leaking_exception_or_path(self):
        output = StringIO()
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID": ""}), patch.object(
                verifier, "download_verify", side_effect=RuntimeError("PRIVATE_TOKEN")):
            with redirect_stdout(output):
                code = verifier.main([
                    "--object", self.object_name, "--workspace-root", str(self.workspace)])
        self.assertEqual(code, 1)
        self.assertEqual(output.getvalue().strip(), "H03_PRODUCTION_RECOVERY result=BLOCKED")
        self.assertNotIn("PRIVATE_TOKEN", output.getvalue())
        self.assertNotIn(str(self.workspace), output.getvalue())


if __name__ == "__main__":
    unittest.main()
