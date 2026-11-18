# SNARTY Y1 rebrand12 test

For Innioasis Y1, Android4.2/API17,480x360. Back up .rockbox and retain the prior APK. Place SNARTY-Y1-12-rebrand-test.apk beside adb.exe, pause playback, then run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-12-rebrand-test.apk
```

Only after Success:

```powershell
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Finish/eject Windows transfers, then unplug so Android can mount the card. The once-only v12 migration backs up replaced assets/settings as .before-snarty12, installs the paired theme/plugin and preserves music/history and unrelated settings. Do not uninstall, flash firmware or change wheel mappings. Later user theme changes are retained.

Read REBRAND-12.md for implemented UI, asset paths and limits. ROCKBLOCK-SYNCER-PROMPT.md is the full implementation prompt for the other chat. Artist portraits and podcast grouping require compatible sync assets; legacy flat podcast files are not moved automatically. The idle-image path is .rockbox/snarty/screensaver.jpg, exact480x360 JPEG, <=2MiB,60seconds idle. Next input dismisses it; hardware acceptance pending.

Shared native lists are themed; plugin/game/editor-owned screens and Android system dialogs are not all redesigned. Android storage wait/status has themed controls. Device video/standby/idle input handling remain physical acceptance checks. Previews use synthetic data on the320x240 shared simulator.

Rollback: update-install the prior matching-signature APK without uninstalling. Restore saved card settings/theme if reverting the appearance. Revision11 remains available:
https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-playback-11-d1666147/SNARTY-Y1-11-playback-test.apk
