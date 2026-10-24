"""Instala/retira seis variables temporales sin desplegar; secretos solo por stdin."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from issue23_key_handoff import dpapi

PROJECT = '1edabae7-53ff-4a6c-ad55-a1dc0b865b4f'
ENVIRONMENT = 'a2ce7142-f315-4ab9-8d6e-ad058c1dc9fc'
SERVICE = '78a0bdb2-95aa-41e0-8785-32ba17ffeb70'
REVISION = '41f55654a92fa44c350d2a33d261979bf595deb2'
ORIGINAL = {'DB_PATH', 'DISCORD_TOKEN', 'MESSAGE_CONTENT_INTENT'}
TEMPORARY = {'SUPABASE_BACKUP_URL', 'SUPABASE_BACKUP_PUBLISHABLE_KEY',
             'SUPABASE_BACKUP_EMAIL', 'SUPABASE_BACKUP_PASSWORD',
             'SUPABASE_BACKUP_USER_ID', 'HERALDO_BACKUP_ENCRYPTION_KEY'}


def explicit_variables(rendered):
    return {k: v for k, v in rendered.items() if not k.startswith('RAILWAY_')}


def prepare_update(values, *, cleanup=False):
    expected = ORIGINAL if cleanup else TEMPORARY
    if set(values) != expected or any(not isinstance(v, str) or not v for v in values.values()):
        raise RuntimeError('unexpected_variable_set')
    return dict(projectId=PROJECT, environmentId=ENVIRONMENT, serviceId=SERVICE,
                skipDeploys=True, replace=cleanup, variables=values)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('install', 'cleanup'))
    parser.add_argument('--custody', type=Path, required=True)
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{32}', args.request):
        raise RuntimeError('invalid_request')
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo.parent / 'backup-tools'))
    import transfer_secure as t
    prod = ['--project', PROJECT, '--environment', ENVIRONMENT, '--service', SERVICE]
    t.TEST = ['--project', '747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61',
              '--environment', '71b77daf-9092-4af0-913f-32c57367fff3',
              '--service', '055a2bc8-0a0a-4455-8c6c-1ec0a84564bb']
    live = explicit_variables(json.loads(t.run([t.CLI, 'variables', *prod, '--json'])))
    baseline = args.custody / 'production-original-variables.dpapi'
    marker = args.custody / 'production-config-install.json'
    if args.mode == 'install':
        if set(live) != ORIGINAL or baseline.exists() or marker.exists():
            raise RuntimeError('existing_configuration_needs_review')
        custody = json.loads((args.custody / 'custody-receipt.json').read_bytes())
        if custody.get('source') != 'usb_keepass' or custody.get('gcm_authenticated') is not True:
            raise RuntimeError('custody_not_verified')
        key = dpapi((args.custody / 'key.dpapi').read_bytes(), decrypt=True)
        if len(key) != 32:
            raise RuntimeError('invalid_recovered_key')
        legacy = json.loads(t.run([t.CLI, 'variables', *t.TEST, '--json']))
        values = {k: legacy[k] for k in TEMPORARY if k != 'HERALDO_BACKUP_ENCRYPTION_KEY'}
        del legacy
        values['HERALDO_BACKUP_ENCRYPTION_KEY'] = base64.urlsafe_b64encode(key).decode()
        headers, _ = t.auth()
        name = custody['historical_object']
        if not re.fullmatch(r'heraldo-production/20261018/[0-9a-f]{32}\.h03e', name):
            raise RuntimeError('historical_object_identity_invalid')
        _, blob = t.http('/storage/v1/object/' + t.BUCKET + '/' + name, headers)
        if hashlib.sha256(blob).hexdigest() != custody['ciphertext_sha256']:
            raise RuntimeError('historical_ciphertext_changed')
        plaintext = t.AESGCM(key).decrypt(blob[len(t.PREFIX):len(t.PREFIX)+12],
                                         blob[len(t.PREFIX)+12:], t.AAD)
        del plaintext, key
        update = prepare_update(values)
        with baseline.open('xb') as output:
            output.write(dpapi(json.dumps(live).encode()))
        with marker.open('x') as output:
            json.dump(dict(request=args.request, revision=REVISION, status='prepared',
                           temporary_names=sorted(TEMPORARY)), output)
    else:
        state = json.loads(marker.read_bytes())
        if state['request'] != args.request or state['revision'] != REVISION:
            raise RuntimeError('configuration_operation_mismatch')
        original = json.loads(dpapi(baseline.read_bytes(), decrypt=True))
        if set(original) != ORIGINAL or set(live) != ORIGINAL | TEMPORARY:
            raise RuntimeError('concurrent_configuration_change')
        if any(live[k] != original[k] for k in ORIGINAL):
            raise RuntimeError('original_configuration_changed')
        update = prepare_update({k: live[k] for k in ORIGINAL}, cleanup=True)
    # Values never enter a shell command, argv, plaintext file or tool output.
    query = 'mutation TemporaryBackupVariables($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input:$input) }'
    result = json.loads(t.run([t.CLI, 'api', query, '--variables', '@-', '--compact'],
                              json.dumps({'input': update}).encode()))
    if result.get('data', {}).get('variableCollectionUpsert') is not True:
        raise RuntimeError('configuration_write_unconfirmed')
    observed = explicit_variables(json.loads(t.run([t.CLI, 'variables', *prod, '--json'])))
    expected = ORIGINAL if args.mode == 'cleanup' else ORIGINAL | TEMPORARY
    if set(observed) != expected or any(observed[k] != live[k] for k in ORIGINAL):
        raise RuntimeError('configuration_readback_mismatch')
    if args.mode == 'install' and any(observed[k] != update['variables'][k] for k in TEMPORARY):
        raise RuntimeError('temporary_configuration_readback_mismatch')
    result = dict(status=args.mode + '_verified', request=args.request,
                  checked_at=datetime.now(timezone.utc).isoformat(),
                  original_variables_unchanged=True, deploy_triggered=False,
                  daily_scheduler_activated=False)
    (args.custody / ('production-config-' + args.mode + '-result.json')).write_text(json.dumps(result))
    print('ISSUE23_CONFIG ' + args.mode.upper() + '_VERIFIED original_variables=unchanged deploy_triggered=false daily_enabled=false', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ISSUE23_CONFIG BLOCKED reason=' + type(exc).__name__, flush=True)
        sys.exit(1)
