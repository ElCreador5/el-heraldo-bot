"""Identidad y comprobaciones locales exclusivas de Enzonic Test; sin Gateway.

No sustituye identidades Railway ni contiene credenciales. Las pruebas de
persistencia y recuperación son recibos privados en el volumen real.
"""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from urllib.request import Request, urlopen

ROOT = Path("/home/container")
DATABASE = ROOT / "heraldo.db"
STATE = ROOT / ".heraldo-h03-enzonic"
ENVIRONMENT = "heraldo-test"
DISK_CAP_BYTES = 1_000_000_000  # Conservador: 1 GB incluye código y dependencias.
TEST_PROJECT = "747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61"
SUPABASE_URL = "https://bzomavqthjhnukmaqocc.supabase.co"
# Huella de la identidad Auth permitida por las políticas Test comprobadas.
TEST_UID_SHA256 = "823b53eb795d71a033144ff8055692b63780478f98d0d8bba3fb9904e172552a"
# Identidad pública corroborada en los logs originales de Railway Test.
TEST_BOT_TAG = "El Heraldo's Lab 🧪#6700"
FLAG = "HERALDO_ENZONIC_BACKUP_ENABLED"
FLAG_VALUE = "enabled-after-validation"


def is_enzonic():
    return (os.environ.get("HERALDO_HOSTING_PROVIDER") == "enzonic"
            or Path(__file__).resolve().parent == Path("/home/container"))


def is_test():
    if is_enzonic():
        return os.environ.get("HERALDO_ENVIRONMENT") == ENVIRONMENT
    return os.environ.get("RAILWAY_PROJECT_ID") == TEST_PROJECT


def blocked(reason):
    from backup_job import BackupJobError
    raise BackupJobError(reason)


def provider_preflight():
    if (os.environ.get("HERALDO_HOSTING_PROVIDER") != "enzonic"
            or os.environ.get("HERALDO_ENVIRONMENT") != ENVIRONMENT):
        blocked("enzonic_identity_mismatch")
    if any(name.startswith("RAILWAY_") for name in os.environ):
        blocked("stale_railway_variables")
    for name in ("HERALDO_TEST_BACKUP_ENABLED", "HERALDO_PRODUCTION_BACKUP_ENABLED",
                 "HERALDO_H03_STARTUP_GATE", "HERALDO_BACKUP_VOLUME_CAP_MB"):
        if name in os.environ:
            blocked("legacy_backup_variable_present")
    if os.environ.get("DB_PATH") != str(DATABASE):
        blocked("enzonic_database_path_mismatch")
    if (ROOT.is_symlink() or not ROOT.is_dir() or ROOT.resolve() != ROOT
            or not ROOT.is_mount()):
        blocked("enzonic_persistent_mount_missing")
    if STATE.is_symlink() or STATE.resolve() != STATE:
        blocked("enzonic_state_path_mismatch")


def check_test_secrets():
    from supabase_backup import _config, _key
    base, public_key, _, _, uid = _config()
    if base != SUPABASE_URL or hashlib.sha256(uid.encode()).hexdigest() != TEST_UID_SHA256:
        blocked("enzonic_test_storage_identity_mismatch")
    if not public_key.startswith("sb_publishable_"):
        try:
            body = public_key.split(".")[1]
            role = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))["role"]
        except (ValueError, KeyError, IndexError, TypeError):
            blocked("invalid_test_publishable_key")
        if role != "anon":
            blocked("privileged_test_key_forbidden")
    _key()


def _github_metadata(path):
    """Lee solo metadatos públicos de la rama Test, con tamaño y tiempo acotados."""
    url = "https://api.github.com/repos/ElCreador5/el-heraldo-bot/" + path
    try:
        request = Request(url, headers={"Accept": "application/vnd.github+json",
                                        "User-Agent": "ElHeraldo-Enzonic-Test/1.0"})
        with urlopen(request, timeout=10) as response:
            payload = response.read(512 * 1024 + 1)
        if len(payload) > 512 * 1024:
            blocked("enzonic_checkout_unverified")
        return json.loads(payload)
    except (OSError, ValueError, TimeoutError):
        blocked("enzonic_checkout_unverified")


def _git_blob_sha(path, size):
    """Huella de los bytes en disco, equivalente al SHA de blob Git."""
    if (not path.is_file() or path.is_symlink() or path.resolve() != path
            or size < 0 or size > 32 * 1024 * 1024 or path.stat().st_size != size):
        blocked("enzonic_checkout_unverified")
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(128 * 1024):
                digest.update(chunk)
    except OSError:
        blocked("enzonic_checkout_unverified")
    return digest.hexdigest()


def _verified_github_deployment():
    """Enzonic puede copiar archivos sin mover HEAD: verificar TODOS los blobs.

    No hace reset, pull ni modificaciones de Git/SQLite. Si un solo archivo
    difiere del árbol publicado en Pruebas, el arranque sigue bloqueado.
    """
    info = _github_metadata("commits/Pruebas")
    commit_sha = info.get("sha") if isinstance(info, dict) else None
    tree = (info.get("commit") or {}).get("tree") if isinstance(info, dict) else None
    tree_sha = tree.get("sha") if isinstance(tree, dict) else None
    if not (isinstance(commit_sha, str) and re.fullmatch(r"[0-9a-f]{40}", commit_sha)
            and isinstance(tree_sha, str) and re.fullmatch(r"[0-9a-f]{40}", tree_sha)):
        blocked("enzonic_checkout_unverified")
    listing = _github_metadata("git/trees/" + tree_sha + "?recursive=1")
    if (not isinstance(listing, dict) or listing.get("sha") != tree_sha
            or listing.get("truncated") is not False
            or not isinstance(listing.get("tree"), list)):
        blocked("enzonic_checkout_unverified")
    tracked = set()
    total_size = 0
    for item in listing["tree"]:
        if not isinstance(item, dict):
            blocked("enzonic_checkout_unverified")
        if item.get("type") == "tree":
            continue
        name, sha, size = item.get("path"), item.get("sha"), item.get("size")
        if (item.get("type") != "blob" or item.get("mode") not in ("100644", "100755")
                or not isinstance(name, str) or not name or name.startswith("/")
                or "\\" in name or ".." in Path(name).parts or name == ".git"
                or name.startswith(".git/") or name in tracked
                or not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha)
                or type(size) is not int or size < 0):
            blocked("enzonic_checkout_unverified")
        tracked.add(name)
        total_size += size
        if len(tracked) > 10000 or total_size > 64 * 1024 * 1024:
            blocked("enzonic_checkout_unverified")
        if _git_blob_sha(ROOT / name, size) != sha:
            blocked("enzonic_checkout_unverified")
    if not tracked or "bot.py" not in tracked or "enzonic_test_host.py" not in tracked:
        blocked("enzonic_checkout_unverified")
    return commit_sha


def _trusted_origin_url(remote):
    """Evita verificar un árbol obtenido de un repositorio distinto."""
    return bool(re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
        r"ElCreador5/el-heraldo-bot(?:\.git)?/?",
        remote, flags=re.IGNORECASE,
    ))


def _verified_git_deployment():
    """Verifica la superposición de Enzonic usando Git, sin API REST ni reset.

    Git valida criptográficamente los objetos descargados. La operación fetch
    solo actualiza FETCH_HEAD y objetos internos, no los archivos ni SQLite.
    """
    def git(*args, timeout=30):
        try:
            result = subprocess.run(
                ["git", "-C", str(ROOT), *args],
                capture_output=True, timeout=timeout, check=False,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
        except (OSError, subprocess.TimeoutExpired):
            blocked("enzonic_checkout_unverified")
        if result.returncode != 0:
            blocked("enzonic_checkout_unverified")
        return result.stdout.decode("utf-8", errors="strict").strip()

    origin = git("remote", "get-url", "origin", timeout=8)
    if not _trusted_origin_url(origin):
        blocked("enzonic_checkout_unverified")
    git("fetch", "--no-tags", "--depth=1", "origin", "refs/heads/Pruebas", timeout=45)
    commit_sha = git("rev-parse", "--verify", "FETCH_HEAD^{commit}", timeout=8)
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        blocked("enzonic_checkout_unverified")
    listing = git("ls-tree", "-r", "-l", "-z", commit_sha, timeout=10)
    if not listing:
        blocked("enzonic_checkout_unverified")
    tracked = set()
    total_size = 0
    for item in listing.split("\x00"):
        if not item:
            continue
        try:
            metadata, name = item.split("\t", 1)
        except ValueError:
            blocked("enzonic_checkout_unverified")
        match = re.fullmatch(r"(100644|100755) blob ([0-9a-f]{40}) ([0-9]+)", metadata)
        if match is None:
            blocked("enzonic_checkout_unverified")
        sha, size = match.group(2), int(match.group(3))
        if (not name or name.startswith("/") or "\\" in name
                or ".." in Path(name).parts or name == ".git"
                or name.startswith(".git/") or name in tracked):
            blocked("enzonic_checkout_unverified")
        tracked.add(name)
        total_size += size
        if len(tracked) > 10000 or total_size > 64 * 1024 * 1024:
            blocked("enzonic_checkout_unverified")
        if _git_blob_sha(ROOT / name, size) != sha:
            blocked("enzonic_checkout_unverified")
    if not tracked or "bot.py" not in tracked or "enzonic_test_host.py" not in tracked:
        blocked("enzonic_checkout_unverified")
    return commit_sha


def revision():
    """Solo acepta Pruebas limpio o archivos íntegros del despliegue GitHub."""
    def git(*args, allowed=(0,)):
        try:
            result = subprocess.run(["git", "-C", str(ROOT), *args],
                                    capture_output=True, timeout=8, check=False)
        except (OSError, subprocess.TimeoutExpired):
            blocked("enzonic_checkout_unverified")
        if result.returncode not in allowed:
            blocked("enzonic_checkout_unverified")
        return result
    if git("rev-parse", "--show-toplevel").stdout.decode("ascii").strip() != str(ROOT):
        blocked("enzonic_checkout_unverified")
    if git("symbolic-ref", "--short", "HEAD").stdout.decode("ascii").strip() != "Pruebas":
        blocked("enzonic_wrong_branch")
    value = git("rev-parse", "HEAD").stdout.decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        blocked("enzonic_checkout_unverified")
    dirty = git("diff", "--quiet", "HEAD", "--", allowed=(0, 1)).returncode
    if not dirty:
        return value
    # GitHub Deploy puede superponer archivos con HEAD antiguo. Preferir Git
    # para no depender de la cuota REST de api.github.com en cada reinicio.
    try:
        return _verified_git_deployment()
    except Exception as exc:
        from backup_job import BackupJobError
        if not isinstance(exc, BackupJobError):
            raise
        # Compatibilidad con instalaciones que carecen de remote Git.
        return _verified_github_deployment()

def private_state():
    from backup_job import _private_root
    return _private_root(STATE)


def read_receipt(name):
    path = STATE / name
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "r") as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) & 0o077 or info.st_size > 65536):
                blocked("enzonic_receipt_not_private")
            value = json.load(stream)
        if not isinstance(value, dict):
            blocked("enzonic_invalid_receipt")
        return value
    except (OSError, ValueError):
        blocked("enzonic_receipt_missing_or_invalid")


def write_receipt(name, value):
    from backup_job import _write_receipt
    root = private_state()
    path = root / name
    _write_receipt(path, value, initial=not path.exists())


def runtime_instance():
    # A new PID namespace / PID 1 start time proves an actual container restart.
    # No process arguments or environment contents are read or logged.
    start = Path("/proc/1/stat").read_text().rsplit(")", 1)[1].split()[19]
    value = os.readlink("/proc/1/ns/pid") + ":" + start
    return hashlib.sha256(value.encode()).hexdigest()


def persistence_probe(action):
    provider_preflight()
    private_state()
    path = STATE / "persistence.json"
    if action == "prepare":
        if path.exists() or path.is_symlink():
            blocked("persistence_probe_already_exists")
        write_receipt("persistence.json", {"status": "pending_restart",
                      "environment": ENVIRONMENT, "initial_instance": runtime_instance(),
                      "marker": os.urandom(16).hex()})
        return "RESTART_REQUIRED"
    record = read_receipt("persistence.json")
    if (record.get("environment") != ENVIRONMENT
            or not re.fullmatch(r"[0-9a-f]{32}", record.get("marker", ""))):
        blocked("persistence_probe_invalid")
    if record.get("status") == "verified_after_restart":
        return "VERIFIED_AFTER_RESTART"
    if record.get("status") != "pending_restart" or record.get("initial_instance") == runtime_instance():
        blocked("container_restart_not_observed")
    record.update(status="verified_after_restart", verified_at=datetime.now(timezone.utc).isoformat())
    write_receipt("persistence.json", record)
    return "VERIFIED_AFTER_RESTART"


def require_persistence():
    if read_receipt("persistence.json").get("status") != "verified_after_restart":
        blocked("enzonic_persistence_not_verified")


def require_restored_database():
    from sqlite_recovery import inspect_database
    record = read_receipt("migration.json")
    if (record.get("status") != "verified_and_installed"
            or record.get("environment") != ENVIRONMENT
            or not re.fullmatch(r"[0-9a-f]{64}", record.get("sqlite_sha256", ""))):
        blocked("enzonic_migration_not_verified")
    if (DATABASE.is_symlink() or not DATABASE.is_file()
            or stat.S_IMODE(DATABASE.stat().st_mode) & 0o077):
        blocked("enzonic_database_not_private")
    actual = inspect_database(DATABASE)
    if actual["schema_sha256"] != record.get("schema_sha256"):
        blocked("enzonic_restored_schema_mismatch")


def guard(source, state_root):
    provider_preflight()
    if Path(source) != DATABASE or Path(state_root) != STATE:
        blocked("enzonic_backup_path_mismatch")
    require_persistence()
    require_restored_database()
    check_test_secrets()


def remaining_space(root):
    import shutil
    if Path(root).resolve() != STATE:
        blocked("enzonic_budget_path_mismatch")
    occupied = 0
    for path in ROOT.rglob("*"):
        info = path.lstat()
        if stat.S_ISREG(info.st_mode):
            occupied += info.st_size
    return min(shutil.disk_usage(ROOT).free, max(0, DISK_CAP_BYTES - occupied))


def verify_test_token():
    """GET sin Gateway. Comprueba la cuenta original, sin revelar el token."""
    from supabase_backup import _http
    provider_preflight()
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        blocked("enzonic_test_token_missing")
    raw = _http("https://discord.com/api/v10/users/@me", method="GET",
                headers={"Authorization": "Bot " + token,
                         "User-Agent": "ElHeraldo-EnzonicMigration/1.0"}, limit=8192)
    value = json.loads(raw)
    tag = str(value.get("username")) + "#" + str(value.get("discriminator"))
    if (value.get("bot") is not True or tag != TEST_BOT_TAG
            or not re.fullmatch(r"[0-9]{17,20}", value.get("id", ""))):
        blocked("enzonic_wrong_discord_bot")
    record_path = STATE / "discord-identity.json"
    if record_path.exists() or record_path.is_symlink():
        if read_receipt(record_path.name).get("bot_id") != value["id"]:
            blocked("enzonic_discord_identity_changed")
    else:
        write_receipt(record_path.name, {"status": "verified", "bot_id": value["id"]})


def before_discord():
    if not is_enzonic():
        return
    provider_preflight()
    require_persistence()
    require_restored_database()
    revision()
    verify_test_token()


def refuse_legacy_test_start():
    """Un push a Pruebas no debe reactivar el segundo Gateway en Railway Test."""
    if os.environ.get("RAILWAY_PROJECT_ID") == TEST_PROJECT and not is_enzonic():
        print("HERALDO_TEST status=STOPPED reason=ENZONIC_MIGRATION", flush=True)
        raise SystemExit(0)
