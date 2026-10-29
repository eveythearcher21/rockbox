# SNARTY-Y1-9: automatic startup, standby and complete Shuffle

This APK updates the working Y1 application. It does not flash a ROM, replace wheel mappings, erase the card or uninstall the stock app. Keep the working recovery APK available.

## Install using Windows platform-tools

Place SNARTY-Y1-9-video.apk beside adb.exe. Pause music, then run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-9-video.apk
```

Only after Success:

```powershell
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Finish file transfers, safely eject the Windows storage drive and unplug USB before testing. Android needs the microSD card mounted locally; USB sharing, a missing card or a card error can still prevent startup. No manual storage Retry button is required: storage polls automatically, and pre-core startup failures retry after five seconds. Errors remain visible. Native-library loading and config reads no longer wait on the Android UI thread.

## What changed

The dedicated service stays foreground and holds a separate partial CPU wake lock while alive, even when playback is stopped. The screen may still go dark. This consumes more standby battery in exchange for avoiding deep-sleep and service-demotion risks. Teardown removes foreground status and releases its locks. A one-time migration appends idle poweroff: 0 to current/pending settings, preserving all existing bytes; later user changes to the timer are preserved. Explicit shutdown, sleep timer and low-battery behavior remain. Device/kernel reboot causes have not been confirmed from logs, so absence of every reboot is not guaranteed.

Album and playlist Shuffle and Play Similar Songs use a dedicated full-queue shuffle. Both the physical current index and logical first index reset to zero before shuffling all entries. Play Selected First and an inherited rotated queue origin no longer cause Shuffle to skip part of the queue. A 26-song shuffled queue starts at 1 of 26 and contains every entry once. Saved playlist files and ordinary selected-track playback retain their behavior.

Fullscreen aspect-fit video, the transient seek bar, and the asynchronous decoder worker from revision7 remain. This release adds no codecs or on-device transcoder; incompatible videos may need conversion to H264 Baseline/AAC at 320x240.

## Validate on the Y1

With USB unplugged and the card inserted, restart and verify the music menu appears automatically. Leave the screen off for at least ten minutes with music paused, then wake and resume it. Repeat while playing music. Check album and playlist Shuffle starts at 1 of N, with all N songs queued; keep Repeat Off when checking a complete pass. Check video Back/reentry too. These physical acceptance checks cannot be performed in the cloud.

Host tests exercise automatic retries, single/reentrant startup, cancellation, configuration preservation, decoder-thread stalls, local video policy, and JNI handling. The ASan/UBSan shuffle regression compiles actual production functions, reproduces the old origin mismatch, and checks 1..26 songs, every prior origin, both Play Selected First settings, 20 seeds and empty queues. Native/strict-API17 builds, signatures, alignment and public-download checksum are checked separately. See UPDATE-VALIDATION.json and source tests for precise evidence and limits.

## Recovery

The verified aligned pre-video APK remains available:
https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-recovery-3-cf45feb6/SNARTY-Y1-3-recovery.apk

Install it without uninstalling:
`adb install --no-streaming -r -f SNARTY-Y1-3-recovery.apk`

The one-time idle timer change remains an ordinary setting and can be changed later. The source package is snarty-y1-9-source.zip; source is also on this download branch. Rockbox GPLv2-or-later and SNARTY CC BY-SA4 attribution remain.

Simulator acceptance passed: actual catalog → 26-file playlist → Shuffle shows 1 of 26 and persists origin zero. Album Shuffle starts at 1, includes both album paths and persists origin zero. Play Selected First was on and the original saved playlist remained unchanged. The physical Y1 standby/reboot acceptance checks remain pending.
