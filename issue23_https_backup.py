"""Copia puntual por HTTPS antes de iniciar el bot; sin activar el diario H-03.

La misma fuente puede ejecutarse en memoria sobre el SHA productivo existente.
Nunca restaura SQLite activa, imprime secretos ni reintenta subidas ambiguas.
"""
from contextlib import closing
from datetime import datetime, timezone
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from urllib import error, request

import backup_job as job
import supabase_backup as cloud
from sqlite_recovery import create_backup, validate_backup

ROOT = Path('/data/.heraldo-issue23-https')
PROFILES = {
    # main aun no define backup_job.TEST_IDS. El ejecutor debe funcionar sobre
    # el codigo productivo existente, antes de integrar cualquier funcionalidad.
    'test': (('747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61',
              '71b77daf-9092-4af0-913f-32c57367fff3',
              '13a555fc-7ddd-4712-a9bc-e88509e18b2b'), 'worker-volume', 'heraldo-test'),
    'production': (job.PRODUCTION_IDS, 'heraldo-data', 'heraldo-production'),
}


def bucket_for(environment):
    # Test tiene bucket e identidad separados; nunca probar contra produccion.
    if environment == 'heraldo-test':
        return cloud.TEST_BUCKET
    if environment == 'heraldo-production':
        return cloud.BUCKET
    raise job.BackupJobError('invalid_environment')


def identity(env):
    scope = env.get('ISSUE23_BACKUP_SCOPE')
    if scope not in PROFILES:
        raise job.BackupJobError('invalid_scope')
    ids, volume, environment = PROFILES[scope]
    observed = tuple(env.get(k) for k in (
        'RAILWAY_PROJECT_ID', 'RAILWAY_ENVIRONMENT_ID', 'RAILWAY_SERVICE_ID'))
    if observed != ids or env.get('RAILWAY_VOLUME_NAME') != volume:
        raise job.BackupJobError('identity_mismatch')
    if env.get('RAILWAY_VOLUME_MOUNT_PATH') != '/data':
        raise job.BackupJobError('mount_mismatch')
    revision = env.get('ISSUE23_BACKUP_EXPECTED_REVISION', '')
    if not re.fullmatch('[0-9a-f]{40}', revision) or revision != env.get('RAILWAY_GIT_COMMIT_SHA'):
        raise job.BackupJobError('revision_mismatch')
    operation = env.get('ISSUE23_BACKUP_REQUEST', '')
    if not re.fullmatch('[0-9a-f]{32}', operation):
        raise job.BackupJobError('invalid_request')
    if env.get('HERALDO_BACKUP_VOLUME_CAP_MB') != '500':
        raise job.BackupJobError('unverified_volume_budget')
    return environment, revision, operation


def check_denied(url, anon):
    try:
        opener = request.build_opener(cloud._NoRedirect() if hasattr(cloud, '_NoRedirect')
                                     else NoRedirect())
        with opener.open(request.Request(url, headers={'apikey': anon}), timeout=20):
            raise job.BackupJobError('backup_publicly_accessible')
    except error.HTTPError as exc:
        if exc.code not in (400, 401, 403, 404):
            raise job.BackupJobError('privacy_probe_inconclusive') from None


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def run_once():
    environment, revision, operation = identity(os.environ)
    mount = Path('/data')
    source = Path(os.environ.get('DB_PATH', ''))
    if (not mount.is_mount() or mount.is_symlink() or not source.is_absolute()
            or source.is_symlink() or not source.is_file()
            or source != source.resolve() or not source.is_relative_to(mount)
            or source.is_relative_to(ROOT)):
        raise job.BackupJobError('source_or_mount_invalid')
    secret = cloud._key()
    base, anon, email, password, uid = cloud._config()
    headers = cloud._session(base, anon, email, password, uid)
    root = job._private_root(ROOT)
    with job._exclusive_job_lock(root):
        receipt_path = root / (operation + '.json')
        if receipt_path.exists() or receipt_path.is_symlink():
            # No retry after an uncertain transfer, even on container restart.
            raise job.BackupJobError('existing_request_review_required')
        job._require_backup_headroom(source, root)
        workspace = job._private_root(root / operation)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d')
        object_name = environment + '/' + stamp + '/' + operation + '.h03e'
        receipt = dict(status='started', request_id=operation, revision=revision,
                       environment=environment, object=object_name)
        job._write_receipt(receipt_path, receipt, initial=True)
        try:
            package = create_backup(source, workspace / 'generations',
                                    environment=environment, revision=revision, timeout=90)
            manifest = validate_backup(package, environment=environment)
            blob, _ = cloud._bundle(package, environment, secret)
            receipt.update(status='upload_unconfirmed',
                           sqlite_sha256=manifest['sha256'],
                           ciphertext_sha256=hashlib.sha256(blob).hexdigest(),
                           created_at=manifest['created_at'])
            job._write_receipt(receipt_path, receipt)
            bucket = bucket_for(environment)
            url = base + '/storage/v1/object/' + bucket + '/' + object_name
            cloud._http(url, method='POST', payload=blob, headers={
                **headers, 'Content-Type': 'application/octet-stream',
                'Cache-Control': 'no-store', 'x-upsert': 'false'}, limit=8192)
            receipt['status'] = 'uploaded_unverified'
            job._write_receipt(receipt_path, receipt)
            downloaded = cloud._http(url, method='GET', headers=headers)
            if downloaded != blob:
                raise job.BackupJobError('ciphertext_download_mismatch')
            with cloud._unpack(downloaded, environment, secret) as remote:
                remote_manifest = validate_backup(remote, environment=environment)
                if remote_manifest != manifest:
                    raise job.BackupJobError('remote_manifest_mismatch')
                job._isolated_restore(remote, workspace / 'restored.sqlite', manifest)
            check_denied(url, anon)
            check_denied(base + '/storage/v1/object/public/' + bucket + '/' + object_name, anon)
            receipt.update(status='verified_and_restored',
                           finished_at=datetime.now(timezone.utc).isoformat(),
                           anonymous_download_denied=True, public_download_denied=True)
            job._write_receipt(receipt_path, receipt)
        except BaseException:
            receipt.update(failed_stage=receipt['status'], status='needs_manual_review')
            job._write_receipt(receipt_path, receipt)
            raise
    return 'verified_and_restored'


def launch():
    """El bot vuelve a iniciar aun si el respaldo falla; no oculta el fallo."""
    try:
        status = run_once()
        print('ISSUE23_HTTPS status=' + status, flush=True)
    except BaseException as exc:
        safe = str(exc) if type(exc) in (job.BackupJobError, cloud.CloudBackupError) else type(exc).__name__
        if not re.fullmatch('[A-Za-z0-9_]+', safe):
            safe = 'unexpected_failure'
        print('ISSUE23_HTTPS status=BLOCKED reason=' + safe, flush=True)
    finally:
        # Variables used solely by this child must not activate daily H-03.
        if os.environ.get('ISSUE23_BACKUP_SCOPE') == 'production':
            for key in ('SUPABASE_BACKUP_URL', 'SUPABASE_BACKUP_PUBLISHABLE_KEY',
                        'SUPABASE_BACKUP_EMAIL', 'SUPABASE_BACKUP_PASSWORD',
                        'SUPABASE_BACKUP_USER_ID', 'HERALDO_BACKUP_ENCRYPTION_KEY'):
                os.environ.pop(key, None)
        for key in ('ISSUE23_BACKUP_SCOPE', 'ISSUE23_BACKUP_REQUEST',
                    'ISSUE23_BACKUP_EXPECTED_REVISION'):
            os.environ.pop(key, None)
        os.execv(sys.executable, [sys.executable, 'bot.py'])


if __name__ == '__main__':
    launch()
