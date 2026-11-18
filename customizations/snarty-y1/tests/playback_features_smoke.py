#!/usr/bin/env python3
"""Real SDL tests of synced ordering, cover cards/detail, one-click sheet/radio/lyrics."""
import shutil,subprocess,json,time,importlib.util,re,threading,hashlib
from pathlib import Path
from PIL import Image
import navigation_smoke as ui
repo=Path(__file__).resolve().parents[3]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
writer=module('sync_library',repo/'customizations/snarty-y1/tools/compile_sync_library.py')
lyrics=module('sync_lyrics',repo/'customizations/snarty-y1/tools/encode_word_lyrics.py')
for directory in ('fonts','icons'):shutil.copytree(ui.source/directory,ui.disk/'.rockbox'/directory,dirs_exist_ok=True)
for n in range(1,5):
 source=ui.disk/f'Music/{n:02}.flac';out=ui.work/f'long-{n}.flac'
 subprocess.run(['ffmpeg','-v','error','-y','-stream_loop','149','-i',str(source),'-t','300','-c:a','flac',str(out)],check=True);shutil.copy2(out,source)
 Image.new('RGB',(200,200),[(220,35,35),(220,35,35),(30,200,40),(30,50,220)][n-1]).save(ui.disk/f'Music/{n:02}.jpg',quality=95)
 data={'duration_ms':300000,'lines':[]}
 for start in range(0,300000,10000):
  data['lines'].append({'words':[{'text':text,'start_ms':start+offset,'end_ms':start+offset+2800} for text,offset in [('Paper ',0),('stars ',3000),('shine',6000)]]})
 (ui.disk/f'Music/{n:02}.lrc').write_bytes(lyrics.encode_words(data))
(ui.disk/'Music/03.flac.radio.m3u8').write_text('#SNARTY-RADIO\t1\n/Music/03.flac\n/Music/missing.mp3\n/Music/01.flac\n/Music/04.flac\n/Music/01.flac\n')
(ui.disk/'.rockbox/snarty').mkdir()
tracks=[{'device_path':f'/Music/{n:02}.flac','song_added_rank':rank,'album_added_rank':album} for n,rank,album in [(1,3,2),(2,2,2),(3,1,1),(4,4,3)]]
(ui.disk/'.rockbox/snarty/library-v1.bin').write_bytes(writer.encode_library({'version':1,'tracks':tracks}))
(ui.disk/'Playlists').mkdir();(ui.disk/'Playlists/Test.m3u8').write_text('/Music/01.flac\n')
plugin=ui.build/'apps/plugins/lrcplayer.rock';shutil.copy2(plugin,ui.disk/'.rockbox/rocks/apps/lrcplayer.rock')
wps=ui.disk/'.rockbox/wps/snarty-fixture.wps'
wps.write_text('''%wd
%V(0,0,320,28,-)
%acPLAYBACK
%V(160,35,155,36,-)
%s%it
%V(160,80,155,28,-)
%s%ia
%V(160,115,155,28,-)
%s%id
%V(5,190,310,20,-)
%acQUEUE %pp OF %pe
%V(5,215,310,20,-)
%pc / %pt
%V(13,47,133,133,-)
%Cl(0,0,133,133,c,c)
%Cd
''')
(ui.disk/'.rockbox/wps/snarty-fixture.sbs').write_text('''%wd
%V(5,0,310,24,-)
%alSNARTY%ar%bl%%
%V(5,25,310,25,-)
%al%Lt
%Vi(-,5,53,310,180,-)
''')
p=ui.disk/'.rockbox/config.cfg';p.write_text(p.read_text()+'''\nfont: /.rockbox/fonts/15-KodeMono-SemiBold.fnt
wps: /.rockbox/wps/snarty-fixture.wps
sbs: /.rockbox/wps/snarty-fixture.sbs
repeat: off
playlist viewer track display: title from tags
''')
def key(*keys):
 # Deliver down/up in one xdotool process: spawning a second process under
 # parallel build/OCR load can turn a short test press into a >300ms hold.
 for button in keys:
  ui.run([ui.xdo,'keydown',button,'sleep','0.08','keyup',button]);time.sleep(.45)
ui.key=key
original_seen=ui.seen
def seen(text,word):
 text=text.replace('Sone','Song').replace('sone','song').replace('Album &','Album B')
 if word=='Songs' and 'sones' in text.lower():return True
 if word=='Albums' and 'albuns' in text.lower():return True
 if word=='2025' and '2825' in text:return True
 return original_seen(text,word)
ui.seen=seen

def wait(*words):return ui.wait(*words)
def capture(name):
 ui.screen();path=ui.work/f'screen-{ui.screen_number:03}.png';shutil.copy2(path,ui.work/name);return Image.open(path).resize((320,240),Image.Resampling.NEAREST).convert('RGB')
def home():ui.key('Escape');wait('Music','Videos','Podcasts','Settings')
def animate(name):
 frames=[]
 ui.run([ui.xdo,'keydown','Return'])
 release=threading.Timer(.1,lambda:ui.run([ui.xdo,'keyup','Return']));release.start()
 for i in range(15):
  p=ui.work/f'{name}-{i:02}.png';ui.run(['import','-window',ui.window,str(p)])
  frames.append(Image.open(p).convert('RGB').copy());time.sleep(.012)
 release.join();ui.run([ui.xdo,'keyup','Return'])
 distinct=len({hashlib.sha256(im.tobytes()).digest() for im in frames});assert distinct>=3,(name,distinct)
 frames[0].save(ui.work/f'{name}.gif',save_all=True,append_images=frames[1:],duration=45,loop=0)
 ui.record(f'{name}: {distinct} distinct actual SDL frames')
animated_sheet=False
def sheet():
 global animated_sheet
 if not animated_sheet:animate('Playing-Sheet-Slide');animated_sheet=True
 else:ui.key('Return')
 wait('Now Playing','Play Similar Songs','Lyrics')
try:
 ui.start();wait('Music','Videos','Podcasts','Settings');ui.key('Return');wait('Music','Songs','Albums')
 ui.key('Return');wait('Songs','Alpha Song','Beta Song');ui.key('Up');wait('Recently Added');ui.key('Return');wait('Songs','Gamma Song')
 im=capture('Recently-Added-Songs.png')
 ui.key('Return');wait('PLAYBACK','Gamma Song');ui.record('Recently Added Songs starts with synced rank1 Gamma, not file or alphabetical order')
 home();ui.key('Return','Down','Return');wait('Albums','Album A','Artist A')
 im=capture('Album-Cards.png');r,g,b=im.getpixel((20,80));assert r>150 and g<100 and b<100,(r,g,b)
 ui.key('Up');wait('Recently Added');ui.key('Return');wait('Albums','Album B','Artist A')
 im=capture('Recently-Added-Albums.png');r,g,b=im.getpixel((20,80));assert g>130 and r<100 and b<100,(r,g,b)
 ui.record('Album cards show real color art, title and artist; synced album rank1 Album B moves above Album A')
 animate('Album-Cover-Zoom');wait('Album B','Artist A','Gamma Song');im=capture('Album-Detail.png');r,g,b=im.getpixel((30,100));assert g>130 and r<100 and b<100,(r,g,b)
 ui.key('Return');wait('PLAYBACK','Gamma Song');ui.record('Opening an album expands its cover into the playback-sized panel and keeps the song list alongside')
 sheet();capture('Playing-Song-Menu.png');ui.key('Left');wait('PLAYBACK','Gamma Song')
 sheet();ui.key('Return');wait('Album B','Gamma Song');ui.key('Left');wait('PLAYBACK','Gamma Song')
 ui.record('One click opens the six-item sheet; Back returns to playback; Album shortcut Back also returns to playback')
 sheet();ui.key('Down','Down','Return');wait('PLAYBACK','Gamma Song');text=ui.screen();assert re.search(r'1\s*(?:OF|of)\s*3',text),text
 ui.record('Synced radio keeps Gamma playing and queues two valid distinct recommendations, skipping the seed, missing file and duplicate')
 sheet();ui.key('Down','Down','Down','Return');wait('Words');wait('Paper','stars')
 images=[];counts=[]
 for i in range(4):
  im=capture(f'Lyrics-{i}.png');images.append(im)
  counts.append(sum(1 for r,g,b in im.crop((0,65,320,225)).getdata() if g>150 and g>r+15 and g>b+5));time.sleep(.6)
 assert max(counts)>0 and len(set(counts))>1,counts
 images[0].save(ui.work/'Word-Lyrics.gif',save_all=True,append_images=images[1:],duration=600,loop=0)
 time.sleep(.3);ui.key('Escape');wait('PLAYBACK','Gamma Song')
 ui.record('Lyrics loads enhanced LRC word intervals, changes mint word highlight during actual playback, and Back returns to playback')
 sheet();ui.key(*(['Down']*5));wait('Current Playlist');ui.key('Return');wait('Gamma Song','Alpha Song','Delta Song');ui.key('Left');wait('PLAYBACK','Gamma Song')
 ui.record('Current Playlist opens the recommendation queue and Back returns to playback')
 (ui.work/'features-results.json').write_text(json.dumps({'passed':ui.passed,'highlight_pixel_counts':counts,'evidence':str(ui.work)},indent=2)+'\n')
 print('Evidence: '+str(ui.work),flush=True)
except Exception:
 print('Simulator exit:',ui.sim.poll() if ui.sim else None,'Evidence:',ui.work,flush=True);raise
finally:ui.stop()
