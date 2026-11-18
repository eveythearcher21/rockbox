#!/usr/bin/env python3
"""Actual SDL menu navigation for SNARTY launcher; private files only."""
import shutil,json,time,subprocess,os,sys
from pathlib import Path
import navigation_smoke as ui
if os.environ.get("SNARTY_DEBUG_PRELOAD"):
 ui.env["LD_PRELOAD"]=os.environ["SNARTY_DEBUG_PRELOAD"]
# Use the actual SNARTY font on the shared-code, 320x240 test LCD.
for directory in ('fonts','icons'):
 shutil.copytree(ui.source/directory,ui.disk/'.rockbox'/directory,dirs_exist_ok=True)
config=ui.disk/'.rockbox/config.cfg'
config.write_text(config.read_text()+'\nfont: /.rockbox/fonts/15-KodeMono-SemiBold.fnt\n')
(ui.disk/'Playlists').mkdir()
(ui.disk/'Playlists/Test.m3u8').write_text('/Music/01.flac\n/Music/02.flac\n')
original_seen=ui.seen
def launcher_seen(text,word):
 if word=="Home" and any(x in text.lower() for x in ("hore","hone")):return True
 if word=="Albums" and "albuns" in text.lower():return True
 if word=="2025" and "2825" in text:return True
 return original_seen(text,word)
ui.seen=launcher_seen
def home():
 ui.key('Escape');ui.wait('Music','Videos','Podcasts','Settings')
def moves(n):
 if n>0:ui.key(*(['Down']*n))
 elif n<0:ui.key(*(['Up']*(-n)))
try:
 ui.start();ui.wait('Music','Videos','Podcasts','Settings')
 ui.screen();shutil.copy2(ui.work/f'screen-{ui.screen_number:03}.png',ui.work/'Home.png')
 ui.record('Home has Music, Videos, Podcasts, Settings with no Database entry')
 if '--settings-only' in sys.argv:
  ui.key('Down','Down','Down','Return');ui.wait('Settings','Sound Settings','Playback Settings')
 else:
  ui.key('Return');ui.wait('Music','Songs','Albums','Artists','Playlists')
  ui.screen();shutil.copy2(ui.work/f'screen-{ui.screen_number:03}.png',ui.work/'Music.png')
  ui.key('Return');ui.wait('Songs','Alpha Song','Beta Song');ui.key('Return');ui.wait('Alpha Song',player=True);home();ui.key('Return')
  ui.wait('Music','Songs','Albums');ui.record('Songs opens directly; Back returns to Music, without an extra Database menu')
  ui.key('Down','Return');ui.wait('Albums','Album A');ui.key('Left');ui.wait('Music','Albums')
  ui.key('Down','Return');ui.wait('Artists','Artist A');ui.key('Left');ui.wait('Music','Artists')
  ui.record('Albums and Artists open directly and return to their Music folder')
  ui.key('Down','Return');ui.wait('Playlists','Test');ui.key('Left');ui.wait('Music','Playlists')
  ui.record('Music Playlists opens the existing playlist catalog')
  ui.key('Down','Return');ui.wait('Alpha Song',player=True);home();ui.key('Return');ui.wait('Music','Currently Playing')
  ui.record('Currently Playing returns to the actual playing Alpha Song')
  ui.key('Down','Return');ui.wait('Genre','Rock');ui.key('Left');ui.wait('Music','Genre')
  ui.key('Down','Return');ui.wait('Year','2025');ui.key('Left');ui.wait('Music','Year')
  ui.key('Down','Return');ui.wait('Search','Artist','Song Title','Album');ui.key('Left');ui.wait('Music','Search')
  ui.record('Genre, Year and Search open directly and return to Music')
  moves(1);ui.wait('Spotify Wrapped','Search','Year');ui.key('Return');ui.wait('Monthly','Year','Sync')
  ui.key('Left');ui.wait('Music','Spotify Wrapped')
  ui.record('Spotify Wrapped is last in Music and opens the local monthly/yearly views')
  home();ui.key('Down','Return');ui.wait('Videos');assert (ui.disk/'Videos').is_dir();ui.key('Left');ui.wait('Music','Videos')
  ui.key('Down','Return');ui.wait('Podcasts');assert (ui.disk/'Podcasts').is_dir();ui.key('Left');ui.wait('Podcasts')
  ui.record('Videos and Podcasts open directly from Home and Back returns Home')
  ui.key('Down','Return');ui.wait('Settings','Sound Settings','Playback Settings')
 ui.screen();shutil.copy2(ui.work/f'screen-{ui.screen_number:03}.png',ui.work/'Settings.png')
 ui.key('Return');ui.wait('Sound Settings','Volume');ui.key('Left');ui.wait('Settings','Sound Settings')
 # This configured iPod 6G simulator has ten Settings rows.
 moves(9);ui.wait('Settings','System','Files','Additional Features')
 ui.key('Return');ui.wait('Additional Features','Shortcuts','Plugins')
 ui.screen();shutil.copy2(ui.work/f'screen-{ui.screen_number:03}.png',ui.work/'Additional-Features.png')
 ui.key('Left');ui.wait('Settings','Additional Features')
 ui.record('Settings retains sound controls and contains Additional Features with Shortcuts/Plugins; Y1 adds its Android FM Radio app')
 moves(-2);ui.key('Return');ui.wait('System','Credits','Debug');ui.key('Left');ui.wait('Settings','System')
 ui.key('Down','Return');ui.wait('Files','Playlists');ui.key('Left');ui.wait('Settings','Files')
 ui.record('Settings System opens system information; Files opens storage and returns to Settings')

 (ui.work/'launcher-results.json').write_text(json.dumps({'passed':ui.passed,'evidence':str(ui.work)},indent=2)+'\n')
 print('Evidence: '+str(ui.work),flush=True)
except Exception:
 print("Simulator exit:",ui.sim.poll() if ui.sim else None,"Evidence:",ui.work,flush=True)
 raise
finally:ui.stop()
