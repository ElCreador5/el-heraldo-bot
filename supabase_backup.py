"""Respaldo H-03 cifrado en Supabase Storage privado. Herramienta offline, nunca inicia Discord.

Requiere una identidad de Auth exclusiva, RLS limitada al bucket, y secretos
inyectados por el operador. No se activa automáticamente al importar el bot.
"""
import argparse
import base64
from contextlib import contextmanager
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib import error, parse, request
import uuid
from zipfile import ZipFile, ZIP_DEFLATED

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlite_recovery import validate_backup

BUCKET = "heraldo-sqlite-backups"
PREFIX = b"ELHERALDO-BACKUP-1\x00"
AAD = b"ElHeraldo:H03:Supabase:2026:1"
MAX_UPLOAD_BYTES = 45_000_000  # Margen bajo el limite Free de 50 MB.
MAX_DATABASE_BYTES = 150_000_000


class CloudBackupError(RuntimeError):
    """Fallos saneados, sin URLs completas, claves, filas ni rutas privadas."""


def _key():
    value = os.environ.get("HERALDO_BACKUP_ENCRYPTION_KEY", "")
    try:
        raw = base64.b64decode(value, altchars=b"-_", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise CloudBackupError("encryption_key_invalid") from exc
    if len(raw) != 32:
        raise CloudBackupError("encryption_key_invalid")
    return raw


def _environment(value):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,30}", value):
        raise CloudBackupError("environment_invalid")
    return value


def _object_key(value, environment):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,30}/[0-9]{8}/[0-9a-f]{32}\.h03e", value):
        raise CloudBackupError("object_key_invalid")
    if not value.startswith(environment + "/"):
        raise CloudBackupError("object_environment_mismatch")
    return value


def _bundle(package, environment, encryption_key):
    manifest = validate_backup(package, environment=environment)
    database = Path(package) / "database.sqlite"
    if database.stat().st_size > MAX_DATABASE_BYTES:
        raise CloudBackupError("database_too_large_for_single_object")
    stream = BytesIO()
    with ZipFile(stream, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        archive.write(database, arcname="database.sqlite")
        archive.write(Path(package) / "manifest.json", arcname="manifest.json")
    plaintext = stream.getvalue()
    if len(plaintext) + len(PREFIX) + 12 + 16 > MAX_UPLOAD_BYTES:
        raise CloudBackupError("backup_exceeds_free_upload_limit")
    nonce = os.urandom(12)
    encrypted = PREFIX + nonce + AESGCM(encryption_key).encrypt(nonce, plaintext, AAD)
    return encrypted, manifest


@contextmanager
def _unpack(blob, environment, encryption_key):
    if not blob.startswith(PREFIX) or len(blob) > MAX_UPLOAD_BYTES or len(blob) < len(PREFIX) + 28:
        raise CloudBackupError("encrypted_package_invalid")
    nonce = blob[len(PREFIX):len(PREFIX) + 12]
    try:
        data = AESGCM(encryption_key).decrypt(nonce, blob[len(PREFIX) + 12:], AAD)
    except (ValueError, InvalidTag) as exc:
        raise CloudBackupError("decryption_or_integrity_failed") from exc
    with tempfile.TemporaryDirectory(prefix="heraldo-h03-") as root:
        package = Path(root) / "package"
        package.mkdir(mode=0o700)
        with ZipFile(BytesIO(data)) as archive:
            if set(archive.namelist()) != {"database.sqlite", "manifest.json"}:
                raise CloudBackupError("package_layout_invalid")
            if archive.getinfo("database.sqlite").file_size > MAX_DATABASE_BYTES or archive.getinfo("manifest.json").file_size > 1_000_000:
                raise CloudBackupError("package_expansion_limit")
            for name in ("database.sqlite", "manifest.json"):
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                fd = os.open(package / name, flags, 0o600)
                with os.fdopen(fd, "wb") as output, archive.open(name) as source:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
        validate_backup(package, environment=environment)
        yield package


def _config():
    raw_url = os.environ.get("SUPABASE_BACKUP_URL", "")
    parsed = parse.urlsplit(raw_url)
    if (parsed.scheme != "https" or parsed.port is not None or parsed.username or parsed.password
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment
            or not re.fullmatch(r"[a-z0-9-]+\.supabase\.co", parsed.hostname or "")):
        raise CloudBackupError("project_url_invalid")
    anon = os.environ.get("SUPABASE_BACKUP_PUBLISHABLE_KEY", "")
    email = os.environ.get("SUPABASE_BACKUP_EMAIL", "")
    password = os.environ.get("SUPABASE_BACKUP_PASSWORD", "")
    user_id = os.environ.get("SUPABASE_BACKUP_USER_ID", "")
    if not all((anon, email, password)) or not re.fullmatch(r"[0-9a-f-]{36}", user_id):
        raise CloudBackupError("backup_identity_not_configured")
    return raw_url.rstrip("/"), anon, email, password, user_id


def _http(url, *, method, headers, payload=None, limit=MAX_UPLOAD_BYTES):
    try:
        with request.urlopen(request.Request(url, data=payload, headers=headers, method=method),
                             timeout=35) as response:
            if response.status not in (200, 201):
                raise CloudBackupError("storage_request_failed")
            result = response.read(limit + 1)
    except (error.URLError, TimeoutError, OSError) as exc:
        raise CloudBackupError("storage_unavailable_or_unauthorized") from exc
    if len(result) > limit:
        raise CloudBackupError("storage_response_too_large")
    return result


def _session(base_url, anon, email, password, expected_uid):
    payload = json.dumps({"email": email, "password": password}).encode()
    raw = _http(base_url + "/auth/v1/token?grant_type=password", method="POST",
                headers={"apikey": anon, "Content-Type": "application/json"},
                payload=payload, limit=8192)
    try:
        token = json.loads(raw)["access_token"]
        encoded = token.split(".")[1]
        jwt = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        if jwt.get("sub") != expected_uid:
            raise CloudBackupError("unexpected_backup_identity")
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise CloudBackupError("authentication_response_invalid") from exc
    return {"apikey": anon, "Authorization": "Bearer " + token}


def _storage(environment):
    _environment(environment)
    base, anon, email, password, uid = _config()
    return (base + "/storage/v1/object/" + BUCKET + "/",
            _session(base, anon, email, password, uid))


def upload(package, environment):
    environment = _environment(environment)
    key = _key()
    blob, manifest = _bundle(package, environment, key)
    remote, headers = _storage(environment)
    object_name = (environment + "/" + manifest["created_at"][:10].replace("-", "") +
                   "/" + uuid.uuid4().hex + ".h03e")
    _http(remote + parse.quote(object_name, safe="/"), method="POST",
          headers={**headers, "Content-Type": "application/octet-stream",
                   "Cache-Control": "no-store", "x-upsert": "false"},
          payload=blob, limit=8192)
    return {"status": "uploaded", "object": object_name,
            "plaintext_sha256": manifest["sha256"], "encrypted_bytes": len(blob)}


def download_verify(object_name, environment, destination=None):
    environment = _environment(environment)
    name = _object_key(object_name, environment)
    secret = _key()
    remote, headers = _storage(environment)
    blob = _http(remote + parse.quote(name, safe="/"), method="GET",
                 headers=headers, limit=MAX_UPLOAD_BYTES)
    with _unpack(blob, environment, secret) as package:
        manifest = validate_backup(package, environment=environment)
        result = {"status": "verified", "object": name, "plaintext_sha256": manifest["sha256"]}
        if destination is not None:
            target_root = Path(destination)
            if target_root.is_symlink():
                raise CloudBackupError("destination_symlink")
            target_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            if target_root.stat().st_mode & 0o077:
                raise CloudBackupError("destination_not_private")
            target = target_root / ("h03-" + uuid.uuid4().hex)
            shutil.copytree(package, target)
            os.chmod(target, 0o700)
            validate_backup(target, environment=environment)
            result["local_package"] = str(target)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Subida cifrada H-03 y verificacion remota; sin iniciar el bot")
    sub = parser.add_subparsers(dest="action", required=True)
    put = sub.add_parser("upload")
    put.add_argument("--package", required=True)
    get = sub.add_parser("verify-remote")
    get.add_argument("--object", required=True)
    fetch = sub.add_parser("fetch")
    fetch.add_argument("--object", required=True)
    fetch.add_argument("--destination", required=True)
    for command in (put, get, fetch):
        command.add_argument("--environment", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "upload":
            result = upload(args.package, args.environment)
        else:
            result = download_verify(args.object, args.environment,
                                     destination=args.destination if args.action == "fetch" else None)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (CloudBackupError, OSError, ValueError) as exc:
        # No devolver mensajes del SDK/HTTP ni rutas internas.
        error_code = str(exc) if isinstance(exc, CloudBackupError) else "backup_operation_failed"
        print(json.dumps({"status": "blocked", "reason": error_code}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
