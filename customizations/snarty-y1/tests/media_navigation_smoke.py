#!/usr/bin/env python3
"""Default real-row selection and bounded media-folder navigation."""
import shutil,sys
import navigation_smoke as ui

def selected(label):
 ui.screen()
 assert ui.seen(ui.selected_text,label),(label,ui.selected_text,str(ui.work))
def database():
 ui.key('Escape');ui.wait('Database','Songs','Artists');ui.choose('Database');ui.wait('Music','Songs','Albums')
try:
 ui.start();ui.wait('Database','Songs','Artists');ui.choose('Database')
 if '--folders' not in sys.argv:
  ui.wait('Music','Songs','Albums');ui.key('Return');ui.wait('Songs','Alpha Song')
  selected('Alpha Song');ui.key('Up');selected('Most Listened to');ui.key('Down')
  ui.record('Songs starts on Alpha Song; bracketed Most Listened to remains above it')
  database();ui.key('Down','Down','Return');ui.wait('Artists','Artist A')
  selected('Artist A');ui.key('Return');ui.wait('Artist A','Album A','Album B');selected('Album A')
  ui.key('Up');selected('Random');ui.key('Down','Return');ui.wait('Album A','Alpha Song');selected('Alpha Song')
  ui.key('Up');selected('Shuffle');ui.key('Down','Left');ui.wait('Artist A','Album A');selected('Album A')
  ui.record('Artist, nested album list and album tracks start below bracketed actions; Back preserves selection')
 database();ui.choose('Search');ui.wait('Search','Artist','Song Title');ui.key('Return')
 ui.wait('Search Artists','First Letter');ui.key('Return');ui.wait('Numeric');ui.key('Down','Return')
 ui.wait('Artist A');selected('Artist A')
 ui.record('First-letter Artist search starts on the first real matching artist')
 database();ui.choose('Videos');ui.wait('Videos')
 assert (ui.disk/'Videos').is_dir()
 ui.key('Left');ui.wait('Music','Videos','Podcasts');selected('Videos')
 ui.record('Videos creates a storage-root folder and Back returns to Database')
 ui.choose('Podcasts');ui.wait('Podcasts');assert (ui.disk/'Podcasts').is_dir()
 ui.key('Left');ui.wait('Music','Podcasts');selected('Podcasts')
 shutil.copy2(ui.disk/'Music/02.flac',ui.disk/'Podcasts/Episode.flac')
 ui.key('Return');ui.wait('Podcasts','Episode');selected('Episode');ui.key('Return')
 ui.wait('Beta Song',player=True)
 ui.record('Podcasts creates its root folder and plays a copied audio episode')
 database();ui.wait('Music','Songs','Albums')
 ui.record('Database remains usable after podcast playback')
 print('Evidence: '+str(ui.work),flush=True)
finally:ui.stop()
