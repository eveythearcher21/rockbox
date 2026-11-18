#!/usr/bin/env python3
"""Real Java<->Python HTTP/HMAC transfers; no YouTube account/hardware claims."""
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer

repo = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo/'customizations/snarty-y1/tools'))
from wireless_bridge import Bridge, snapshot, valid_path
from compile_sync_library import encode_library
work = Path(tempfile.mkdtemp(prefix='snarty-wireless-'))
jar = Path(os.environ.get('SNARTY_JSON_JAR','/workspace/setup/wireless-tests/json.jar'))
subprocess.run(['javac','-cp',str(jar),'-d',str(work),*[str(repo/'android/y1/src/org/rockbox'/n) for n in ('WirelessProtocol.java','WirelessSync.java')],str(Path(__file__).with_name('WirelessTransferTest.java'))],check=True)
export, cache, device=work/'export',work/'objects',work/'device'
items={'Music/A/song.mp3':b'actual transport fixture, not an audio-decoder test',
       'Music/A/song.lrc':b'[00:00.00]Original synthetic lyric',
       'Music/A/cover.jpg':b'JPEG transport bytes',
       'Music/B/other.mp3':b'another track',
       'Music/B/other.txt':b'Original synthetic text',
       'Artist_Images/Artist A.jpg':b'JPEG transport bytes',
       'Playlists/Favorites.m3u8':b'#EXTM3U\n/sdcard/Music/A/song.mp3\n/sdcard/Music/B/other.mp3\n',
       '.rockbox/snarty/library-v1.bin':encode_library({'version':1,'tracks':[{'device_path':'/sdcard/Music/A/song.mp3','song_added_rank':1}]})}
for n,b in items.items():p=export/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
(export/'wireless-source-report.json').write_text('{"missing_artist_images":0}')
key=secrets.token_bytes(32);bridge=Bridge(export,cache,key)
def reset():
    bridge.manifest=snapshot(export,cache);bridge.last_refresh=time.monotonic();bridge.error=None
reset();handler=bridge.handler();tamper={'enabled':False};send_header=handler.send_header
def header(self,name,value):
    if tamper['enabled'] and name=='X-Snarty-Auth':value='0'*64
    return send_header(self,name,value)
handler.send_header=header
server=ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}'
def java(mode,root=device,secret=key.hex()):
    subprocess.run(['java','-cp',str(work)+os.pathsep+str(jar),'org.rockbox.WirelessTransferTest',mode,str(root),url,secret],check=True)
try:
    java('first')
    for n,b in items.items():assert (device/n).read_bytes()==b,n
    java('same')
    p=export/'Music/A/song.lrc';p.write_bytes(b'[00:00.00]Updated real source interval');reset();java('update');assert (device/'Music/A/song.lrc').read_bytes()==p.read_bytes()
    song=device/'Music/A/song.mp3';stamp=song.stat();hidden=b'E'*song.stat().st_size;song.write_bytes(hidden);os.utime(song,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    (export/'Music/A/song.mp3').write_bytes(b'Server updated recording bytes');reset();java('hidden-edit');assert song.read_bytes()==hidden
    song.write_bytes(items['Music/A/song.mp3']);os.utime(song,ns=(stamp.st_atime_ns,stamp.st_mtime_ns));(export/'Music/A/song.mp3').write_bytes(items['Music/A/song.mp3']);reset()
    user=device/'Music/A/song.mp3';user.write_bytes(b'user edited locally');java('local-edit');assert user.read_bytes()==b'user edited locally'
    fresh=work/'bad-device'
    good=bridge.manifest
    # Alter authenticated payload without updating the signing key at client.
    java('bad-key',fresh,secret=secrets.token_hex(32))
    tamper['enabled']=True;java('bad-manifest',fresh);tamper['enabled']=False
    entry=json.loads(good)['files'][0];blob=cache/entry['sha256'];original=blob.read_bytes();blob.write_bytes(b'X'*len(original));java('corrupt',fresh);blob.write_bytes(original)
    assert not list((fresh/'Music').glob('**/*.mp3'))
    body=json.loads(good);body['files'][0]['path']='Music/../../escape.mp3';bridge.manifest=json.dumps(body).encode();java('escape',fresh)
    body=json.loads(good);body['files'].append(dict(body['files'][0],path=body['files'][0]['path'].upper().replace('ARTIST_IMAGES','Artist_Images')))
    # Use Music case-preserving prefix to ensure collision check, not whitelist, rejects.
    body=json.loads(good);sample=next(x for x in body['files'] if x['path'].startswith('Music/'))
    body['files'].append(dict(sample,path='Music/'+sample['path'][6:].swapcase()));bridge.manifest=json.dumps(body).encode();java('collision',fresh)
    bridge.manifest=good;java('offline',fresh)
    protected=fresh/'.rockbox/config.cfg';protected.parent.mkdir(parents=True,exist_ok=True);protected.write_bytes(b'keep player settings')
    alias=fresh/'Music/A/song.mp3';alias.parent.mkdir(parents=True,exist_ok=True);alias.symlink_to(protected)
    java('symlink',fresh);assert protected.read_bytes()==b'keep player settings';alias.unlink()
    nonce=secrets.token_hex(16);auth=hmac.new(key,f'GET\n/v1/manifest\n{nonce}'.encode(),'sha256').hexdigest()
    request=urllib.request.Request(url+'/v1/manifest',headers={'X-Snarty-Nonce':nonce,'X-Snarty-Auth':auth})
    with urllib.request.urlopen(request) as response:
        data=response.read();assert hmac.compare_digest(response.headers['X-Snarty-Auth'],hmac.new(key,nonce.encode()+b'\n'+data,'sha256').hexdigest())
    try:urllib.request.urlopen(request);raise AssertionError('Replay accepted')
    except urllib.error.HTTPError as error:assert error.code==403
    (export/'Music/A/SONG.mp3').write_bytes(b'collision')
    try:snapshot(export,cache);raise AssertionError('Case collision accepted')
    except ValueError:pass
    (export/'Music/A/SONG.mp3').unlink();reset()
    subprocess.run([sys.executable,str(Path(__file__).with_name('wireless_android_test.py')),url,key.hex()],check=True)
    print('PASS: byte-identical audio/lyrics/art/playlists/ranks, duplicate-content staging, managed incremental update, local edits, bad key, corrupt content, traversal, Unicode/case policy, offline cancellation and nonce replay; evidence',work)
finally:server.shutdown();server.server_close()
