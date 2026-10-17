"""Copias SQLite consistentes y restauración offline; no conecta a Discord.

Los paquetes contienen datos privados. No enviarlos a Git ni imprimir registros.
El bloqueo de servicio es cooperativo: todos los procesos del bot deben usarlo.
"""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import tempfile
import time
import uuid


class RecoveryError(RuntimeError):
    """Error operacional seguro, sin contenido de la base de datos."""


def readonly(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise RecoveryError("database_not_file")
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)


def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def inspect_database(path):
    with closing(readonly(path)) as conn:
        if conn.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise RecoveryError("integrity_failed")
        if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise RecoveryError("foreign_keys_failed")
        schema = conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE sql IS NOT NULL ORDER BY type,name").fetchall()
        if not schema:
            raise RecoveryError("empty_schema")
        counts = {}
        for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            quoted = '"' + name.replace('"', '""') + '"'
            counts[name] = conn.execute(f"SELECT count(*) FROM {quoted}").fetchone()[0]
        return {
            "schema_sha256": hashlib.sha256(json.dumps(schema).encode()).hexdigest(),
            "user_version": conn.execute("PRAGMA user_version").fetchone()[0],
            "application_id": conn.execute("PRAGMA application_id").fetchone()[0],
            "rows": counts,
        }


def private_directory(path):
    if os.name != "posix":
        raise RecoveryError("private_backup_requires_posix_permissions")
    path = Path(path)
    if path.is_symlink():
        raise RecoveryError("symlink_directory")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise RecoveryError("directory_not_private")
    return path.resolve()


def sync_path(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def service_lock(db_path, *, exclusive=False):
    """Bloqueo cooperativo del bot y la restauración sobre la misma ruta."""
    path = Path(db_path).resolve().with_name(Path(db_path).name + ".service.lock")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        info = os.fstat(fd)
        if os.name == "posix" and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
            raise RecoveryError("lock_not_private")
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except OSError as exc:
            raise RecoveryError("service_running_or_restore_active") from exc
        yield
    finally:
        os.close(fd)


def create_backup(source, destination, *, environment, revision, timeout=30, operation=None):
    """Copia online publicada únicamente tras validación y fsync."""
    if not environment or not revision or timeout <= 0:
        raise RecoveryError("missing_backup_identity")
    source = Path(source).resolve(strict=True)
    root = private_directory(destination)
    stage = Path(tempfile.mkdtemp(prefix=".partial-", dir=root))
    started = time.monotonic()
    try:
        database = stage / "database.sqlite"
        fd = os.open(database, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        def progress(status, remaining, total):
            if time.monotonic() - started > timeout:
                raise RecoveryError("backup_timeout")
        with closing(readonly(source)) as src, closing(sqlite3.connect(database)) as target:
            page_size = src.execute("PRAGMA page_size").fetchone()[0]
            pages = src.execute("PRAGMA page_count").fetchone()[0]
            if shutil.disk_usage(root).free < pages * page_size + 8 * 1024 * 1024:
                raise RecoveryError("insufficient_storage")
            src.backup(target, pages=128, progress=progress, sleep=0.01)
            target.execute("PRAGMA journal_mode=DELETE")
        manifest = {
            "format": 1, "environment": environment, "revision": revision,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sqlite_version": sqlite3.sqlite_version, "result": "verified",
            "size": database.stat().st_size, "sha256": digest(database),
            **inspect_database(database),
            "evidence_files_included": False,
        }
        # Included inside the authenticated encrypted package by H-03.
        if operation is not None:
            manifest["operation"] = operation
        metadata = stage / "manifest.json"
        fd = os.open(metadata, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(manifest, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        sync_path(database)
        sync_path(stage)
        final = root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex)
        stage.rename(final)
        sync_path(root)
        return final
    except BaseException:
        # Si el proceso muere abruptamente, .partial-* no es un respaldo válido.
        if stage.exists():
            shutil.rmtree(stage)
        raise


def validate_backup(package, *, environment):
    package = Path(package)
    if package.name.startswith(".partial-"):
        raise RecoveryError("incomplete_package")
    private_directory_existing(package)
    for name in ("database.sqlite", "manifest.json"):
        item = package / name
        if item.is_symlink() or not item.is_file() or item.stat().st_mode & 0o077:
            raise RecoveryError("package_not_private")
    if any((package / ("database.sqlite" + suffix)).exists()
           for suffix in ("-wal", "-shm", "-journal")):
        raise RecoveryError("backup_has_sidecars")
    try:
        manifest = json.loads((package / "manifest.json").read_text())
    except (ValueError, OSError) as exc:
        raise RecoveryError("invalid_manifest") from exc
    database = package / "database.sqlite"
    if (manifest.get("format") != 1 or manifest.get("result") != "verified"
            or manifest.get("environment") != environment):
        raise RecoveryError("backup_identity_mismatch")
    if manifest.get("size") != database.stat().st_size or manifest.get("sha256") != digest(database):
        raise RecoveryError("backup_checksum_failed")
    actual = inspect_database(database)
    if any(manifest.get(key) != value for key, value in actual.items()):
        raise RecoveryError("backup_metadata_mismatch")
    return manifest


def private_directory_existing(path):
    if not Path(path).is_dir():
        raise RecoveryError("missing_package")
    return private_directory(path)


def retention_plan(destination, *, environment, keep_min=7, max_age_days=30):
    """Propone conservación sin borrar archivos ni tocar evidencias de Discord."""
    if keep_min < 1 or max_age_days < 1:
        raise RecoveryError("invalid_retention_policy")
    root = private_directory_existing(destination)
    valid, unverified = [], []
    for package in root.iterdir():
        try:
            manifest = validate_backup(package, environment=environment)
            created = datetime.fromisoformat(manifest['created_at'])
            if created.tzinfo is None:
                raise ValueError('missing_timezone')
            valid.append((created, package))
        except (RecoveryError, OSError, sqlite3.Error, ValueError, KeyError):
            unverified.append(str(package))
    valid.sort(reverse=True)
    cutoff = datetime.now(timezone.utc).timestamp() - max_age_days * 86400
    candidates = [str(path) for index, (created, path) in enumerate(valid)
                  if index >= keep_min and created.timestamp() < cutoff]
    return {'result': 'plan_only', 'keep_min': keep_min, 'max_age_days': max_age_days,
            'candidates': candidates, 'unverified_preserved': unverified}


def restore_backup(package, target, *, environment, schema_from, service_stopped=False):
    """Offline, entorno y esquema explícitos; conserva la base anterior."""
    if not service_stopped:
        raise RecoveryError("stop_service_first")
    target = Path(target)
    if target.is_symlink():
        raise RecoveryError("symlink_target")
    target = target.resolve()
    if target == (Path(package) / "database.sqlite").resolve():
        raise RecoveryError("target_is_backup")
    expected = inspect_database(schema_from)
    rollback = None
    with service_lock(target, exclusive=True):
        # Un proceso antiguo sin bloqueo podría conservar WAL o journal abiertos.
        # No borrar estos archivos ni forzar su recuperación.
        if any(Path(str(target) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            raise RecoveryError("active_or_unclean_database")
        fd, name = tempfile.mkstemp(prefix=".restore-", suffix=".sqlite", dir=target.parent)
        os.close(fd)
        staged = Path(name)
        try:
            # Validar también la copia privada de los bytes que se instalarán.
            manifest = validate_backup(package, environment=environment)
            shutil.copyfile(Path(package) / "database.sqlite", staged)
            actual = inspect_database(staged)
            if digest(staged) != manifest["sha256"]:
                raise RecoveryError("backup_changed_during_restore")
            keys = ("schema_sha256", "user_version", "application_id")
            if any(actual[key] != expected[key] for key in keys):
                raise RecoveryError("schema_incompatible")
            if target.exists():
                if any(inspect_database(target)[key] != expected[key] for key in keys):
                    raise RecoveryError("target_schema_incompatible")
                rollback = create_backup(target, target.parent / ".recovery-history",
                                         environment=environment, revision="pre-restore")
            sync_path(staged)
            os.replace(staged, target)
            sync_path(target.parent)
            return {"result": "restored", "sha256": manifest["sha256"],
                    "previous_backup": str(rollback) if rollback else None}
        finally:
            staged.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Respaldos privados SQLite; restauración offline")
    sub = parser.add_subparsers(dest="command", required=True)
    backup = sub.add_parser("backup")
    backup.add_argument("--db", required=True)
    backup.add_argument("--destination", required=True)
    backup.add_argument("--revision", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("package")
    restore = sub.add_parser("restore")
    restore.add_argument("package")
    restore.add_argument("--db", required=True)
    restore.add_argument("--schema-from", required=True)
    restore.add_argument("--service-stopped", action="store_true")
    retention = sub.add_parser("retention-plan")
    retention.add_argument("--destination", required=True)
    retention.add_argument("--keep-min", type=int, default=7)
    retention.add_argument("--max-age-days", type=int, default=30)
    for command in (backup, verify, restore, retention):
        command.add_argument("--environment", required=True)
    args = parser.parse_args()
    try:
        if args.command == "backup":
            package = create_backup(args.db, args.destination, environment=args.environment,
                                    revision=args.revision)
            print(json.dumps({"result": "verified", "package": str(package)}))
        elif args.command == "verify":
            manifest = validate_backup(args.package, environment=args.environment)
            print(json.dumps({key: manifest[key] for key in
                              ("result", "created_at", "revision", "size", "sha256")}))
        elif args.command == "retention-plan":
            print(json.dumps(retention_plan(args.destination, environment=args.environment,
                                            keep_min=args.keep_min, max_age_days=args.max_age_days)))
        else:
            print(json.dumps(restore_backup(args.package, args.db, environment=args.environment,
                                           schema_from=args.schema_from,
                                           service_stopped=args.service_stopped)))
    except (RecoveryError, OSError, sqlite3.Error) as exc:
        # Los errores SQLite o de sistema pueden contener datos/rutas sensibles.
        parser.exit(1, "Recuperación fallida: " + (str(exc) if isinstance(exc, RecoveryError)
                                                else type(exc).__name__) + "\n")


if __name__ == "__main__":
    main()
