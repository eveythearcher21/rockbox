#!/usr/bin/env python3
"""GUI regression for playing-track shortcuts and explicit Database entry.
Requires the onboarding iPod 6G simulator + four-track fixture, Xvfb, xdotool,
ImageMagick, Tesseract and Pillow. Runs an isolated copy; never edits simdisk.
"""
import json,os,re,select,shutil,subprocess,tempfile,time
from pathlib import Path
from PIL import Image,ImageOps

build=Path('/workspace/builds/ipod6g-sim')
source=Path('/workspace/rockbox/customizations/snarty-y1/.rockbox')
work=Path(tempfile.mkdtemp(prefix='snarty-navigation-',dir='/tmp'))
disk=work/'simdisk';disk.mkdir()
shutil.copytree(build/'simdisk/.rockbox',disk/'.rockbox')
(disk/'Music').mkdir()
for name in ('01.flac','02.flac','03.flac','04.flac'):
 shutil.copy2(build/'simdisk/Music'/name,disk/'Music'/name)
shutil.copy2(source/'tagnavi_user.config',disk/'.rockbox/tagnavi_user.config')
(disk/'.rockbox/config.cfg').write_text('''wps: cabbiev2.wps
root menu order: database, songs, artists, wps, settings, system_menu
start in screen: root
repeat: one
shuffle: off
warn when erasing dynamic playlist: off
gather runtime data: off
tagcache_autoupdate: off
show icons: on
''')
for name in ('.playlist_control','.resume.cfg'):
 p=disk/'.rockbox'/name
 if p.exists():p.unlink()
env=os.environ.copy();env['OMP_THREAD_LIMIT']='1'
env['LD_LIBRARY_PATH']='/workspace/setup/sysroot/usr/lib/x86_64-linux-gnu'
env['SDL_VIDEODRIVER']='x11';env['SDL_AUDIODRIVER']='dummy';env['SDL_RENDER_DRIVER']='software'
runtime=work/'runtime';runtime.mkdir(mode=0o700)
env['XDG_RUNTIME_DIR']=str(runtime);env['XDG_CACHE_HOME']=str(work/'cache')
xdo='/workspace/setup/sysroot/usr/bin/xdotool'
xserver=None;sim=None;screen_number=0;window=None;passed=[];player_visible=False;selected_text=''
def run(args,**kwargs):return subprocess.run(args,env=env,check=True,capture_output=True,text=True,**kwargs)
def norm(text):return re.sub('[^a-z0-9]','',text.lower())
def seen(text,word):
 # Allow only known bitmap-font menu-label OCR confusions. Song names,
 # calendar years and play counts are always checked exactly.
 text=re.sub(r'\b(artist|album)\s*&',r'\1 A',text,flags=re.I)
 expected=norm(word);actual=norm(text)
 aliases={'songs':('songs','sangs'),'artists':('artists','ariists'),
          'spotifywrapped':('spotifywrapped','spotitywrapped'),
          'numeric':('numeric','mumeric','alumeric'),
          'artista':('artista','artist4'),'albuma':('albuma','album4')}
 return any(value in actual for value in aliases.get(expected,(expected,)))
def screen():
 global screen_number,player_visible,selected_text
 screen_number+=1;selected_text=''
 path=work/f'screen-{screen_number:03}.png'
 run(['import','-window',window,str(path)])
 with Image.open(path) as image:
  rgb=image.convert('RGB')
  # Known cabbiev2 fixture: the gold NOW PLAYING header is at y=10.
  # A track list can contain the same title, so text alone is insufficient.
  player_visible=all((lambda c:c[0]>160 and c[1]>100 and c[0]>c[2]*1.2)(rgb.getpixel(point))
                     for point in ((50,10),(270,10)))
  image.resize((image.width*3,image.height*3),Image.Resampling.NEAREST).save(path)
 text=run(['tesseract',str(path),'stdout','--psm','6']).stdout
 light_path=work/f'light-{screen_number:03}.png'
 ImageOps.grayscale(Image.open(path)).point(lambda p:0 if p>120 else 255).save(light_path)
 text+='\n'+run(['tesseract',str(light_path),'stdout','--psm','6']).stdout
 title=ImageOps.grayscale(Image.open(path).crop((45,25,940,70))).point(lambda p:0 if p>145 else 255)
 title_path=work/f'title-{screen_number:03}.png';title.save(title_path)
 text+='\n'+run(['tesseract',str(title_path),'stdout','--psm','7']).stdout
 # The theme mixes light text on gray with black text on the gold selection.
 # OCR the selected band separately so it cannot disappear in page segmentation.
 image=Image.open(path).convert('RGB')
 rows=[]
 for y in range(image.height):
  r,g,b=image.getpixel((image.width-60,y))
  if (r>160 and g>100 and r>b*1.2) or (r>140 and g>145 and b>120 and r+g+b>480):rows.append(y)
 bands=[]
 for y in rows:
  if not bands or y>bands[-1][-1]+1:bands.append([y])
  else:bands[-1].append(y)
 for index,band in enumerate(bands):
  if len(band)<8:continue
  selected=ImageOps.grayscale(image.crop((0,max(0,band[0]-2),image.width-5,min(image.height,band[-1]+3))))
  selected=selected.point(lambda p:255 if p>140 else 0)
  selected_path=work/f'selection-{screen_number:03}-{index}.png';selected.save(selected_path)
  band_text=run(['tesseract',str(selected_path),'stdout','--psm','6' if len(band)>70 else '7']).stdout
  selected_text+='\n'+band_text;text+='\n'+band_text
  # Catalog/database rows reserve an icon column; Wrapped cards do not.
  iconless_path=work/f'selection-text-{screen_number:03}-{index}.png'
  selected.crop((65,0,selected.width,selected.height)).save(iconless_path)
  band_text=run(['tesseract',str(iconless_path),'stdout','--psm','6' if len(band)>70 else '7']).stdout
  selected_text+='\n'+band_text;text+='\n'+band_text
 return text

def wait(*words,player=False):
 deadline=time.monotonic()+35;last=''
 while time.monotonic()<deadline:
  if sim.poll() is not None:raise AssertionError('Simulator exited; see '+str(work/'runtime.log'))
  last=screen()
  if all(seen(last,word) for word in words) and (not player or player_visible):return last
  time.sleep(.25)
 raise AssertionError('Expected '+repr(words)+'; got '+repr(last)+'; evidence: '+str(work))

def key(*keys):
 # Hold/release each button long enough for the simulator's input polling.
 for button in keys:
  run([xdo,'keydown',button]);time.sleep(.18)
  run([xdo,'keyup',button]);time.sleep(.45)

def choose(label):
 # Root selection can follow the previous screen; do not assume an index.
 for _ in range(12):
  screen()
  if seen(selected_text,label):
   key('Return');return
  key('Down')
 raise AssertionError('Cannot select '+label+'; evidence: '+str(work))

def context():
 run([xdo,'keydown','Return']);time.sleep(.85);run([xdo,'keyup','Return']);time.sleep(.35)
 wait('Context Menu','Play Similar Songs')

def record(message):
 passed.append(message);print('PASS: '+message,flush=True)

def start():
 global xserver,sim,window
 window=None
 xlog=(work/'xvfb.log').open('w')
 xserver=subprocess.Popen(['/workspace/setup/sysroot/usr/bin/Xvfb','-displayfd','1','-screen','0','800x600x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=xlog,text=True,env=env)
 assert select.select([xserver.stdout],[],[],15)[0],'Xvfb did not start'
 env['DISPLAY']=':'+xserver.stdout.readline().strip()
 slog=(work/'runtime.log').open('w')
 sim=subprocess.Popen([str(build/'rockboxui'),'--nobackground','--root',str(disk)],cwd=work,env=env,stdout=slog,stderr=subprocess.STDOUT)
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  p=subprocess.run([xdo,'search','--name','iPod 6G'],env=env,capture_output=True,text=True)
  if p.returncode==0:
   window=p.stdout.splitlines()[0];break
  time.sleep(.2)
 assert window,'Simulator window missing'
 run([xdo,'windowfocus',window])

def navigation_checks():
 wait('Database','Songs','Artists');key('Return')
 wait('Music','Songs','Albums');key('Return')
 wait('Songs','Alpha Song','Beta Song','Gamma Song');key('Down','Return')
 wait('Beta Song',player=True);context();key('Return')
 wait('Current Album','Alpha Song','Beta Song');key('Left')
 wait('Beta Song',player=True)
 record('Back from Current Album returns to the currently playing Beta Song')
 key('Return');wait('Songs','Beta Song','Delta Song','Gamma Song')
 key('Return');wait('Beta Song',player=True)
 record('Playing-screen browse resumes the original Songs selection, not the album')
 key('Escape');wait('Database','Songs','Artists');choose('Database')
 wait('Music','Songs','Albums')
 record('Explicit Home → Database opens its main menu after leaving the album')
 key('Return');wait('Songs','Alpha Song','Gamma Song');key('Down','Down','Down','Return')
 wait('Gamma Song',player=True);context();key('Return')
 wait('Current Album','Gamma Song');key('Escape')
 wait('Database','Songs','Artists');key('Return');wait('Music','Songs','Albums')
 record('Exiting the album through Home also leaves Database unlocked at its main menu')
 key('Escape');wait('Database','Songs','Artists');choose('Now Playing')
 wait('Gamma Song',player=True);context();key('Down','Return')
 wait('Current Artist','Random');key('Left');wait('Gamma Song',player=True)
 record('Back from Current Artist returns to the playing screen')
 key('Escape');wait('Database','Songs','Artists');choose('Database');wait('Music','Songs','Albums')
 record('Repeated Database entry remains at the main menu after an artist shortcut')
 (work/'results.json').write_text(json.dumps({'passed':passed,'evidence':str(work)},indent=2)+'\n')
 print('Evidence: '+str(work),flush=True)

def stop():
 for process in (sim,xserver):
  if process and process.poll() is None:
   process.terminate()
   try:process.wait(timeout=5)
   except subprocess.TimeoutExpired:process.kill();process.wait()


if __name__=="__main__":
 try:
  start();navigation_checks()
 finally:
  stop()
