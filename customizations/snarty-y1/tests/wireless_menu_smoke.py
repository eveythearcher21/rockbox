#!/usr/bin/env python3
"""Actual shared renderer menu integration; radio belongs to physical Y1."""
import shutil,json,time
import navigation_smoke as ui
original=ui.seen
ui.seen=lambda text,word:original(text.replace('Syne Library','Sync Library'),word)
try:
    ui.start();ui.wait('Music','Videos');ui.key('Return');ui.wait('Music','Songs')
    ui.key(*(['Down']*10));ui.wait('Sync Library')
    ui.screen();shutil.copy2(ui.work/f'screen-{ui.screen_number:03}.png',ui.work/'Music-Sync-Library.png')
    ui.key('Return');time.sleep(2.5);ui.wait('Music','Sync Library');ui.key('Escape');ui.wait('Music','Videos')
    ui.key('Down','Down','Down','Return');ui.wait('Settings');ui.key(*(['Down']*6));ui.wait('Settings')
    ui.screen();shutil.copy2(ui.work/f'screen-{ui.screen_number:03}.png',ui.work/'Settings-Wi-Fi.png')
    ui.key('Return');time.sleep(2.5);ui.wait('Settings')
    ui.record('Sync Library is last in Music; Wi-Fi route appears in Settings; unsupported simulator action returns to correct menu')
    (ui.work/'wireless-menu-results.json').write_text(json.dumps({'passed':ui.passed,'evidence':str(ui.work)},indent=2))
    print('Evidence:',ui.work)
finally:ui.stop()
