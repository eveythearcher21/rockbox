#!/usr/bin/env python3
"""Capture real SDL frames during a selection change; no synthesized UI frames."""
import shutil,time,hashlib,json,threading
from PIL import Image
import navigation_smoke as ui
shutil.copytree(ui.source/'fonts',ui.disk/'.rockbox/fonts',dirs_exist_ok=True)
p=ui.disk/'.rockbox/config.cfg';p.write_text(p.read_text()+'\nfont: /.rockbox/fonts/15-KodeMono-SemiBold.fnt\n')
try:
 ui.start();ui.wait('Music','Videos','Podcasts','Settings')
 frames=[];started=time.monotonic()
 ui.run([ui.xdo,'keydown','Down'])
 release=threading.Timer(.1,lambda:ui.run([ui.xdo,'keyup','Down']));release.start()
 for i in range(15):
  p=ui.work/f'animation-{i:02}.png';ui.run(['import','-window',ui.window,str(p)])
  frames.append(Image.open(p).convert('RGB').copy());time.sleep(.012)
 release.join()
 ui.run([ui.xdo,'keyup','Down'])
 # More than two distinct images proves intermediate animation frames, not a jump.
 unique=len({hashlib.sha256(frame.tobytes()).digest() for frame in frames})
 assert unique>=3,unique
 frames[0].save(ui.work/'Selection-animation.gif',save_all=True,append_images=frames[1:],duration=45,loop=0)
 (ui.work/'animation-results.json').write_text(json.dumps({'distinct_frames':unique,'elapsed_seconds':time.monotonic()-started,'source':'actual SDL screen captures','physical_y1_timing':'not tested'},indent=2))
 print('PASS: '+str(unique)+' distinct real selection-animation frames. Evidence: '+str(ui.work),flush=True)
finally:ui.stop()
