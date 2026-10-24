"""Entrada local de clave existente; custodia temporal DPAPI, sin secretos en logs.

No cambia Railway ni escribe plaintext. Solo acepta una clave que autentique
una copia historica productiva descargada con la identidad existente.
"""
import base64
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import uuid
from zipfile import ZipFile


class Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_byte))]


def dpapi(data, *, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError('windows_required')
    raw = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(raw, ctypes.POINTER(ctypes.c_byte)))
    extra = ctypes.create_string_buffer(b'ElHeraldo:issue23:keyhandoff:v1')
    entropy = Blob(len(extra.raw) - 1, ctypes.cast(extra, ctypes.POINTER(ctypes.c_byte)))
    result = Blob()
    api = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    fn = api.CryptUnprotectData if decrypt else api.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob),
                   ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fn.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not fn(ctypes.byref(source), None, ctypes.byref(entropy), None, None, 1, ctypes.byref(result)):
        raise RuntimeError('dpapi_failed')
    try:
        return ctypes.string_at(result.data, result.size)
    finally:
        kernel.LocalFree(result.data)


def encrypted_temp():
    """Solo ciphertext DPAPI y recibos administrativos; nunca plaintext SQLite/clave."""
    # mkdtemp(mode=0700) en Python/Windows quita acceso al AppContainer actual.
    # Heredar la carpeta temporal autorizada: aqui solo se guarda ciphertext.
    # TEMP/LOCALAPPDATA del AppContainer cambian entre llamadas de herramientas.
    # Usar la raiz temporal Windows expresamente autorizada y estable.
    parent = (Path.home() / 'AppData/Local/Temp') if os.name == 'nt' else Path(tempfile.gettempdir())
    root = parent / ('ElHeraldoIssue23-' + uuid.uuid4().hex)
    root.mkdir()
    return root


def authenticate_key(encoded, candidates, t):
    key = base64.b64decode(encoded.strip(), altchars=b'-_', validate=True)
    if len(key) != 32:
        raise ValueError('key_length')
    for name, blob in candidates:
        try:
            if not blob.startswith(t.PREFIX):
                continue
            raw = t.AESGCM(key).decrypt(blob[len(t.PREFIX):len(t.PREFIX)+12],
                                       blob[len(t.PREFIX)+12:], t.AAD)
            with ZipFile(io.BytesIO(raw)) as archive:
                if sorted(archive.namelist()) != ['database.sqlite', 'manifest.json']:
                    continue
                if (archive.getinfo('database.sqlite').file_size > 150_000_000
                        or archive.getinfo('manifest.json').file_size > 1_000_000):
                    continue
                manifest = json.loads(archive.read('manifest.json'))
                if (manifest.get('environment') != 'heraldo-production'
                        or manifest.get('result') != 'verified'
                        or hashlib.sha256(archive.read('database.sqlite')).hexdigest() != manifest['sha256']):
                    continue
            return key, name, hashlib.sha256(blob).hexdigest()
        except Exception:
            continue
    raise ValueError('no_authenticated_production_match')


PAGE = '''<!doctype html><html lang="es"><meta charset="utf-8"><title>El Heraldo: recuperar clave</title>
<style>body{font:18px system-ui;max-width:700px;margin:4em auto;padding:20px}input,button{font:inherit;padding:12px;width:100%;box-sizing:border-box;margin:10px 0}#status{white-space:pre-wrap}</style>
<h1>Recuperar la clave existente de El Heraldo</h1>
<p>Copie desde KeePassXC la clave AES-256-GCM del respaldo productivo. No introduzca la contraseña maestra de la bóveda.</p>
<p>Se comprobará contra una copia histórica cifrada. La clave quedará protegida temporalmente por Windows para este usuario. Esta pantalla no activa producción.</p>
<form autocomplete="off"><label for="key">Clave del respaldo (base64url)</label><input id="key" type="password" maxlength="128" autocomplete="new-password" required><button>Comprobar y proteger clave</button></form><p id="status">Esperando la clave recuperada de la memoria USB.</p>
<script nonce="TOKEN">document.querySelector('form').onsubmit=async e=>{e.preventDefault();let input=document.querySelector('#key'),key=input.value.trim();input.value='';let button=document.querySelector('button');button.disabled=true;try{let r=await fetch('/recover',{method:'POST',headers:{'Content-Type':'application/json','X-Local-Key':'TOKEN'},body:JSON.stringify({key})});key='';let v=await r.json();document.querySelector('#status').textContent=v.ok?'VERIFICADO. La clave autentica una copia productiva y quedó protegida por Windows. Puede cerrar esta página y avisar a ChatGPT.':'No se ha aceptado la clave. Compruebe que es la clave del respaldo productivo.';if(!v.ok)button.disabled=false;}catch{document.querySelector('#status').textContent='No se pudo completar. Avise a ChatGPT.';button.disabled=false;}finally{key='';}};</script></html>'''


def local_server(handler):
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    server.daemon_threads = True
    return server


def main():
    helper = Path(__file__).resolve().parents[2] / 'backup-tools'
    sys.path.insert(0, str(helper))
    import transfer_secure as t
    t.TEST = ['--project', '747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61',
              '--environment', '71b77daf-9092-4af0-913f-32c57367fff3',
              '--service', '055a2bc8-0a0a-4455-8c6c-1ec0a84564bb']
    headers, _ = t.auth()
    _, listing = t.http('/storage/v1/object/list/' + t.BUCKET,
                        {**headers, 'Content-Type': 'application/json'}, 'POST',
                        json.dumps({'prefix': 'heraldo-production/20261018', 'limit': 100}).encode())
    candidates = []
    for item in json.loads(listing):
        if not item['name'].endswith('.h03e') or '/' in item['name']:
            continue
        name = 'heraldo-production/20261018/' + item['name']
        _, blob = t.http('/storage/v1/object/' + t.BUCKET + '/' + name, headers)
        candidates.append((name, blob))
    if not candidates:
        raise RuntimeError('historical_ciphertext_missing')
    root = encrypted_temp()
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self, *args):
            pass

        def respond(self, status, body, mime):
            self.send_response(status)
            for k, v in {'Content-Type': mime, 'Content-Length': str(len(body)),
                         'Cache-Control': 'no-store', 'X-Frame-Options': 'DENY',
                         'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
                         'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-" + token + "'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'"}.items():
                self.send_header(k, v)
            self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            if self.path != '/key/' + token or self.headers.get('Host') != server.host:
                self.respond(404, b'', 'text/plain'); return
            self.respond(200, PAGE.replace('TOKEN', token).encode(), 'text/html; charset=utf-8')

        def do_POST(self):
            if (self.path != '/recover' or self.headers.get('Host') != server.host
                    or self.headers.get('Origin') != 'http://' + server.host
                    or not secrets.compare_digest(self.headers.get('X-Local-Key', ''), token)):
                self.respond(403, b'{"ok":false}', 'application/json'); return
            ok = False
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 1024:
                    raise ValueError('length')
                supplied = json.loads(self.rfile.read(length))
                key, name, checksum = authenticate_key(supplied.pop('key'), candidates, t)
                protected = dpapi(key)
                if dpapi(protected, decrypt=True) != key:
                    raise RuntimeError('dpapi_roundtrip_failed')
                del key
                with (root / 'key.dpapi').open('xb') as f:
                    f.write(protected)
                receipt = {'source': 'usb_keepass', 'gcm_authenticated': True,
                           'historical_object': name, 'ciphertext_sha256': checksum,
                           'verified_at': datetime.now(timezone.utc).isoformat(),
                           'key_at_rest': 'Windows-DPAPI-current-user', 'production_changed': False}
                (root / 'custody-receipt.json').write_text(json.dumps(receipt))
                ok = True
                print('ISSUE23_KEY_CUSTODY VERIFIED plaintext_saved=false production_changed=false', flush=True)
            except Exception:
                print('ISSUE23_KEY_CUSTODY BLOCKED no_sensitive_output=true', flush=True)
            self.respond(200, json.dumps({'ok': ok}).encode(), 'application/json')
            if ok:
                threading.Thread(target=server.shutdown, daemon=True).start()

    # Los navegadores pueden abrir sockets anticipados sin enviar peticion.
    # Un socket asi no debe bloquear ni la pagina ni la entrega de la clave.
    server = local_server(Handler)
    server.host = '127.0.0.1:' + str(server.server_port)
    (root / 'ready.json').write_text(json.dumps({'url': 'http://' + server.host + '/key/' + token}))
    print('ISSUE23_KEY_PAGE_READY directory=' + str(root), flush=True)
    expiry = threading.Timer(900, server.shutdown)
    expiry.daemon = True
    expiry.start()
    try:
        server.serve_forever()
    finally:
        expiry.cancel()
        server.server_close()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ISSUE23_KEY_CUSTODY BLOCKED reason=' + type(exc).__name__, flush=True)
        sys.exit(1)
