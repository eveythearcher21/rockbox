#!/usr/bin/env python3
"""Actual expanded-library navigation, retained sorts, density and favorites."""
import shutil,time,json,subprocess
from PIL import Image
import navigation_smoke as ui
for d in ('fonts','icons'):shutil.copytree(ui.source/d,ui.disk/'.rockbox'/d,dirs_exist_ok=True)
(ui.disk/'.rockbox/wps/test13.sbs').write_text('%wd\n%V(5,0,310,25,-)\n%alSNARTY%ar%bl%%\n%V(5,26,310,25,-)\n%al%Lt\n%Vi(-,5,53,310,180,-)\n')
p=ui.disk/'.rockbox/config.cfg';p.write_text(p.read_text()+'\nfont: /.rockbox/fonts/15-KodeMono-SemiBold.fnt\nsbs: /.rockbox/wps/test13.sbs\nbackground color: 232234\nforeground color: a2accd\nscrollbar: off\ntagcache_autoupdate: on\nrepeat: off\n')
for n in range(1,5):
 path=ui.disk/f'Music/{n:02}.flac';out=ui.work/f'long{n}.flac'
 subprocess.run(['ffmpeg','-v','error','-y','-stream_loop','149','-i',str(path),'-t','300','-c:a','flac',str(out)],check=True);shutil.copy2(out,path)
 Image.new('RGB',(200,200),[(220,35,35),(220,35,35),(30,200,40),(30,50,220)][n-1]).save(ui.disk/f'Music/{n:02}.jpg')
for n in range(3,13):
 title=f'Track {n:02} With A Very Long Title That Must Scroll Cleanly'
 album='Album A' if n<9 else f'Album {chr(68+n-9)}';artist='Artist A' if n<9 else f'Artist {chr(67+n-9)}'
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(ui.disk/'Music/01.flac'),'-c','copy','-metadata','title='+title,'-metadata','album='+album,'-metadata','artist='+artist,'-metadata','album_artist='+artist,'-metadata',f'track={n}',str(ui.disk/f'Music/extra{n:02}.flac')],check=True)
 Image.new('RGB',(200,200),(100+n*5,60,180)).save(ui.disk/f'Music/extra{n:02}.jpg')
def key(*keys):
 for k in keys:ui.run([ui.xdo,'keydown',k,'sleep','.08','keyup',k]);time.sleep(.4)
ui.key=key
original=ui.seen
ui.seen=lambda t,w:original(t.replace('Sone','Song').replace('Albuns','Albums').replace('Alburi','Album'),w)
def shot(name):
 ui.screen();shutil.copy2(ui.work/f'screen-{ui.screen_number:03}.png',ui.work/name)
def back_music():ui.key('Escape');ui.wait('Music','Songs','Albums')
def sheet():ui.key('Return');ui.wait('Now Playing','Lyrics')
def gesture():
 command=[ui.xdo]
 for direction in ('Right','Left','Right','Left'):command+=['keydown',direction,'sleep','.06','keyup',direction,'sleep','.06']
 ui.run(command);time.sleep(.7)
try:
 ui.start();ui.wait('Music','Videos');time.sleep(15);ui.stop();p.write_text(p.read_text()+'\ntagcache_autoupdate: off\n');ui.start();ui.wait('Music','Videos')
 # An empty Favorites gesture must not replace/create a queue or navigate.
 control=ui.disk/'.rockbox/.playlist_control';before=control.read_bytes() if control.exists() else None
 gesture();time.sleep(2.2);ui.wait('Music','Videos');assert (control.read_bytes() if control.exists() else None)==before
 ui.record('Empty Favorites gesture stays Home and preserves the queue')
 ui.key('Return','Down','Return');ui.wait('Albums','Album A');ui.key('Return');ui.wait('Album A','Alpha Song');shot('Eight-Album-Tracks.png')
 ui.record('Compact album header and full-width eight-row track pane captured')
 ui.key('Return');time.sleep(1);sheet();ui.key(*(['Down']*4));ui.wait('Favorite');ui.key('Return');ui.wait('Song?','Album?','Artist?');ui.key('Down','Return');time.sleep(2)
 # The album rule includes exactly Alpha/Beta + the six extra Album A files.
 expected={'/Music/01.flac','/Music/02.flac',*[f'/Music/extra{n:02}.flac' for n in range(3,9)]}
 gesture();time.sleep(1);data=control.read_text();paths=[line.split(':',3)[3] for line in data.splitlines() if line.startswith(('A:','Q:'))]
 assert set(paths)==expected and len(paths)==8,(paths,data)
 shuffle=[line for line in data.splitlines() if line.startswith('S:')];assert shuffle and shuffle[-1].split(':')[2]=='0',data
 shot('Shuffled-Favorites-Playback.png');ui.record('WPS RLRL creates a complete unique eight-song Favorites queue, shuffles it and persists origin zero')
 ui.key('Escape');ui.wait('Album A');gesture();time.sleep(1);data=control.read_text();paths=[line.split(':',3)[3] for line in data.splitlines() if line.startswith(('A:','Q:'))]
 assert set(paths)==expected and len(paths)==8,data
 ui.record('The same shortcut works in the album browser and enters playback')
 (ui.work/'navigation14-results.json').write_text(json.dumps({'passed':ui.passed,'queue':data,'expected':sorted(expected),'evidence':str(ui.work)},indent=2));print('Evidence:',ui.work,flush=True)
finally:ui.stop()
