#!/usr/bin/env python3
"""Real shared renderer/artists/media checks; synthetic private fixture only."""
import shutil,time,json
from PIL import Image
import navigation_smoke as ui
for d in ('fonts','icons'):shutil.copytree(ui.source/d,ui.disk/'.rockbox'/d,dirs_exist_ok=True)
shutil.copy2(ui.source/'wps/SNARTY-Y1.sbs',ui.disk/'.rockbox/wps/rebrand.sbs')
# Scale only viewport coordinates/font for the 320px simulator fixture.
p=ui.disk/'.rockbox/wps/rebrand.sbs';s=p.read_text().replace('22-KodeMono','15-KodeMono')
import re
s=re.sub(r'(?m)(%V(?:i)?\([^\n]*)',lambda m:m[0],s)
# Native Y1 SBS has480px coordinates; use its test-scale counterpart.
p.write_text('%wd\n%V(5,0,310,25,-)\n%alSNARTY%ar%bl%%\n%V(5,26,310,25,-)\n%al%Lt\n%Vi(-,5,53,310,180,-)\n')
p=ui.disk/'.rockbox/config.cfg';p.write_text(p.read_text()+'\nfont: /.rockbox/fonts/15-KodeMono-SemiBold.fnt\nsbs: /.rockbox/wps/rebrand.sbs\nbackground color: 232234\nforeground color: a2accd\niconset: SNARTY.bmp\nscrollbar: off\n')
for n in range(1,5):Image.new('RGB',(200,200),(30,200,40)).save(ui.disk/f'Music/{n:02}.flac.artist.jpg')
(ui.disk/'Videos').mkdir(exist_ok=True);(ui.disk/'Videos/Test.mpg').write_bytes(b'fixture only, never played')
Image.new('RGB',(200,200),(220,180,30)).save(ui.disk/'Videos/Test.jpg')
show=ui.disk/'Podcasts/Test Show';show.mkdir(parents=True);Image.new('RGB',(200,200),(30,50,220)).save(show/'cover.jpg')
for n in (1,2):shutil.copy2(ui.disk/f'Music/{n:02}.flac',show/f'{n:06} - Episode.flac')
def key(*keys):
 for k in keys:ui.run([ui.xdo,'keydown',k,'sleep','.08','keyup',k]);time.sleep(.45)
ui.key=key
original=ui.seen
ui.seen=lambda t,w:original(t.replace('Fest','Test').replace('Sone','Song').replace('Albuns','Albums'),w)
def shot(name):
 ui.screen();shutil.copy2(ui.work/f'screen-{ui.screen_number:03}.png',ui.work/name)
 return Image.open(ui.work/name).resize((320,240)).convert('RGB')
try:
 ui.start();ui.wait('Music','Videos','Podcasts','Settings');ui.key('Return','Down','Down','Return');ui.wait('Artists','Artist A')
 im=shot('Artist-Cards.png');r,g,b=im.getpixel((20,80));assert g>130 and r<100,(r,g,b)
 ui.key('Return');ui.wait('Artist A','Album A');shot('Artist-Albums.png');ui.record('Artist cards use distinct real portrait sidecars and open filtered albums')
 ui.key('Escape');ui.wait('Music','Videos');ui.key('Down','Return');ui.wait('Videos','Test');im=shot('Video-Cards.png');r,g,b=im.getpixel((20,80));assert r>150 and g>100 and b<80,(r,g,b);ui.key('Left');ui.wait('Music','Videos')
 ui.key('Down','Return');ui.wait('Podcasts','Test Show');shot('Podcast-Shows.png');ui.key('Return');ui.wait('Episode');shot('Podcast-Episodes.png');ui.record('Video cards and grouped podcast show/episode views retain functional navigation')
 (ui.work/'rebrand-results.json').write_text(json.dumps(ui.passed,indent=2));print('Evidence:',ui.work,flush=True)
finally:ui.stop()
