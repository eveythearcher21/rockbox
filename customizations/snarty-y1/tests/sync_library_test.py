#!/usr/bin/env python3
"""Cross-language golden test of the actual device reader and reference writer."""
from pathlib import Path
import importlib.util,subprocess,tempfile,struct,json
repo=Path(__file__).resolve().parents[3]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
writer=module('library',repo/'customizations/snarty-y1/tools/compile_sync_library.py')
lyrics=module('lyrics',repo/'customizations/snarty-y1/tools/encode_word_lyrics.py')
r=Path(tempfile.mkdtemp(prefix='snarty-library-test-'));(r/'snarty').mkdir();stubs=r/'headers';stubs.mkdir()
(stubs/'config.h').write_text('')
(stubs/'file.h').write_text('#include <unistd.h>\n#include <sys/types.h>\n#include <fcntl.h>\n')
(stubs/'rbpaths.h').write_text('#define ROCKBOX_DIR '+json.dumps(str(r))+'\n')
(r/'main.c').write_text('#include <stdio.h>\n#include <stdlib.h>\n#include "snarty_library.h"\nint main(int n,char**v){if(n!=3)return 2;printf("%d %ld\\n",snarty_library_available(),snarty_library_rank(v[1],atoi(v[2])));}\n')
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g','-I',str(stubs),'-I',str(repo/'apps'),str(repo/'apps/snarty_library.c'),str(r/'main.c'),'-o',str(r/'test')],check=True)
tracks=[{'device_path':'/Music/space é.mp3','song_added_rank':1,'album_added_rank':4},{'device_path':"/Music/A 'quote'.flac",'song_added_rank':3,'album_added_rank':2},{'device_path':'/Music/unknown.mp3','song_added_rank':0,'album_added_rank':None}]
p=r/'snarty/library-v1.bin';data=writer.encode_library({'version':1,'tracks':tracks});p.write_bytes(data)
def expect(path,album,available,rank):
 result=subprocess.run([str(r/'test'),path,str(int(album))],capture_output=True,text=True,check=True).stdout.strip();assert result==f'{int(available)} {rank}',result
for track in tracks:
 for album in (False,True):expect(track['device_path'],album,True,track['album_added_rank' if album else 'song_added_rank'] or 2147483647)
expect('/Music/missing.mp3',False,True,2147483647)
for damaged in [b'',b'wrongheader'*2,data[:-1],data[:8]+struct.pack('<I',1000001)+data[12:],data[:12]+struct.pack('<I',269)+data[16:]]:
 p.write_bytes(damaged);expect('/Music/space é.mp3',False,False,2147483647)
p.write_bytes(writer.encode_library({'version':1,'tracks':[{'device_path':'/storage/sdcard0/Music/alias.mp3','song_added_rank':7,'album_added_rank':9}]}))
for alias in ('/sdcard/','/storage/sdcard0/','/mnt/sdcard/'):
 expect(alias+'Music/alias.mp3',False,True,7);expect(alias+'Music/alias.mp3',True,True,9)
p.write_bytes(writer.encode_library({'version':1,'tracks':[]}));expect('/x',False,False,2147483647)
for bad in ['relative.mp3','/a/../b','/a//b','/a\n.mp3','/a\0.mp3','/'+('é'*130)]:
 try:writer.encode_library({'version':1,'tracks':[{'device_path':bad}]});raise AssertionError(bad)
 except ValueError:pass
for value in (True,False):
 try:writer.encode_library({'version':1,'tracks':[{'device_path':'/a','song_added_rank':value}]});raise AssertionError('Boolean rank')
 except ValueError:pass
for paths in [('/Music/A.mp3','/Music/a.mp3'),('/Music/é.mp3','/Music/e\u0301.mp3')]:
 try:writer.encode_library({'version':1,'tracks':[{'device_path':v} for v in paths]});raise AssertionError('Collision')
 except ValueError:pass
sample={'duration_ms':10000,'lines':[{'words':[{'text':'Paper ','start_ms':0,'end_ms':900},{'text':'stars ','start_ms':1200,'end_ms':1900},{'text':'shine','start_ms':2300,'end_ms':3500}]}]}
lrc=lyrics.encode_words(sample).decode('utf-8-sig');assert '[00:00.00]<00:00.00>Paper <00:00.90><00:01.20>stars <00:01.90><00:02.30>shine<00:03.50>' in lrc
for invalid in [{'duration_ms':100,'lines':[{'words':[{'text':'x','start_ms':0,'end_ms':200}]}]}, {'duration_ms':1000,'lines':[{'text':'untimed'}]}]:
 try:lyrics.encode_words(invalid);raise AssertionError('Invented timings')
 except ValueError:pass
print('PASS: actual C library reader under ASan/UBSan matches reference writer for UTF8, spaces/quotes, independent song/album ranks, unknowns, malformed/truncated data, bounds and invalid paths; word encoder preserves explicit intervals and rejects invented timing')
