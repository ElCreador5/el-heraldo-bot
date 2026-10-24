"""Respaldo único #23 desde el PowerShell del propietario, sin publicar código.

Reutiliza los ejecutores locales auditados, con SHA de producción y generación
actualizados. Nunca imprime credenciales, contenido SQLite ni manifiestos.
--preflight comprueba custodia y autenticación sin crear respaldo ni subir datos.
No reintentar automáticamente si existe una generación parcial.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

REVISION = '41f55654a92fa44c350d2a33d261979bf595deb2'
GENERATION = 'issue23-20261024-41f55654'
HELPER_HASHES = {
    'pr19_production_backup.py': '71b18579200e0eb59c994178b9af6449d3d17fb7d2540236cd000cb7c017037d',
    'transfer_secure.py': 'ab596afe322328d7649f7798a5755ae833b920dc5f629da6a2909feeb71bebb4',
}


def prepare(helper_dir):
    """Validar los ayudantes antes de importar o ejecutar cualquier operación."""
    for name, expected in HELPER_HASHES.items():
        if hashlib.sha256((helper_dir / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('audited_helper_changed')
    sys.path.insert(0, str(helper_dir))
    spec = importlib.util.spec_from_file_location('issue23_audited_backup', helper_dir / 'pr19_production_backup.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REV = module.t.REV = REVISION
    module.dest = module.private_root / GENERATION
    anchor = "destination=root/'pr19-20261018'"
    if module.REMOTE.count(anchor) != 1:
        raise RuntimeError('remote_generation_anchor_changed')
    module.REMOTE = module.REMOTE.replace(anchor, 'destination=root/' + repr(GENERATION), 1)
    module.REMOTE = module.REMOTE.replace(
        "mount=Path('/data');assert mount.is_mount() and not mount.is_symlink()",
        "assert os.environ.get('RAILWAY_VOLUME_NAME')=='heraldo-data'\n"
        "assert os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')=='/data'\n"
        "mount=Path('/data');assert mount.is_mount() and not mount.is_symlink()", 1)
    return module


def verify_custody(module):
    if os.name != 'nt':
        raise RuntimeError('run_from_owner_windows_powershell')
    if not module.private_root.is_dir() or not module.keyfile.is_file():
        raise RuntimeError('existing_private_custody_missing')
    paths = [module.private_root, module.keyfile.parent, module.keyfile]
    checks = []
    for path in paths:
        literal = str(path).replace("'", "''")
        checks.append("$a=Get-Acl -LiteralPath '" + literal + "';"
                      "foreach($r in $a.Access){if($r.AccessControlType -eq 'Allow'){"
                      "$sid=$r.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value;"
                      "if($sid -notin @($owner,'S-1-5-18')){throw 'custody_not_private'}}};")
    code = "$ErrorActionPreference='Stop';$owner=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value;" + ''.join(checks)
    encoded = base64.b64encode(code.encode('utf-16-le')).decode('ascii')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                            capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError('custody_acl_verification_failed')
    key = base64.b64decode(module.keyfile.read_bytes().strip(), altchars=b'-_', validate=True)
    if len(key) != 32:
        raise RuntimeError('existing_recovery_key_invalid')


def verify_private_access(module, headers, anonymous):
    # La identidad INSERT/SELECT no administra metadatos del bucket. Probar
    # un objeto existente y autentificado, no un 404 de una ruta inventada.
    plan = json.loads((module.private_root / 'pr19-20261018' / 'transfer-plan.json').read_bytes())
    key = plan['object']
    if not key.startswith('heraldo-production/') or '..' in key:
        raise RuntimeError('historical_privacy_probe_identity_invalid')
    path = '/storage/v1/object/' + module.t.BUCKET + '/' + key
    status, raw = module.t.http(path, headers)
    if status != 200 or module.t.digest(raw) != plan['ciphertext_sha256']:
        raise RuntimeError('historical_privacy_probe_checksum_failed')
    for url in (path, '/storage/v1/object/public/' + module.t.BUCKET + '/' + key):
        denied, _ = module.t.http(url, anonymous, allow_denied=True)
        if denied not in (400, 401, 403, 404):
            raise RuntimeError('historical_backup_publicly_accessible')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    helper_dir = Path(__file__).resolve().parents[2] / 'backup-tools'
    module = prepare(helper_dir)
    os.environ['RAILWAY_CALLER'] = 'skill:use-railway@1.3.5'
    os.environ['RAILWAY_AGENT_SESSION'] = 'heraldo-issue23-owner-backup'
    verify_custody(module)
    if module.dest.exists():
        raise RuntimeError('generation_exists_review_receipts_before_retry')
    headers, anonymous = module.t.auth()
    verify_private_access(module, headers, anonymous)
    if args.preflight:
        print('ISSUE23_PREFLIGHT local_custody=verified storage_identity=verified bucket=private backup_created=false')
        return
    # Fija el resultado de la autenticación ya comprobada para este intento.
    module.t.auth = lambda: (headers, anonymous)
    print('ISSUE23_BACKUP starting=true overwrite=false live_restore=false', flush=True)
    module.main()
    plan = json.loads((module.dest / 'transfer-plan.json').read_bytes())
    verify_private_access(module, headers, anonymous)
    path = '/storage/v1/object/' + module.t.BUCKET + '/' + plan['object']
    for url in (path, '/storage/v1/object/public/' + module.t.BUCKET + '/' + plan['object']):
        status, _ = module.t.http(url, anonymous, allow_denied=True)
        if status not in (400, 401, 403, 404):
            raise RuntimeError('unauthorized_backup_download_not_denied')
    receipt = json.loads((module.dest / 'verification-result.json').read_bytes())
    receipt.update({'anonymous_download_denied': True, 'public_download_denied': True,
                    'private_access_verified': True, 'issue': 23})
    module.t.put(module.dest / 'issue23-final-verification.json', json.dumps(receipt).encode())
    print('ISSUE23_BACKUP VERIFIED external_download=true isolated_restore=true integrity_fk_schema_counts_content=ok private_access=verified')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Ni tracebacks ni respuestas del proveedor: podrían contener datos privados.
        print('ISSUE23_BACKUP BLOCKED reason=' + type(exc).__name__ +
              (':' + str(exc) if type(exc) is RuntimeError else '') +
              ' automatic_retry=false')
        sys.exit(1)
