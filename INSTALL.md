# SNARTY-Y1-6 fullscreen video update

Place SNARTY-Y1-6-video.apk beside adb.exe. Pause music, then run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-6-video.apk
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Continue only after installation reports Success. Keep your working recovery APK. No firmware ZIP, uninstall, key-layout changes or data wipe is required. Finish copying files and safely eject/unplug USB before playback so Android can mount the card.

Database → Videos opens actual MP4 files in card-root Videos. The entire viewport is available to video, with aspect ratio preserved. Wheel/previous/next seeking or horizontal swipes show the bottom progress overlay; it hides after 1.2 seconds of inactivity. Center or a tap pauses/resumes. Back returns to Videos. Other menu/theme/history features remain.

Decoder runtime failures during prepare, playback, pause, seek, position polling and cleanup are caught and logged. Late inactive callbacks are ignored. These changes address identified crash paths; they cannot guarantee absence of every crash without a device trace and physical tests. To collect a video crash: `adb logcat -d -s RockboxVideo:E AndroidRuntime:E`.

The test ZIP contains Videos/SNARTY-video-test.mp4: extract and copy Videos to card root beside .rockbox. Test picture, sound, normal playback with no bar, wheel seek showing and hiding the bar, center pause/resume, Back, then reopening. Test normal startup after reboot as well. This build has not been run on a physical Y1 in the cloud.

The APK is API17-compatible, internal-only, ZIP-aligned and signed with the same platform certificate as recovery3. Source is included in snarty-y1-6-source.zip and this branch; Rockbox GPLv2-or-later and SNARTY CC BY-SA4 attribution remain.

Recovery APK: https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-recovery-3-cf45feb6/SNARTY-Y1-3-recovery.apk . Install with `adb install --no-streaming -r -f SNARTY-Y1-3-recovery.apk` without uninstalling.
