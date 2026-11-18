#!/usr/bin/env python3
"""Inspect actual ARM ELF plugin headers and matching APK payload, not device execution."""
import struct,zipfile,io,sys,json
from pathlib import Path
apk=Path(sys.argv[1]);out=Path(sys.argv[2])
with zipfile.ZipFile(apk) as a:
 assert a.testzip() is None
 core=a.read('lib/armeabi/librockbox.so')
 for category in ['apps','games','demos','viewers']:
  assert ('/sdcard/.rockbox/rocks/'+category).encode() in core,category
 assert b'/sdcard/.rockbox/rocks/apps/lrcplayer.rock' in core
 with zipfile.ZipFile(io.BytesIO(a.read('lib/armeabi/libmisc.so'))) as z:
  assert z.testzip() is None
  plugins=[n for n in z.namelist() if n.endswith('.rock')];assert len(plugins)==167
  headers=[]
  for n in plugins:
   b=z.read(n);assert b[:6]==b'\x7fELF\1\1' and struct.unpack_from('<HH',b,16)==(3,40),n
   off=struct.unpack_from('<I',b,32)[0];entry,count=struct.unpack_from('<HH',b,46)
   sections=[struct.unpack_from('<10I',b,off+i*entry) for i in range(count)]
   found=False
   for s in sections:
    if s[1]!=11:continue
    strings=sections[s[6]];names=b[strings[4]:strings[4]+strings[5]]
    for pos in range(s[4],s[4]+s[5],s[9]):
     name,value,size,info,other,index=struct.unpack_from('<IIIBBH',b,pos)
     if names[name:].split(b'\0',1)[0]!=b'__header':continue
     data=sections[index];at=data[4]+value-data[3];magic,target,api=struct.unpack_from('<IHH',b,at);api_size=struct.unpack_from('<I',b,at+24)[0]
     assert (magic,target,api)==(0x526f634b,125,285),(n,magic,target,api)
     headers.append(api_size);found=True
   assert found,n
  assert len(set(headers))==1,headers
  resource=[n for n in z.namelist() if '/rocks.data/' in n];assert len(resource)==71
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as target:
   for n in z.namelist():
    if n.startswith('sdcard/.rockbox/rocks/') or n.startswith('sdcard/.rockbox/rocks.data/'):
     target.writestr(n[len('sdcard/'):],z.read(n))
 print(json.dumps({'status':'PASS','plugins':len(plugins),'overlays':sum(n.endswith('.ovl') for n in z.namelist()),'resources':len(resource),'target':125,'plugin_api':285,'api_size':headers[0],'scope':'actual APK/ARM binaries; not Android runtime'},indent=2))
