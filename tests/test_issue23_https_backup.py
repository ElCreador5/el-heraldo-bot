"""Guardas del respaldo puntual: sin datos reales ni credenciales."""
import io
import os
from contextlib import redirect_stdout
from unittest.mock import patch
import unittest
from urllib.error import HTTPError

import issue23_https_backup as once


class HttpsBackupTests(unittest.TestCase):
    def test_test_bucket_is_separate_from_production(self):
        self.assertEqual(once.bucket_for('heraldo-test'), 'heraldo-test-sqlite-backups')
        self.assertEqual(once.bucket_for('heraldo-production'), 'heraldo-sqlite-backups')
        self.assertNotEqual(once.bucket_for('heraldo-test'), once.bucket_for('heraldo-production'))
        with self.assertRaises(once.job.BackupJobError):
            once.bucket_for('other')

    def env(self, scope='test'):
        ids, volume, _ = once.PROFILES[scope]
        result = dict(zip(('RAILWAY_PROJECT_ID', 'RAILWAY_ENVIRONMENT_ID',
                           'RAILWAY_SERVICE_ID'), ids))
        result.update(ISSUE23_BACKUP_SCOPE=scope, RAILWAY_VOLUME_NAME=volume,
                      RAILWAY_VOLUME_MOUNT_PATH='/data', HERALDO_BACKUP_VOLUME_CAP_MB='500',
                      RAILWAY_GIT_COMMIT_SHA='a' * 40,
                      ISSUE23_BACKUP_EXPECTED_REVISION='a' * 40,
                      ISSUE23_BACKUP_REQUEST='b' * 32)
        return result

    def test_exact_test_and_production_profiles(self):
        for scope in once.PROFILES:
            self.assertEqual(once.identity(self.env(scope)),
                             (once.PROFILES[scope][2], 'a' * 40, 'b' * 32))

    def test_cross_environment_wrong_volume_revision_request_and_budget_rejected(self):
        for key, value in (
            ('RAILWAY_PROJECT_ID', 'other'), ('RAILWAY_ENVIRONMENT_ID', 'other'),
            ('RAILWAY_SERVICE_ID', 'other'), ('RAILWAY_VOLUME_NAME', 'other'),
            ('RAILWAY_VOLUME_MOUNT_PATH', '/other'), ('ISSUE23_BACKUP_SCOPE', 'lab'),
            ('ISSUE23_BACKUP_EXPECTED_REVISION', 'c' * 40),
            ('RAILWAY_GIT_COMMIT_SHA', 'c' * 40), ('ISSUE23_BACKUP_REQUEST', '../bad'),
            ('HERALDO_BACKUP_VOLUME_CAP_MB', '1000')):
            env = self.env(); env[key] = value
            with self.subTest(key=key), self.assertRaises(once.job.BackupJobError):
                once.identity(env)

    def test_known_object_must_reject_anonymous_download(self):
        with patch.object(once.request, 'build_opener') as build:
            for status in (400, 401, 403, 404):
                build.return_value.open.side_effect = HTTPError('https://example.test', status, '', {}, None)
                once.check_denied('https://example.test', 'synthetic')
            build.return_value.open.side_effect = None
            with self.assertRaisesRegex(once.job.BackupJobError, 'backup_publicly_accessible'):
                once.check_denied('https://example.test', 'synthetic')

    def test_server_failure_does_not_count_as_privacy(self):
        with patch.object(once.request, 'build_opener') as build:
            build.return_value.open.side_effect = HTTPError('https://example.test', 500, '', {}, None)
            with self.assertRaisesRegex(once.job.BackupJobError, 'privacy_probe_inconclusive'):
                once.check_denied('https://example.test', 'synthetic')

    def test_resume_bot_even_on_failure_without_printing_sensitive_exception(self):
        with patch.object(once, 'run_once', side_effect=RuntimeError('SECRET')), \
                patch.object(once.os, 'execv') as execute, \
                patch.dict(os.environ, self.env()), redirect_stdout(io.StringIO()) as output:
            once.launch()
            execute.assert_called_once_with(once.sys.executable, [once.sys.executable, 'bot.py'])
            self.assertNotIn('SECRET', output.getvalue())
            self.assertNotIn('ISSUE23_BACKUP_SCOPE', os.environ)
            self.assertNotIn('HERALDO_PRODUCTION_BACKUP_ENABLED', self.env())


if __name__ == '__main__':
    unittest.main()
