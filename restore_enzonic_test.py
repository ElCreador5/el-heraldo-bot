#!/usr/bin/env python3
"""Restauracion aislada de El Heraldo Test en Enzonic (un solo uso).

NO inicia Discord; NO modifica la base activa si ya existe; NO modifica
Railway ni produccion. Solo usar con servidor de pruebas detenido.
La ruta del respaldo se recibe por variable privada, nunca se publica en Git.
"""
import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

DESTINATION = Path("/home/container/heraldo.db")
ENVIRONMENT = "heraldo-test"


class MigrationBlocked(RuntimeError):
    pass


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _preflight():
    if os.environ.get("DB_PATH") != str(DESTINATION):
        raise MigrationBlocked("DB_PATH_INCORRECTO")
    if not DESTINATION.parent.is_dir() or DESTINATION.parent.is_symlink():
        raise MigrationBlocked("CARPETA_DESTINO_NO_VALIDA")
    if DESTINATION.exists() or DESTINATION.is_symlink():
        raise MigrationBlocked("YA_EXISTE_BASE_NO_SOBRESCRIBIR")
    if any(Path(str(DESTINATION) + ext).exists() for ext in ("-wal", "-shm", "-journal")):
        raise MigrationBlocked("ARCHIVOS_SQLITE_EXISTENTES")
    object_name = os.environ.get("HERALDO_TEST_RECOVERY_OBJECT", "")
    if not re.fullmatch(r"heraldo-test/[0-9]{8}/[0-9a-f]{32}\.h03e", object_name):
        raise MigrationBlocked("RESPALDO_TEST_NO_SELECCIONADO")
    required = ("HERALDO_BACKUP_ENCRYPTION_KEY", "SUPABASE_BACKUP_URL",
                "SUPABASE_BACKUP_PUBLISHABLE_KEY", "SUPABASE_BACKUP_EMAIL",
                "SUPABASE_BACKUP_PASSWORD", "SUPABASE_BACKUP_USER_ID")
    if any(not os.environ.get(name) for name in required):
        raise MigrationBlocked("CREDENCIALES_TEST_INCOMPLETAS")
    if os.environ.get("HERALDO_TEST_BACKUP_ENABLED"):
        raise MigrationBlocked("PLANIFICADOR_ANTIGUO_HABILITADO")
    return object_name


def _install_verified_copy(source, expected_hash):
    with tempfile.TemporaryDirectory(prefix=".heraldo-install-", dir=DESTINATION.parent) as directory:
        staged = Path(directory) / "validated.sqlite"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(staged, flags, 0o600)
        with os.fdopen(fd, "wb") as output, open(source, "rb") as original:
            shutil.copyfileobj(original, output, length=1024 * 1024)
            output.flush()
            os.fsync(output.fileno())
        if _sha256(staged) != expected_hash:
            raise MigrationBlocked("HASH_NO_COINCIDE")
        if stat.S_IMODE(staged.stat().st_mode) & 0o077:
            raise MigrationBlocked("PERMISOS_INSEGUROS")
        try:
            os.link(staged, DESTINATION, follow_symlinks=False)
        except FileExistsError as exc:
            raise MigrationBlocked("YA_EXISTE_BASE_NO_SOBRESCRIBIR") from exc
        except OSError as exc:
            raise MigrationBlocked("INSTALACION_NO_DISPONIBLE") from exc
        directory_fd = os.open(DESTINATION.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        if _sha256(DESTINATION) != expected_hash:
            raise MigrationBlocked("VERIFICACION_FINAL_FALLO")


def main():
    try:
        object_name = _preflight()
        from supabase_backup import download_verify
        from sqlite_recovery import validate_backup
        from backup_job import _isolated_restore
        with tempfile.TemporaryDirectory(prefix=".heraldo-recovery-", dir=DESTINATION.parent) as directory:
            root = Path(directory)
            remote = download_verify(object_name, ENVIRONMENT, destination=root / "package")
            package = Path(remote["local_package"])
            manifest = validate_backup(package, environment=ENVIRONMENT)
            source = package / "database.sqlite"
            if manifest["sha256"] != remote["plaintext_sha256"] or _sha256(source) != manifest["sha256"]:
                raise MigrationBlocked("RESPALDO_NO_VALIDADO")
            _isolated_restore(package, root / "isolated.sqlite", manifest)
            _install_verified_copy(source, manifest["sha256"])
        print("HERALDO_TEST_RECOVERY status=VERIFIED_AND_INSTALLED", flush=True)
        return 0
    except MigrationBlocked as exc:
        print("HERALDO_TEST_RECOVERY status=BLOCKED reason=" + str(exc), flush=True)
        return 1
    except Exception:
        print("HERALDO_TEST_RECOVERY status=BLOCKED reason=RECOVERY_FAILED", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
