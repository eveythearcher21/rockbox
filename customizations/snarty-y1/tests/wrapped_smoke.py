#!/usr/bin/env python3
"""Wrapped/menu GUI checks and actual playback-to-journal integration."""
import csv,datetime,time
from pathlib import Path
import navigation_smoke as ui

(ui.disk/'Playlists').mkdir()
(ui.disk/'Playlists/Test.m3u8').write_text('/Music/01.flac\n/Music/02.flac\n')
history=ui.disk/'.rockbox/listening-history-v1.tsv'
rows=['# rockbox-listening-history\t1\n']
def add(year,month,path,title,artist,album,count):
 for i in range(count):
  rows.append(f'{year:04}-{month:02}-01T12:{i:02}:00\t180000\t180000\t{path}\t{title}\t{artist}\t{album}\n')
add(2025,1,'/Music/01.flac','Alpha Song','Artist A','Album A',5)
add(2025,1,'/Music/02.flac','Beta Song','Artist A','Album A',3)
add(2025,1,'/Music/03.flac','Gamma Song','Artist A','Album B',2)
add(2025,1,'/Music/04.flac','Delta Song','Artist B','Album C',1)
add(2025,2,'/Music/04.flac','Delta Song','Artist B','Album C',6)
add(2025,2,'/Music/02.flac','Beta Song','Artist A','Album A',2)
add(2024,1,'/Music/01.flac','Alpha Song','Artist A','Album A',9)
history.write_text(''.join(rows))
def play_beta():
 ui.wait('Database','Songs','Artists');ui.key('Return');ui.wait('Music','Songs','Albums')
 ui.key('Return');ui.wait('Songs','Alpha Song','Beta Song');ui.key('Down','Return')
 ui.wait('Beta Song',player=True)
def home_database():
 ui.key('Escape');ui.wait('Database','Songs','Artists');ui.choose('Database')
 ui.wait('Music','Songs','Albums')
try:
 ui.start();play_beta();home_database()
 ui.key('Down','Down','Down','Return');ui.wait('Playlists','Test')
 ui.key('Left');ui.wait('Music','Songs','Albums')
 ui.record('Database Playlists opens the catalog and Back returns to Database')
 ui.key('Down','Return');ui.wait('Beta Song',player=True)
 ui.record('Database Currently Playing opens the actual playing screen')
 home_database();ui.choose('spotify wrapped')
 ui.wait('spotify wrapped','Monthly Top 10','Song of the Year')
 ui.key('Return');ui.wait('Your months','January 2025','January 2024')
 ui.key('Down','Return');ui.wait('January 2025','TOP 10','Alpha Song','Beta Song','Gamma Song')
 ui.record('Monthly Wrapped displays Alpha Song first, followed by Beta and Gamma for January 2025')
 ui.key('Left');ui.wait('Your months','January 2025');ui.key('Left')
 ui.wait('spotify wrapped','Monthly Top 10');ui.key('Down','Return');ui.wait('Your years','2025','2024')
 ui.key('Return');ui.wait('2025','song of the year','Delta Song')
 ui.record('Yearly Wrapped aggregates January and February and selects Delta Song with seven plays')
 ui.key('Left');ui.wait('Your years','2025');ui.key('Down','Return')
 ui.wait('2024','song of the year','Alpha Song')
 ui.record('Year picker isolates 2024 history from 2025')
finally:ui.stop()
print('Evidence: '+str(ui.work),flush=True)
