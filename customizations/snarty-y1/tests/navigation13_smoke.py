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
try:
 ui.start();ui.wait('Music','Videos');time.sleep(15);ui.stop();p.write_text(p.read_text()+'\ntagcache_autoupdate: off\n');ui.start();ui.wait('Music','Videos')
 ui.key('Return','Down','Return');ui.wait('Albums','Album A');shot('Five-Albums.png')
 ui.key('Up','Return');ui.wait('Albums');assert (ui.disk/'.rockbox/snarty-sorts-v1.bin').read_bytes()[2]==2
 back_music();ui.key('Return');ui.wait('Albums');ui.key('Up');ui.wait('By Artist');shot('Remembered-Artist-Sort.png');ui.key('Down','Return');ui.wait('Album A','Alpha Song');shot('Five-Album-Tracks.png')
 # Scroll the long selected title across several actual frames.
 ui.key('Down','Down');time.sleep(1)
 for i in range(3):shot(f'Marquee-{i}.png');time.sleep(.8)
 ui.key('Escape');ui.wait('Albums');back_music();ui.key('Up','Return');ui.wait('Songs','Alpha Song');shot('Five-Songs.png')
 ui.key('Up','Up','Return');ui.wait('Songs');assert (ui.disk/'.rockbox/snarty-sorts-v1.bin').read_bytes()[1]==1
 back_music();ui.key('Return');ui.wait('Songs');shot('Remembered-Recent-Songs.png')
 # Pick first recent track, use top Back to return to the same list.
 ui.key('Return');time.sleep(1);ui.key('Escape');ui.wait('Songs');ui.record('Top Back returns from playback to originating Songs; sorts persist independently')
 # Ensure alphabetical start for deterministic favorite seed Alpha.
 ui.key('Up','Return');ui.wait('Songs');ui.key('Return');time.sleep(1);sheet();ui.key(*(['Down']*4));ui.wait('Favorite');ui.key('Return');ui.wait('Song?','Album?','Artist?');ui.key('Down','Down','Return');time.sleep(2)
 assert list((ui.disk/'.rockbox/snarty-favorites-v1').glob('*.fav'))
 ui.key('Escape');ui.wait('Songs');back_music();ui.key(*(['Down']*5));ui.wait('Favorites');ui.key('Return');ui.wait('Favorites');shot('Favorites.png')
 control=(ui.disk/'.rockbox/snarty-sorts-v1.bin').read_bytes();ui.record('Favorite star exposes Song/Album/Artist rules; artist Favorites browse opens; five-row card/track views captured')
 (ui.work/'navigation13-results.json').write_text(json.dumps({'passed':ui.passed,'sort_bytes':list(control),'evidence':str(ui.work)},indent=2));print('Evidence:',ui.work,flush=True)
finally:ui.stop()
