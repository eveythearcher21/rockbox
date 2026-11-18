#!/usr/bin/env python3
"""Encode actual word intervals as UTF-8-BOM enhanced LRC, without inventing timing.
JSON: {"duration_ms":...,"lines":[{"words":[{"text":"word ","start_ms":0,
"end_ms":500},...]}]}. Input intervals must be verified/aligned to the local audio.
Long lines split at word boundaries below the player's 512-byte input limit.
"""
import argparse,json,os
from pathlib import Path

def stamp(ms,bracket='<'):
 minutes,rest=divmod(ms,60000);seconds,centiseconds=divmod(rest//10,100)
 return f'{bracket}{minutes:02}:{seconds:02}.{centiseconds:02}'+(']' if bracket=='[' else '>')

def encode_words(document):
 duration=document['duration_ms']
 if isinstance(duration,bool) or not isinstance(duration,int) or not 0<duration<2147483647:raise ValueError('Invalid duration')
 output=['[re:SNARTY sync word-timed lyrics]'];previous_end=-1
 for line in document['lines']:
  words=line.get('words')
  if not words:raise ValueError('Word intervals required; use ordinary LRC/TXT for line/plain lyrics')
  chunk=[];chunk_start=None;chunk_end=None
  for word in words:
   start,end,text=word['start_ms'],word['end_ms'],word['text']
   if any(isinstance(t,bool) or not isinstance(t,int) for t in (start,end)) or not 0<=start<end<=duration or start<previous_end:
    raise ValueError('Word intervals must be ordered, non-overlapping, within the matching audio')
   if not text or any(c in text for c in '\0\r\n<>'):raise ValueError('Unsafe/empty lyric token')
   if chunk_start is None:chunk_start=start
   if end//10<=start//10:raise ValueError("Word interval below player timing precision")
   part=stamp(start)+text+stamp(end)
   candidate=stamp(chunk_start,'[')+''.join(chunk)+part
   if len(candidate.encode('utf-8'))>480:
    if not chunk:raise ValueError('Single lyric token too long')
    output.append(stamp(chunk_start,'[')+''.join(chunk));chunk=[];chunk_start=start
    if len((stamp(start,'[')+part).encode('utf-8'))>480:raise ValueError('Single lyric token too long')
   chunk.append(part);chunk_end=end;previous_end=end
  output.append(stamp(chunk_start,'[')+''.join(chunk))
 return ('\ufeff'+'\n'.join(output)+'\n').encode('utf-8')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('json_file',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 data=encode_words(json.loads(a.json_file.read_text(encoding='utf-8')))
 a.output.parent.mkdir(parents=True,exist_ok=True);temp=a.output.with_name(a.output.name+'.tmp')
 with temp.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(temp,a.output)
if __name__=='__main__':main()
