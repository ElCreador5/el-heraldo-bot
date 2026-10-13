"""Ensayo controlado H-03 remoto en contenedor efímero de Railway Test.

No importa bot.py, no usa DB_PATH, no toca Discord ni volumen /data.
No muestra tokens, rutas ni filas; publica solo estados saneados.
La comprobación produce un objeto de laboratorio sin borrar generaciones.
"""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile

from sqlite_recovery import create_backup, restore_backup
from supabase_backup import download_verify, upload, CloudBackupError


def _fixture(path, *, with_rows=False):
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("CREATE TABLE lab_restore (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)")
        if with_rows:
            conn.execute("INSERT INTO lab_restore VALUES (1, 'H03-LAB-SYNTHETIC')")
        conn.commit()


def run():
    if os.environ.get("RAILWAY_PROJECT_ID") != "747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61":
        raise CloudBackupError("railway_project_not_test")
    if os.environ.get("RAILWAY_SERVICE_ID") != "13a555fc-7ddd-4712-a9bc-e88509e18b2b":
        raise CloudBackupError("railway_service_not_test")
    # Prevent importing environment accidentally using a production label.
    environment = "lab"
    with tempfile.TemporaryDirectory(prefix="h03-synthetic-") as directory:
        root = Path(directory)
        source = root / "source.sqlite"
        schema = root / "schema.sqlite"
        restored = root / "restored.sqlite"
        _fixture(source, with_rows=True)
        _fixture(schema)
        generation = create_backup(source, root / "local_generations",
                                   environment=environment, revision="railway-smoke")
        print("H03_SMOKE step=local_backup status=verified", flush=True)
        published = upload(generation, environment)
        print("H03_SMOKE step=encrypted_upload status=verified", flush=True)
        verified = download_verify(published["object"], environment)
        if verified["plaintext_sha256"] != published["plaintext_sha256"]:
            raise CloudBackupError("remote_digest_mismatch")
        print("H03_SMOKE step=remote_download status=verified", flush=True)
        downloaded = download_verify(published["object"], environment,
                                     destination=root / "downloaded_generations")
        if downloaded["plaintext_sha256"] != published["plaintext_sha256"]:
            raise CloudBackupError("download_digest_mismatch")
        restore_backup(downloaded["local_package"], restored, environment=environment,
                       schema_from=schema, service_stopped=True)
        with closing(sqlite3.connect(restored)) as conn:
            rows = conn.execute("SELECT id,marker FROM lab_restore ORDER BY id").fetchall()
        if rows != [(1, "H03-LAB-SYNTHETIC")]:
            raise CloudBackupError("restored_fixture_mismatch")
        print("H03_SMOKE step=isolated_restore status=verified", flush=True)
        print("H03_SMOKE status=PASS scope=synthetic_no_discord", flush=True)


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        # Do not leak full error text (it may embed internal HTTP URLs or filenames).
        category = str(exc) if type(exc) is CloudBackupError else type(exc).__name__
        if not category.replace("_", "").isalnum():
            category = type(exc).__name__
        print("H03_SMOKE status=FAIL reason=" + category, flush=True)
        raise SystemExit(1)
