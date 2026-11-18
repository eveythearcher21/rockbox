from pathlib import Path
import subprocess,re
root=Path('/workspace/builds/y1-plugins-fixed');ndk=Path('/workspace/setup/android-ndk-r10e');readelf=ndk/'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/arm-linux-androideabi-readelf'
def symbols(p):
 text=subprocess.check_output([str(readelf),'--dyn-syms','--wide',str(p)],text=True);defined=set();undefined=set()
 for l in text.splitlines():
  a=l.split()
  if len(a)>=8 and a[0].endswith(':'):
   if a[6]=='UND':
    if a[4]!='WEAK':undefined.add(a[7].split('@')[0])
   else:defined.add(a[7].split('@')[0])
 return defined,undefined
provided=set()
for p in (ndk/'platforms/android-17/arch-arm/usr/lib').glob('*.so'):provided|=symbols(p)[0]
provided|=symbols(root/'librockbox.so')[0]
errors={}
for p in (root/'apps/plugins').rglob('*'):
 if p.suffix not in ('.rock','.ovl'):continue
 missing=symbols(p)[1]-provided
 if missing:errors[str(p.relative_to(root))]=sorted(missing)
print('Unresolved against API17 public libraries + core:',errors)
if errors:raise SystemExit(1)
print('PASS: all plugin/overlay strong dynamic imports available from API17/core')
