"""Verificación productiva H-03 en entorno offline independiente, SIN despliegue.

La copia remota se descarga, se descifra, se autentica y se restaura solo en un
directorio nuevo y privado. No lee DB_PATH, no toca SQLite activa ni Railway.
La clave original y credenciales proceden únicamente del operador, mediante
variables de entorno del entorno aislado; jamás se aceptan por argumentos CLI.
"""
import argparse
import os
from pathlib import Path
import re
import stat
import tempfile

from backup_job import _isolated_restore
from sqlite_recovery import validate_backup
from supabase_backup import _object_key, download_verify

_ENVIRONMENT = "heraldo-production"


class VerificationBlocked(RuntimeError):
    """Fallo de seguridad o de verificación, con motivo no privado."""


def _check_workspace(value):
    path = Path(value)
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise VerificationBlocked("invalid_private_workspace")
    path = path.resolve(strict=True)
    info = path.stat()
    if (os.name != "posix" or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) & 0o077):
        raise VerificationBlocked("workspace_not_private")
    return path


def verify_historical_recovery(object_name, workspace_root):
    """Exige objeto productivo y valida SQLite restaurada sin conservar copias.

    No demuestra por si sola la independencia de la custodia de la clave:
    el operador debe certificar esa condición por separado.
    """
    if os.environ.get("RAILWAY_PROJECT_ID"):
        raise VerificationBlocked("railway_environment_forbidden")
    workspace_root = _check_workspace(workspace_root)
    object_name = _object_key(object_name, _ENVIRONMENT)
    # Una carpeta efímera en volumen privado elegido por el custodio. No se
    # imprime la ubicación ni el hash de la base en stdout ni stderr.
    with tempfile.TemporaryDirectory(prefix="h03-prod-verify-", dir=workspace_root) as temp:
        work = Path(temp)
        received = download_verify(object_name, _ENVIRONMENT, destination=work / "download")
        package = received.get("local_package")
        if not isinstance(package, str):
            raise VerificationBlocked("missing_downloaded_package")
        package_path = Path(package).resolve(strict=True)
        if not package_path.is_relative_to(work.resolve()):
            raise VerificationBlocked("download_outside_workspace")
        manifest = validate_backup(package_path, environment=_ENVIRONMENT)
        if manifest["sha256"] != received.get("plaintext_sha256"):
            raise VerificationBlocked("manifest_digest_mismatch")
        _isolated_restore(package_path, work / "restored.sqlite", manifest)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Comprobación H-03 productiva aislada, sin despliegue")
    parser.add_argument("--object", required=True, help="Nombre remoto privado, prefijo heraldo-production/")
    parser.add_argument("--workspace-root", required=True, help="Directorio Linux privado y cifrado")
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"heraldo-production/[0-9]{8}/[0-9a-f]{32}\.h03e", args.object):
            raise VerificationBlocked("invalid_object")
        verify_historical_recovery(args.object, args.workspace_root)
        print("H03_PRODUCTION_RECOVERY result=VERIFIED_REMOTE_AND_ISOLATED")
        return 0
    except Exception:
        # Nunca imprimir secretos, nombre completo del objeto, datos, hashes o
        # excepciones de red/SQLite que pudieran revelar rutas privadas.
        print("H03_PRODUCTION_RECOVERY result=BLOCKED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
