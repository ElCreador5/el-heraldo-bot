"""Ejecutor local #23: guardas previas sin SSH, secretos ni bases reales."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as NS
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('issue23_backup_runner',
    Path(__file__).resolve().parents[1] / 'tools/run_issue23_backup.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class BackupRunnerTests(unittest.TestCase):
    def test_changed_audited_helper_is_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / 'pr19_production_backup.py').write_text("raise AssertionError('must not import')")
            with self.assertRaisesRegex(RuntimeError, 'audited_helper_changed'):
                runner.prepare(folder)

    def test_revision_generation_and_volume_guards_are_rebased(self):
        source = '''from pathlib import Path
from types import SimpleNamespace
t = SimpleNamespace(REV='old')
private_root = Path('private')
REMOTE = "destination=root/'pr19-20261018'\\nmount=Path('/data');assert mount.is_mount() and not mount.is_symlink()"
'''
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / 'pr19_production_backup.py').write_text(source)
            (folder / 'transfer_secure.py').write_text('# synthetic fixture')
            hashes = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                      for name in runner.HELPER_HASHES}
            with patch.dict(runner.HELPER_HASHES, hashes, clear=True):
                module = runner.prepare(folder)
            self.assertEqual(module.REV, runner.REVISION)
            self.assertEqual(module.t.REV, runner.REVISION)
            self.assertEqual(module.dest, Path('private') / runner.GENERATION)
            self.assertNotIn('pr19-20261018', module.REMOTE)
            self.assertIn(runner.GENERATION, module.REMOTE)
            self.assertIn("RAILWAY_VOLUME_NAME')=='heraldo-data'", module.REMOTE)
            self.assertIn("RAILWAY_VOLUME_MOUNT_PATH')=='/data'", module.REMOTE)

    def privacy_probe(self, authenticated=b'ciphertext', public_status=404, checksum='expected'):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        folder = root / 'pr19-20261018'
        folder.mkdir()
        (folder / 'transfer-plan.json').write_text(json.dumps({
            'object': 'heraldo-production/20261018/object.h03e',
            'ciphertext_sha256': checksum}))
        calls = []
        def http(path, headers, **kwargs):
            calls.append((path, headers))
            return (200, authenticated) if headers == 'private' else (public_status, b'')
        module = NS(private_root=root, t=NS(BUCKET='private-bucket', http=http,
                                            digest=lambda data: 'expected'))
        return module, calls

    def test_existing_authenticated_object_and_both_denials_are_required(self):
        module, calls = self.privacy_probe()
        runner.verify_private_access(module, 'private', 'anonymous')
        self.assertEqual(len(calls), 3)
        self.assertIn('/public/', calls[-1][0])

    def test_public_access_aborts(self):
        module, _ = self.privacy_probe(public_status=200)
        with self.assertRaisesRegex(RuntimeError, 'publicly_accessible'):
            runner.verify_private_access(module, 'private', 'anonymous')

    def test_changed_historical_object_aborts(self):
        module, _ = self.privacy_probe(checksum='tampered')
        with self.assertRaisesRegex(RuntimeError, 'checksum_failed'):
            runner.verify_private_access(module, 'private', 'anonymous')


if __name__ == '__main__':
    unittest.main()
