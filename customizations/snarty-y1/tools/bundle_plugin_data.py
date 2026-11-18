#!/usr/bin/env python3
"""Pair hosted flat rocks.data resources with the original categorized tree."""
import sys,zipfile,os
from pathlib import Path
p=Path(sys.argv[1]);prefix='sdcard/.rockbox/';out=p.with_name(p.name+'.resources')
with zipfile.ZipFile(p) as z:
 data={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
 for n,b in list(data.items()):
  if not n.startswith(prefix+'rocks/') or n.endswith(('.rock','.ovl')):continue
  relative=n[len(prefix+'rocks/'):];parts=relative.split('/',1)
  if len(parts)!=2 or parts[0] not in ('apps','games','demos','viewers'):continue
  dest=prefix+'rocks.data/'+parts[1]
  if dest in data and data[dest]!=b:raise ValueError('Plugin resource collision: '+dest)
  data[dest]=b
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in data.items():z.writestr(n,b)
os.replace(out,p)
print('Paired hosted plugin data resources')
