"""Verificación de despliegue Enzonic vía objetos Git sin cuota REST."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import backup_job
import enzonic_test_host as host


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.DEVNULL
    ).decode().strip()


class EnzonicGitFallbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.remote = base / "bare.git"
        self.publisher = base / "publisher"
        self.runtime = base / "runtime"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "Pruebas", str(self.publisher)], check=True)
        for filename in ("bot.py", "enzonic_test_host.py"):
            (self.publisher / filename).write_text("original " + filename + "\n")
        git(self.publisher, "add", "bot.py", "enzonic_test_host.py")
        git(self.publisher, "-c", "user.name=Fixture", "-c",
            "user.email=fixture@example.invalid", "commit", "-qm", "Inicial")
        git(self.publisher, "remote", "add", "origin", str(self.remote))
        git(self.publisher, "push", "-q", "-u", "origin", "Pruebas")
        subprocess.run(["git", "clone", "-q", "-b", "Pruebas", str(self.remote),
                        str(self.runtime)], check=True)
        self.old_commit = git(self.runtime, "rev-parse", "HEAD")
        for filename in ("bot.py", "enzonic_test_host.py"):
            (self.publisher / filename).write_text("actualizado " + filename + "\n")
        git(self.publisher, "add", "bot.py", "enzonic_test_host.py")
        git(self.publisher, "-c", "user.name=Fixture", "-c",
            "user.email=fixture@example.invalid", "commit", "-qm", "Actualizado")
        git(self.publisher, "push", "-q", "origin", "Pruebas")
        self.latest_commit = git(self.publisher, "rev-parse", "HEAD")
        for filename in ("bot.py", "enzonic_test_host.py"):
            shutil.copy2(self.publisher / filename, self.runtime / filename)
        p = patch.object(host, "ROOT", self.runtime)
        p.start()
        self.addCleanup(p.stop)

    def test_git_verifies_all_deployed_files_without_using_rest(self):
        with patch.object(host, "_trusted_origin_url", return_value=True), \
                patch.object(host, "_github_metadata", side_effect=AssertionError("REST no permitido")):
            self.assertEqual(host.revision(), self.latest_commit)
        self.assertEqual(git(self.runtime, "rev-parse", "HEAD"), self.old_commit)
        self.assertEqual((self.runtime / "bot.py").read_text(), "actualizado bot.py\n")

    def test_missing_file_or_modified_file_blocks_without_reset(self):
        with patch.object(host, "_trusted_origin_url", return_value=True):
            self.assertEqual(host._verified_git_deployment(), self.latest_commit)
            (self.runtime / "bot.py").write_text("contenido no autorizado\n")
            with self.assertRaisesRegex(backup_job.BackupJobError, "checkout_unverified"):
                host._verified_git_deployment()
            (self.runtime / "bot.py").unlink()
            with self.assertRaisesRegex(backup_job.BackupJobError, "checkout_unverified"):
                host._verified_git_deployment()

    def test_only_official_origin_is_trusted(self):
        self.assertTrue(host._trusted_origin_url(
            "https://github.com/ElCreador5/el-heraldo-bot.git"))
        self.assertFalse(host._trusted_origin_url(
            "https://example.invalid/ElCreador5/el-heraldo-bot.git"))
        self.assertFalse(host._trusted_origin_url(
            "https://github.com/another/el-heraldo-bot.git"))


if __name__ == "__main__":
    unittest.main()
