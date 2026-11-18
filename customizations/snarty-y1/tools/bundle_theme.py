#!/usr/bin/env python3
"""Embed the paired SNARTY skin/library assets in Android's resource ZIP."""
from pathlib import Path
import sys,zipfile,os
archive=Path(sys.argv[1]);source=Path(sys.argv[2]);temporary=archive.with_suffix('.snarty.tmp')
assets={('sdcard/.rockbox/'+p.relative_to(source).as_posix()):p for p in source.rglob('*') if p.is_file()}
with zipfile.ZipFile(archive) as old,zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
 for entry in old.infolist():
  if entry.filename not in assets and entry.filename != "sdcard/.rockbox/snarty-playback-v11-assets.txt":new.writestr(entry,old.read(entry))
 manifest=[name.removeprefix('sdcard/.rockbox/') for name in sorted(assets) if not name.endswith('tagnavi_user.config')]
 manifest.append('rocks/apps/lrcplayer.rock')
 new.writestr('sdcard/.rockbox/snarty-playback-v11-assets.txt','\n'.join(manifest)+'\n')
 for name,path in sorted(assets.items()):
  info=zipfile.ZipInfo(name,(2025,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
  new.writestr(info,path.read_bytes())
os.replace(temporary,archive)
print('Embedded %d paired SNARTY theme/library files'%len(assets))
