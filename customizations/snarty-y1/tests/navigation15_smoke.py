#!/usr/bin/env python3
"""Actual nonplaying song menu targeting, return navigation, portrait lookup and grid."""
import shutil,time,json,os
from pathlib import Path
from PIL import Image
import navigation_smoke as ui
fixture=Path(os.environ.get('SNARTY_FIXTURE','/tmp/snarty-navigation-jn21a7k6/simdisk'))
if not fixture.is_dir():raise SystemExit('Requires navigation14_smoke fixture; run that test and set fixture path first')
shutil.copytree(fixture,ui.disk,dirs_exist_ok=True)
config=ui.disk/'.rockbox/config.cfg';config.write_text(config.read_text()+'\nplaylist viewer track display: title from tags\n')
shutil.copy2(ui.build/'apps/plugins/lrcplayer.rock',ui.disk/'.rockbox/rocks/apps/lrcplayer.rock')
(ui.disk/'Artist_Images').mkdir(exist_ok=True);Image.new('RGB',(200,200),(220,30,220)).save(ui.disk/'Artist_Images/aRtIsT a.JPG')
(ui.disk/'.rockbox/snarty/artist-images').mkdir(parents=True,exist_ok=True)
Image.new('RGB',(200,200),(20,200,220)).save(ui.disk/'Artist_Images/Artist B.png')
Image.new('RGB',(200,200),(20,200,220)).save(ui.disk/'.rockbox/snarty/artist-images/Artist B.jpg')
(ui.disk/'Playlists').mkdir(exist_ok=True)
(ui.disk/'Playlists/Mix.m3u8').write_text('#EXTM3U\n../Music/01.flac\n/Music/02.flac\n/Music/03.flac\n/Music/04.flac\n/Music/extra09.flac\n')
(ui.disk/'Music/04.lrc').write_text('[00:00.00]Delta preview words\n[00:05.00]Selected song only\n')
(ui.disk/'Music/04.flac.radio.m3u8').write_text('/Music/03.flac\n/Music/01.flac\n')
def key(*keys):
 for k in keys:ui.run([ui.xdo,'keydown',k,'sleep','.08','keyup',k]);time.sleep(.45)
ui.key=key
original=ui.seen
ui.seen=lambda t,w:original(t.replace('Albun ','Album ').replace('flbun ','Album ').replace('Sone','Song').replace('Albuns','Albums').replace('Alburi','Album'),w)
def shot(name):
 ui.screen();shutil.copy2(ui.work/f'screen-{ui.screen_number:03}.png',ui.work/name)
 return Image.open(ui.work/name).resize((320,240)).convert('RGB')
def hold():ui.run([ui.xdo,'keydown','Return','sleep','.65','keyup','Return']);time.sleep(.4)
def music():ui.key('Escape');ui.wait('Music','Songs','Albums')
try:
 ui.start();ui.wait('Music','Videos');ui.key('Return','Return');ui.wait('Songs','Alpha Song');ui.key('Return');time.sleep(1);ui.key('Escape');ui.wait('Songs');ui.key('Down','Down');hold();ui.wait('Song','Album C','Artist B');shot('Selected-Song-Menu.png')
 control=ui.disk/'.rockbox/.playlist_control';before=control.read_bytes()
 ui.key(*(['Down']*4));ui.key('Return');ui.wait('Song?','Album?','Artist?');ui.key('Return');time.sleep(2.3);ui.wait('Songs')
 assert any(b'/Music/04.flac\x00' in p.read_bytes() for p in (ui.disk/'.rockbox/snarty-favorites-v1').glob('*.fav'))
 assert control.read_bytes()==before
 ui.record('Held Delta menu shows selected Album C/Artist B; Favorite Song targets Delta without replacing Alpha playback')
 hold();ui.wait('Album C');ui.key('Return');ui.wait('Album C','Delta Song');shot('Selected-Album.png');ui.key('Escape');ui.wait('Songs','Delta Song')
 hold();ui.wait('Artist B');ui.key('Down','Return');ui.wait('Album C');ui.key('Escape');ui.wait('Songs')
 ui.record('Selected Album and Artist browse correct library tags; Back restores original Songs list')
 hold();ui.wait('Lyrics');ui.key('Down','Down','Down','Return');ui.wait('Preview','Delta');shot('Selected-Lyrics-Preview.png');assert control.read_bytes()==before;ui.key('Escape');ui.wait('Songs')
 ui.record('Nonplaying Delta lyric preview opens and returns without modifying the current queue')
 hold();ui.key('Down','Down','Return');time.sleep(2);data=control.read_text();paths=[line.split(':',3)[3] for line in data.splitlines() if line.startswith(('A:','Q:'))];assert paths==['/Music/04.flac','/Music/03.flac','/Music/01.flac'],data
 ui.key('Escape');ui.wait('Songs');music();ui.key('Down','Down','Return');ui.wait('Artists','Artist A');im=shot('Named-Artist-Portrait.png');r,g,b=im.getpixel((20,70));assert r>150 and b>150 and g<100,(r,g,b);r,g,b=im.getpixel((20,106));assert g>130 and b>130 and r<100,(r,g,b);ui.key('Escape');ui.wait('Music')
 ui.record('Selected-song radio starts Delta then its ranked continuation; Artist_Images case-insensitive JPEG naming displays the requested portrait')
 ui.key('Down','Return');ui.wait('Playlists');im=shot('Playlist-Four-Albums.png')
 for point,expected in [((14,62),'red'),((32,62),'green'),((14,80),'blue'),((32,80),'purple')]:
  r,g,b=im.getpixel(point)
  assert {'red':r>150 and g<100 and b<100,'green':g>130 and r<100 and b<100,'blue':b>130 and r<100 and g<100,'purple':r>80 and b>120 and g<100}[expected],(point,expected,(r,g,b))
 ui.key('Return');ui.wait('Alpha Song');ui.key('Down');hold();ui.wait('Album A','Artist A');shot('Playlist-Song-Menu.png');ui.key('Return');ui.wait('Album A');ui.key('Escape');ui.wait('Beta Song')
 hold();ui.wait('Album A','Artist A');ui.key(*(['Down']*6));ui.key('Return');ui.wait('Playlist');shot('Current-Queue-From-Song-Menu.png');assert len([line for line in control.read_text().splitlines() if line.startswith(('A:','Q:'))])==3
 ui.record('Playlist collage has four distinct album colors, ignores duplicate Album A, resolves relative paths; playlist hold opens shared selected-song menu and album Back returns to playlist')
 (ui.work/'navigation15-results.json').write_text(json.dumps({'passed':ui.passed,'evidence':str(ui.work)},indent=2));print('Evidence:',ui.work,flush=True)
finally:ui.stop()
