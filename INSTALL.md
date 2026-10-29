# SNARTY-Y1-8 fullscreen video update

Place SNARTY-Y1-8-video.apk beside adb.exe. Pause music, then run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-8-video.apk
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Continue only after installation reports Success. Keep your working recovery APK. No firmware ZIP, uninstall, key-layout changes or data wipe is required. Finish copying files and safely eject/unplug USB before playback so Android can mount the card.

Database → Videos opens actual MP4 files in card-root Videos. The entire viewport is available to video, with aspect ratio preserved. Wheel/previous/next seeking or horizontal swipes show the bottom progress overlay; it hides after 1.2 seconds of inactivity. Center or a tap pauses/resumes. Back returns to Videos. Other menu/theme/history features remain.

Decoder runtime failures during prepare, playback, pause, seek, position polling and cleanup are caught and logged. Late inactive callbacks are ignored. These changes address identified crash paths; they cannot guarantee absence of every crash without a device trace and physical tests. To collect a video crash: `adb logcat -d -s RockboxVideo:E AndroidRuntime:E`.

The test ZIP contains Videos/SNARTY-video-test.mp4: extract and copy Videos to card root beside .rockbox. Test picture, sound, normal playback with no bar, wheel seek showing and hiding the bar, center pause/resume, Back, then reopening. Test normal startup after reboot as well. This build has not been run on a physical Y1 in the cloud.

The APK is API17-compatible, internal-only, ZIP-aligned and signed with the same platform certificate as recovery3. Source is included in snarty-y1-8-source.zip and this branch; Rockbox GPLv2-or-later and SNARTY CC BY-SA4 attribution remain.

Recovery APK: https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-recovery-3-cf45feb6/SNARTY-Y1-3-recovery.apk . Install with `adb install --no-streaming -r -f SNARTY-Y1-3-recovery.apk` without uninstalling.

## Decoder worker update
All vendor MediaPlayer operations now run on a dedicated worker. The UI reads cached state, so a blocking vendor open/seek/release no longer directly blocks the interface. The 30-second load timeout and Back remain on the UI thread; session checks suppress old callbacks. Worker scheduling is tested with a deliberately stalled fake decoder. The supplied device log had no crash entry, so the exact failing codec remains unknown. No new codecs or on-device conversion are included. A hung Android media server or hardware decoder can still require device recovery. Unsupported files may need conversion to H264 Baseline/AAC at 320x240. Physical acceptance remains pending.

## Startup/standby update
Startup retries automatically and no longer waits on native loading in the UI thread. The Retry storage button is removed; the status remains visible until the card is mounted and startup succeeds. The dedicated service stays foreground and holds a separate partial wake lock until teardown, while the screen may turn off. This consumes more standby battery. Idle poweroff is set to Off once, preserving other config bytes and later user changes. Video behavior remains revision7. Test unplugged boot without Retry, screen off for at least 10 minutes then wake, paused playback and resumed playback, plus Back/reentry from video. These checks require the physical Y1; kernel/hardware reboot causes are unconfirmed.
