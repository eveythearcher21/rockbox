#!/usr/bin/env python3
"""Reference writer for the v1 Rockbox/desktop sync library contract.
Input JSON: {"version":1,"tracks":[{"device_path":"/sdcard/Music/song.mp3",
"song_added_rank":1,"album_added_rank":1}]}. Rank 1 means newest in the
YouTube Music account library. 0/None means unknown, never filesystem dates.
"""
import argparse,json,struct,os,unicodedata
from pathlib import Path,PurePosixPath

def encode_library(document):
 if document.get('version')!=1:raise ValueError('Unsupported sync schema')
 rows=[];seen=set()
 for track in document['tracks']:
  path=track['device_path']
  for alias in ('/storage/sdcard0/','/mnt/sdcard/'):
   if path.startswith(alias):path='/sdcard/'+path[len(alias):];break
  raw=path.encode('utf-8')
  if not path.startswith('/') or str(PurePosixPath(path))!=path or '..' in PurePosixPath(path).parts or any(c in path for c in '\0\r\n\t') or len(raw)>259:
   raise ValueError('Invalid canonical device path: '+repr(path))
  collision_key=unicodedata.normalize('NFC',path).casefold()
  if collision_key in seen:raise ValueError('Colliding device path: '+path)
  seen.add(collision_key)
  ranks=[]
  for name in ('song_added_rank','album_added_rank'):
   value=track.get(name)
   if value is None:value=0
   if isinstance(value,bool) or not isinstance(value,int) or not 0<=value<2147483647:raise ValueError('Invalid '+name)
   ranks.append(value)
  rows.append((raw,struct.pack('<260sII',raw,*ranks)))
 if len(rows)>1000000:raise ValueError('Too many entries')
 return struct.pack('<8sII',b'SNRTLIB1',len(rows),268)+b''.join(row for _,row in sorted(rows))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('json_file',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 data=encode_library(json.loads(a.json_file.read_text(encoding='utf-8')))
 a.output.parent.mkdir(parents=True,exist_ok=True);temporary=a.output.with_name(a.output.name+'.tmp')
 with temporary.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(temporary,a.output);print(f'Wrote {len(data)} bytes to {a.output}')
if __name__=='__main__':main()
