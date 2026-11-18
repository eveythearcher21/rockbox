#!/usr/bin/env python3
"""Actual playback-to-journal integration, without seeded statistics."""
import csv,datetime,time
from pathlib import Path
import navigation_smoke as ui
history=ui.disk/'.rockbox/listening-history-v1.tsv'
def play_beta():
 ui.wait('Database','Songs','Artists');ui.key('Return');ui.wait('Music','Songs','Albums')
 ui.key('Return');ui.wait('Songs','Alpha Song','Beta Song');ui.key('Down','Return')
 ui.wait('Beta Song',player=True)
def home_database():
 ui.key('Escape');ui.wait('Database','Songs','Artists');ui.choose('Database')
 ui.wait('Music','Songs','Albums')
# A fresh log with the real finish-event recorder enabled, not seeded statistics.
if history.exists():history.unlink()
with (ui.disk/'.rockbox/config.cfg').open('a') as f:f.write('\ngather runtime data: on\nstart in screen: root\n')
try:
 ui.start();play_beta()
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  if history.exists() and len(history.read_text().splitlines())>=2:break
  time.sleep(.25)
 assert history.exists(),'Actual playback did not create the journal'
 lines=history.read_text().splitlines();assert lines[0]=='# rockbox-listening-history\t1'
 data=list(csv.reader(lines[1:],delimiter='\t'));assert data
 for row in data:
  assert len(row)==7,row
  datetime.datetime.fromisoformat(row[0])
  assert row[3]=='/Music/02.flac' and row[4]=='Beta Song',row
  assert int(row[1])>0 and int(row[2])>0,row
 ui.record('Actual completed playback appends timestamped Beta Song events to the export journal')
 home_database();ui.choose('spotify wrapped')
 ui.wait('spotify wrapped','Monthly Top 10');ui.key('Return');ui.wait('Your months')
 ui.key('Return');ui.wait('TOP 10','Beta Song','plays')
 ui.record('Wrapped reads and displays the actual playback-generated journal')
finally:ui.stop()
print('Evidence: '+str(ui.work),flush=True)
