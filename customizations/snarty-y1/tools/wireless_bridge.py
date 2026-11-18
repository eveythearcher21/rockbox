#!/usr/bin/env python3
"""Paired LAN bridge for SNARTY Y1. No Google credentials are sent to the player.

Serve a prepared Syncer export, or prepare one with the optional YouTube adapter.
Files are immutable SHA256 objects; manifests/requests are HMAC authenticated.
The protocol transfers playable files and existing metadata, never relabels MP3 as video.
"""
import argparse
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import shutil
import threading
import time
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath

AUDIO = {'.mp3', '.flac', '.m4a', '.ogg', '.opus', '.wav'}
MAX_FILE = 2 * 1024**3


def valid_path(name):
    p = PurePosixPath(name)
    if (len(name.encode('utf-8')) > 239 or str(p) != name or p.is_absolute() or
        any(c in name for c in '\\:*?"<>|') or any(ord(c) < 32 or ord(c) == 127 for c in name) or
        any(x in ('', '.', '..') or x.endswith(('.', ' ')) for x in name.split('/'))):
        raise ValueError('Unsafe device path: ' + repr(name))
    lower = name.lower()
    allowed = bool(name.startswith('Music/') and re.search(r'\.(mp3|flac|m4a|ogg|opus|wav|lrc|lrc8|txt|jpg|jpeg|bmp|radio\.m3u8|lyrics\.meta\.json)$', lower))
    allowed |= (name.startswith('Artist_Images/') and len(p.parts) == 2 and p.suffix.lower() in {'.jpg', '.jpeg', '.bmp', '.png', '.webp'})
    allowed |= name.startswith('Playlists/') and p.suffix.lower() in {'.m3u', '.m3u8'}
    allowed |= name == '.rockbox/snarty/library-v1.bin'
    if not allowed:
        raise ValueError('Not a managed music/art/playlist file: ' + name)
    return name


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def snapshot(root, cache):
    root, cache = Path(root).resolve(), Path(cache).resolve()
    if cache == root or root in cache.parents:
        raise ValueError('Object cache must be outside the exported drive folder')
    cache.mkdir(parents=True, exist_ok=True)
    index_file=cache.parent/'snapshot-index.json'
    try:
        previous=json.loads(index_file.read_text('utf-8'))
    except (OSError,ValueError):
        previous={}
    updated={}
    files, seen, paths = [], set(), set()
    for parent in ('Music', 'Artist_Images', 'Playlists', '.rockbox/snarty'):
        directory = root / parent
        if not directory.exists():
            continue
        for file in sorted(directory.rglob('*')):
            if file.is_symlink() or root not in file.resolve().parents:
                raise ValueError('Export cannot contain symbolic links')
            if not file.is_file():
                continue
            name = file.relative_to(root).as_posix()
            # The bridge must never export account files, settings, local history, favorites,
            # pairing secrets, caches, listening journals or arbitrary .rockbox plugins.
            if name.startswith('.rockbox/') and name != '.rockbox/snarty/library-v1.bin':
                continue
            try:
                valid_path(name)
            except ValueError:
                # Ignore unrelated exporter work/temp files, but reject unsafe eligible paths.
                if file.suffix.lower() in AUDIO | {'.lrc', '.lrc8', '.txt', '.jpg', '.jpeg', '.bmp', '.png', '.webp', '.m3u', '.m3u8', '.bin'}:
                    raise
                continue
            collision = unicodedata.normalize('NFC', name).casefold()
            if collision in seen:
                raise ValueError('Case/Unicode path collision: ' + name)
            seen.add(collision)
            info=file.stat()
            size = info.st_size
            if not 0 < size <= MAX_FILE:
                raise ValueError('Empty/oversized sync file: ' + name)
            fingerprint=[size,info.st_mtime_ns,info.st_ctime_ns,info.st_ino]
            identity=str(root)+'/'+name
            old=previous.get(identity,{})
            sha=old.get('sha256','')
            if not (old.get('fingerprint')==fingerprint and re.fullmatch('[a-f0-9]{64}',sha) and (cache/sha).is_file() and (cache/sha).stat().st_size==size):
                digest=hashlib.sha256()
                with file.open('rb') as source:
                    while chunk:=source.read(65536):digest.update(chunk)
                sha=digest.hexdigest()
                target=cache/sha
                if not target.is_file() or target.stat().st_size!=size:
                    temp=cache/(secrets.token_hex(12)+'.tmp')
                    verify=hashlib.sha256()
                    try:
                        with file.open('rb') as source,temp.open('wb') as output:
                            while chunk:=source.read(65536):verify.update(chunk);output.write(chunk)
                            output.flush();os.fsync(output.fileno())
                        if temp.stat().st_size!=size or verify.hexdigest()!=sha:
                            raise ValueError('Export changed while building snapshot')
                        os.replace(temp,target)
                    finally:temp.unlink(missing_ok=True)
            updated[identity]={'fingerprint':fingerprint,'sha256':sha}
            files.append({'path': name, 'size': size, 'sha256': sha})
            paths.add(name)
    if len(files) > 20000:
        raise ValueError('More than 20000 sync files; split this export')
    for entry in files:
        if not entry['path'].lower().endswith(('.m3u', '.m3u8')):
            continue
        for line in (cache / entry['sha256']).read_text('utf-8-sig').splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            # Prepared exports must reference their matching final /sdcard music paths.
            if not line.startswith('/sdcard/') or line[8:] not in paths or PurePosixPath(line).suffix.lower() not in AUDIO:
                raise ValueError('Playlist references missing/non-local audio: ' + entry['path'])
    missing = sum(1 for p in paths if PurePosixPath(p).suffix.lower() in AUDIO and
                  not any(str(PurePosixPath(p).with_suffix(ext)) in paths for ext in ('.lrc', '.lrc8', '.txt')))
    report = {}
    report_path = root / 'wireless-source-report.json'
    if report_path.is_file():
        report = json.loads(report_path.read_text('utf-8'))
    manifest = {'version': 1, 'files': sorted(files, key=lambda f: f['path']),
                'missing_lyrics': missing, 'missing_artist_images': report.get('missing_artist_images', -1),
                'source': report.get('source', 'prepared-syncer-export'),
                'metadata_gaps': sum(bool(w.get('missing_metadata')) for w in report.get('warnings', [])) if report else -1,
                'source_warnings': report.get('warnings', [])}
    generation = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    manifest['generation'] = generation
    encoded = json.dumps(manifest, separators=(',', ':'), ensure_ascii=False).encode()
    if len(encoded) > 8 * 1024**2:
        raise ValueError('Sync manifest too large')
    atomic(index_file,json.dumps(updated,separators=(',',':')).encode())
    return encoded


class Bridge:
    def __init__(self, export, cache, key, refresh=None):
        self.export, self.cache, self.key = Path(export), Path(cache), key
        self.refresh_source = refresh
        self.lock = threading.Lock()
        self.nonces = {}
        self.manifest = None
        self.busy = False
        self.error = None
        self.last_refresh = 0

    def authenticate(self, path, nonce, auth):
        if not re.fullmatch('[a-f0-9]{32}', nonce or ''):
            return False
        expected = hmac.new(self.key, f'GET\n{path}\n{nonce}'.encode(), 'sha256').hexdigest()
        if not hmac.compare_digest(expected, auth or ''):
            return False
        with self.lock:
            now = time.monotonic()
            self.nonces = {k: v for k, v in self.nonces.items() if now-v < 600}
            if nonce in self.nonces or len(self.nonces) >= 100000:
                return False
            self.nonces[nonce] = now
        return True

    def prepare(self, force=False):
        with self.lock:
            if self.busy or not force and (self.manifest or self.error) and time.monotonic()-self.last_refresh < 300:
                return
            self.busy = True

        def work():
            try:
                if self.refresh_source:
                    self.refresh_source()
                body = snapshot(self.export, self.cache)
                with self.lock:
                    self.manifest = body
                    self.error = None
                    self.last_refresh = time.monotonic()
                print('Library prepared:', len(json.loads(body)['files']), 'files', flush=True)
            except Exception as e:
                # Keep details on the computer; never serve a new/partial source generation.
                with self.lock:
                    self.error = type(e).__name__
                    self.last_refresh = time.monotonic()
                print('Source refresh failed. Check account/export and retry. Error type:', type(e).__name__, flush=True)
                if isinstance(e, (ValueError, FileNotFoundError)):
                    print('Export/setup issue:', str(e), flush=True)
            finally:
                with self.lock:
                    self.busy = False
        threading.Thread(target=work, name='Source library refresh', daemon=True).start()

    def handler(self):
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass  # no pairing headers/account/source URLs in access logs

            def do_GET(self):
                nonce = self.headers.get('X-Snarty-Nonce')
                if not bridge.authenticate(self.path, nonce, self.headers.get('X-Snarty-Auth')):
                    self.send_error(403, 'Pairing required')
                    return
                if self.path == '/v1/manifest':
                    bridge.prepare()
                    with bridge.lock:
                        body, busy, error = bridge.manifest, bridge.busy, bridge.error
                    if busy or body is None:
                        self.send_response(202 if busy else 503)
                        self.end_headers()
                        return
                    if error:
                        self.send_error(503, 'Source refresh failed; check computer')
                        return
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Content-Length', str(len(body)))
                    self.send_header('X-Snarty-Auth', hmac.new(bridge.key, nonce.encode()+b'\n'+body, 'sha256').hexdigest())
                    self.end_headers()
                    self.wfile.write(body)
                elif re.fullmatch('/v1/file/[a-f0-9]{64}', self.path):
                    file = bridge.cache / self.path.rsplit('/', 1)[1]
                    if not file.is_file():
                        self.send_error(404)
                        return
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Length', str(file.stat().st_size))
                    self.end_headers()
                    with file.open('rb') as source:
                        shutil.copyfileobj(source, self.wfile, 65536)
                else:
                    self.send_error(404)
        return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, required=True, help='Drive-shaped Syncer export folder')
    parser.add_argument('--state', type=Path, required=True, help='Private computer-side state, outside export')
    parser.add_argument('--host', default='127.0.0.1', help='Use computer private IPv4 to allow paired Y1')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--pair-url', help='http://COMPUTER-PRIVATE-IP:8787 written into pairing file')
    parser.add_argument('--pair-output', type=Path, help='Write initial wireless-pairing.json here')
    parser.add_argument('--youtube-auth', type=Path, help='Optional desktop-only ytmusicapi browser auth JSON')
    parser.add_argument('--youtube-cookies', type=Path, help='Optional desktop-only yt-dlp Netscape cookies file')
    parser.add_argument('--youtube-oauth-credentials', type=Path, help='Desktop-only JSON with owner OAuth client_id/client_secret, when auth is OAuth')
    args = parser.parse_args()
    try:
        address=ipaddress.ip_address(args.host)
        if address.version!=4 or not any(address in ipaddress.ip_network(n) for n in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','127.0.0.0/8')):
            raise ValueError()
    except ValueError:
        parser.error('--host must be a numeric private/loopback IPv4 address; public/wildcard listeners are refused')
    if args.state.resolve()==args.export.resolve() or args.export.resolve() in args.state.resolve().parents:
        parser.error('Private state must be outside the exported media folder')
    args.state.mkdir(parents=True, exist_ok=True)
    key_file = args.state / 'pairing-key.hex'
    if not key_file.exists():
        atomic(key_file, secrets.token_hex(32).encode())
        try:
            key_file.chmod(0o600)
        except OSError:
            pass
    key = bytes.fromhex(key_file.read_text().strip())
    if len(key) != 32:
        parser.error('Invalid stored pairing key')
    if args.pair_output:
        if not args.pair_url:
            parser.error('--pair-output requires --pair-url')
        atomic(args.pair_output, json.dumps({'version': 1, 'url': args.pair_url, 'key': key.hex()}).encode())
        print('Pairing file written. Copy it once to .rockbox/snarty/wireless-pairing.json on Y1.')
    refresh = None
    if args.youtube_auth:
        from youtube_wireless import prepare_youtube
        refresh = lambda: prepare_youtube(args.youtube_auth, args.export, args.state / 'youtube', cookies=args.youtube_cookies, oauth_credentials=args.youtube_oauth_credentials)
    bridge = Bridge(args.export, args.state / 'objects', key, refresh)
    bridge.prepare(force=True)
    server = ThreadingHTTPServer((args.host, args.port), bridge.handler())
    print(f'Paired sync bridge listening on {args.host}:{args.port}; keep this computer running.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
