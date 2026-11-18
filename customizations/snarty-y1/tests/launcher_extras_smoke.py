#!/usr/bin/env python3
"""Exercise moved shortcuts/plugins through their new parent folder."""
import shutil,json
import navigation_smoke as ui
shutil.copytree(ui.source/'fonts',ui.disk/'.rockbox/fonts',dirs_exist_ok=True)
p=ui.disk/'.rockbox/config.cfg';p.write_text(p.read_text()+'\nfont: /.rockbox/fonts/15-KodeMono-SemiBold.fnt\n')
try:
 ui.start();ui.wait('Music','Videos','Podcasts','Settings');ui.key('Down','Down','Down','Return')
 ui.wait('Settings','Sound Settings');ui.key(*(['Down']*9));ui.wait('Additional Features');ui.key('Return')
 ui.wait('Additional Features','Shortcuts','Plugins');ui.key('Return');ui.wait('Additional Features','Shortcuts','Plugins')
 ui.record('Moved Shortcuts opens and returns to Additional Features when empty')
 ui.key('Down','Return');ui.wait('Plugins','Games','Applications','Demos');ui.key('Left');ui.wait('Additional Features','Shortcuts','Plugins')
 ui.record('Moved Plugins opens its existing Games/Applications/Demos menu and Back returns to Additional Features')
 (ui.work/'extras-results.json').write_text(json.dumps({'passed':ui.passed,'physical_fm':'Y1 Android app, not available in iPod simulator'},indent=2)+'\n')
 print('Evidence: '+str(ui.work),flush=True)
finally:ui.stop()
