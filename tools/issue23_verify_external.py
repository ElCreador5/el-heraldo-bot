"""Descarga independiente y restauracion offline en custodia Windows privada."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from zipfile import ZipFile

from issue23_key_handoff import dpapi, encrypted_temp


def inspect_memory(connection):
    if connection.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
        raise ValueError('integrity_failed')
    if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
        raise ValueError('foreign_keys_failed')
    schema = connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name").fetchall()
    rows, content = {}, {}
    for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        quoted = '"' + name.replace('"', '""') + '"'
        hashes = sorted(hashlib.sha256(repr(tuple(row)).encode()).hexdigest()
                        for row in connection.execute('SELECT * FROM ' + quoted))
        rows[name] = len(hashes)
        content[name] = hashlib.sha256(''.join(hashes).encode()).hexdigest()
    return dict(schema_sha256=hashlib.sha256(json.dumps(schema).encode()).hexdigest(),
                rows=rows, content=content,
                user_version=connection.execute('PRAGMA user_version').fetchone()[0],
                application_id=connection.execute('PRAGMA application_id').fetchone()[0])


def restore_in_memory(blob, key, environment, revision, cloud):
    if not blob.startswith(cloud.PREFIX):
        raise ValueError('envelope_invalid')
    raw = cloud.AESGCM(key).decrypt(blob[len(cloud.PREFIX):len(cloud.PREFIX)+12],
                                   blob[len(cloud.PREFIX)+12:], cloud.AAD)
    with ZipFile(io.BytesIO(raw)) as archive:
        if (sorted(archive.namelist()) != ['database.sqlite', 'manifest.json']
                or archive.getinfo('database.sqlite').file_size > cloud.MAX_DATABASE_BYTES
                or archive.getinfo('manifest.json').file_size > 1_000_000):
            raise ValueError('archive_invalid')
        manifest = json.loads(archive.read('manifest.json'))
        database = archive.read('database.sqlite')
    created = datetime.fromisoformat(manifest['created_at'])
    if (manifest['environment'] != environment or manifest['revision'] != revision
            or manifest['result'] != 'verified' or len(database) != manifest['size']
            or hashlib.sha256(database).hexdigest() != manifest['sha256']
            or not 0 <= (datetime.now(timezone.utc) - created).total_seconds() <= 86400):
        raise ValueError('manifest_identity_or_freshness_failed')
    from contextlib import closing
    with closing(sqlite3.connect(':memory:')) as source, closing(sqlite3.connect(':memory:')) as target:
        source.deserialize(database)
        source.execute('PRAGMA temp_store=MEMORY')
        source.execute('PRAGMA query_only=ON')
        source.backup(target)
        observed, restored = inspect_memory(source), inspect_memory(target)
        if observed != restored or any(observed[k] != manifest[k] for k in
                                      ('schema_sha256', 'rows', 'user_version', 'application_id')):
            raise ValueError('isolated_restore_content_mismatch')
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope', choices=('test', 'production'), required=True)
    parser.add_argument('--request', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--day', required=True)
    parser.add_argument('--key-custody', type=Path)
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{32}', args.request) or not re.fullmatch('[0-9a-f]{40}', args.revision) or not re.fullmatch('[0-9]{8}', args.day):
        raise ValueError('identity_invalid')
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo)); sys.path.insert(0, str(repo.parent / 'backup-tools'))
    import transfer_secure as t
    import backup_job as job
    import supabase_backup as cloud
    from issue23_https_backup import bucket_for, check_denied
    from sqlite_recovery import validate_backup
    service = ('13a555fc-7ddd-4712-a9bc-e88509e18b2b' if args.scope == 'test'
               else '055a2bc8-0a0a-4455-8c6c-1ec0a84564bb')
    flags = ['--project', '747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61',
             '--environment', '71b77daf-9092-4af0-913f-32c57367fff3', '--service', service]
    config = json.loads(t.run([t.CLI, 'variables', *flags, '--json']))
    names = ('SUPABASE_BACKUP_URL', 'SUPABASE_BACKUP_PUBLISHABLE_KEY',
             'SUPABASE_BACKUP_EMAIL', 'SUPABASE_BACKUP_PASSWORD', 'SUPABASE_BACKUP_USER_ID')
    os.environ.update({k: config[k] for k in names})
    if args.scope == 'production':
        if not args.key_custody:
            raise ValueError('verified_key_custody_required')
        receipt = json.loads((args.key_custody / 'custody-receipt.json').read_bytes())
        if receipt.get('source') != 'usb_keepass' or receipt.get('gcm_authenticated') is not True:
            raise ValueError('verified_key_custody_required')
        key = dpapi((args.key_custody / 'key.dpapi').read_bytes(), decrypt=True)
    else:
        key = base64.b64decode(config['HERALDO_BACKUP_ENCRYPTION_KEY'], altchars=b'-_', validate=True)
    del config
    if len(key) != 32:
        raise ValueError('key_invalid')
    environment = 'heraldo-' + ('production' if args.scope == 'production' else 'test')
    base, anon, email, password, uid = cloud._config()
    headers = cloud._session(base, anon, email, password, uid)
    name = environment + '/' + args.day + '/' + args.request + '.h03e'
    url = base + '/storage/v1/object/' + bucket_for(environment) + '/' + name
    blob = cloud._http(url, method='GET', headers=headers)
    check_denied(url, anon)
    check_denied(base + '/storage/v1/object/public/' + bucket_for(environment) + '/' + name, anon)
    root = encrypted_temp()
    (root / 'download.h03e').write_bytes(blob)

    def audit(event, arguments):
        if event in ('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen'):
            raise RuntimeError('offline_restore_network_forbidden')
    sys.addaudithook(audit)
    manifest = restore_in_memory(blob, key, environment, args.revision, cloud)
    created = datetime.fromisoformat(manifest['created_at'])
    sqlite_hash = manifest['sha256']
    for invalid_blob, invalid_key in ((blob[:-1] + bytes([blob[-1] ^ 1]), key), (blob, os.urandom(32))):
        try:
            restore_in_memory(invalid_blob, invalid_key, environment, args.revision, cloud)
        except cloud.InvalidTag:
            continue
        raise ValueError('invalid_ciphertext_or_key_accepted')
    result = dict(status='EXTERNAL_DOWNLOAD_OFFLINE_RESTORE_VERIFIED', scope=args.scope,
                  revision=args.revision, request_id=args.request,
                  verified_at=datetime.now(timezone.utc).isoformat(),
                  created_at=created.isoformat(), sqlite_sha256=sqlite_hash,
                  ciphertext_sha256=hashlib.sha256(blob).hexdigest(),
                  integrity_fk_schema_counts_content='ok', wrong_key_and_tamper_rejected=True,
                  anonymous_and_public_download_denied=True, live_restore=False)
    (root / 'verification-result.json').write_text(json.dumps(result))
    print('ISSUE23_EXTERNAL VERIFIED scope=' + args.scope + ' directory=' + str(root), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ISSUE23_EXTERNAL BLOCKED reason=' + type(exc).__name__, flush=True)
        sys.exit(1)
