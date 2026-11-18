#!/usr/bin/env python3
"""Real simulator playlist Shuffle with Play Selected First enabled, 26 files."""
import shutil,time,json,subprocess,re
import navigation_smoke as ui
playlist_dir=ui.disk/'Playlists';playlist_dir.mkdir()
long_track=ui.work/"long.flac"
subprocess.run(["ffmpeg","-v","error","-y","-stream_loop","29","-i",str(ui.disk/"Music/01.flac"),"-t","60","-c:a","flac",str(long_track)],check=True)
shutil.copy2(long_track,ui.disk/"Music/01.flac")
long_beta=ui.work/"long-beta.flac"
subprocess.run(["ffmpeg","-v","error","-y","-stream_loop","29","-i",str(ui.disk/"Music/02.flac"),"-t","60","-c:a","flac",str(long_beta)],check=True)
shutil.copy2(long_beta,ui.disk/"Music/02.flac")
paths=[]
for n in range(1,27):
 name=f'queue-{n:02}.flac';shutil.copy2(long_track,ui.disk/'Music'/name);paths.append('/Music/'+name)
(playlist_dir/'TwentySix.m3u8').write_text('\n'.join(paths)+'\n')
config=ui.disk/'.rockbox/config.cfg'
config.write_text(config.read_text()+'\nplay selected: on\nrepeat: off\n')
try:
 ui.start();ui.wait('Database','Songs','Artists');ui.choose('Database');ui.wait('Music','Songs','Albums');ui.choose('Playlists');ui.wait('Playlists','TwentySix');ui.key('Return')
 ui.wait('queue');ui.key('Up');ui.screen();assert ui.seen(ui.selected_text,'Shuffle'),ui.selected_text
 ui.key('Return');text=ui.wait('Alpha Song',player=True)
 deadline=time.monotonic()+20
 control=ui.disk/'.rockbox/.playlist_control'
 while time.monotonic()<deadline:
  data=control.read_text(errors='replace') if control.exists() else ''
  if any(line.startswith('S:') for line in data.splitlines()):break
  time.sleep(.2)
 # S:seed:first_index must persist origin zero for resumed playback too.
 shuffles=[line for line in data.splitlines() if line.startswith('S:')]
 assert shuffles and shuffles[-1].split(':')[2]=='0',data
 text=ui.screen();assert re.search(r'\b1\s+of\s+26\b',text),text
 ui.record('26-file playlist Shuffle starts at queue origin zero with Play Selected First on; control file persists zero origin')
 original=(playlist_dir/'TwentySix.m3u8').read_text()
 assert original == '\n'.join(paths)+'\n'
 ui.key('Escape');ui.wait('Database','Songs','Artists');ui.choose('Database');ui.wait('Music','Songs','Albums');ui.choose('Albums')
 ui.wait('Albums','Album A');ui.key('Return');ui.wait('Album A','Alpha Song');ui.key('Up');ui.screen();assert ui.seen(ui.selected_text,'Shuffle'),ui.selected_text
 ui.key('Return');ui.wait('Alpha Song',player=True)
 text=ui.screen();assert re.search(r'\b1\s*of',text),text
 album_control=control.read_text()
 assert [line.rsplit(':',1)[-1] for line in album_control.splitlines() if line.startswith('A:')]==['/Music/01.flac','/Music/02.flac'],album_control
 assert [line for line in album_control.splitlines() if line.startswith('S:')][-1].split(':')[2]=='0',album_control
 ui.record('Album Shuffle also starts at 1 of 2 while Play Selected First is on; saved 26-file playlist remains unchanged')
 (ui.work/'shuffle-results.json').write_text(json.dumps({'passed':ui.passed,'control':data,'screen':text},indent=2))
 print('Evidence: '+str(ui.work),flush=True)
finally:ui.stop()
