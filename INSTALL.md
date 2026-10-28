# SNARTY-Y1-5: API17 video application update

The owner has confirmed that the aligned pre-MP4 recovery APK starts and the Rockbox wheel mapping works. This update retains that mapping and the same platform certificate/versionCode. It is an APK update through Android's package manager, not a ROM or SD firmware update.

## Install on Windows

Keep your card backup and SNARTY-Y1-3-recovery.apk available. Pause music first. Place SNARTY-Y1-5-video.apk in the platform-tools folder beside adb.exe and run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-5-video.apk
```

The -r option updates the application while retaining its data. The -f option puts the app in internal storage; music/videos stay on the card. Android extracts the matching native libraries from the same APK. Stop on an installation error and report it; do not uninstall, change key layouts, or flash firmware to force installation.

After Success, open it:

```powershell
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Do not run the old firmware-update ZIP or change the working wheel mapping. If the new screen says USB file transfer is active, finish your transfers, safely eject the card's Windows drive, and unplug the USB cable. Android will remount the card and Rockbox will retry. Missing/shared/read-only storage now has a visible waiting screen instead of the old main-thread SD sleep loop.

## Test an actual video

SNARTY-video-test.zip contains Videos/SNARTY-video-test.mp4, a self-generated 20-second moving picture with a quiet tone (320x240, 25fps, H.264 Constrained Baseline L2, AAC-LC; one-second keyframes). Extract the ZIP on your computer. Copy its Videos folder to the card root, beside .rockbox. Do not put the ZIP itself in Videos, put Videos inside .rockbox, or rename the test ZIP update.zip. If an earlier test clip exists, this optional clip replaces only that same test filename.

When using Windows file-transfer mode, finish copying and safely eject/unplug before playing. Alternatively, with the card mounted for Android and ADB still connected, copy the extracted MP4 using:

```powershell
.\adb.exe push .\Videos\SNARTY-video-test.mp4 /sdcard/Videos/
```

If that reports a permission or missing-storage error, stop and report it. The previously used vdc unshare/mount commands can restore Android access after Windows safely ejects; no formatting is needed.

Open Database → Videos → SNARTY-video-test.mp4. Check picture and sound, moving elapsed time/progress, center/Play pause/resume, wheel five-second and previous/next ten-second seeking, and Back returning to the Videos list. Then test your own H.264/AAC MP4. Other codec profiles depend on the Y1's installed decoder. Decoder errors now include a numeric code; diagnostic logs use the RockboxVideo tag.

The player does not download video. An MP3 contains audio only; renaming it MP4 cannot restore the picture. The other sync/downloader app has not been modified.

## What changed

- All production Java/resources compile against Android API17, matching the reported device. Config reading uses compatible finally/close handling rather than the newer AutoCloseable contract.
- Startup uses StorageStartGate with delayed retries; no main-thread SD polling sleep. Waiting input stays in Android mode, avoids native framebuffer/button calls before initialization, and returns to Rockbox mode for the native screen. Native input is not enabled during resource extraction. Retry and the existing stock-switch flow remain available.
- Native library resources follow ApplicationInfo.nativeLibraryDir, matching Android's loader. Native loading happens in the service with an error path; load failure releases the startup lock.
- APK is internal-only and ZIP-aligned before signing. No system firmware or key-layout replacement is part of installation.
- Videos/Podcasts and the MP4 open path check Android storage state, rather than silently browsing unavailable storage.
- Internal Android MP4 playback retains SNARTY colors, seekable progress, elapsed/total time, play/pause/replay, hardware seeking, Back, and music queue preservation. MPEG playback and previous theme/menu/history features remain.

## Validation and limits

Native build, strict API17 Java/resource compilation, storage-gate and video policy/timeline unit tests, ASan/UBSan JNI bridge tests, alignment, API17/full signatures, APK payload inspection and main-library API17 import checks passed. The clip was probed and fully decoded on the host. No Android emulator or attached Y1 is available here: physical revision-5 startup, waiting-screen controls and video decoding/audio/seek/Back remain device acceptance tests. See UPDATE-VALIDATION.json.

## Recovery

Keep the verified aligned pre-MP4 APK: https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-recovery-3-cf45feb6/SNARTY-Y1-3-recovery.apk . With storage mounted to Android, it can be reinstalled with `adb install --no-streaming -r -f SNARTY-Y1-3-recovery.apk` without uninstalling. This deliberately retains versionCode 1 for a straightforward return to the working baseline.

If you need the stock interface, first finish transfers and safely eject the Windows card drive. The device's existing `adb shell "su -c 'sh /data/data/switch-to-stock.sh'"` restores the stock key layout, switches app enable states, and reboots. That exact recovery path was confirmed working on this device. Merely enabling the stock app without restoring its mapping leaves its wheel incorrect.

Source and tests are included in snarty-y1-5-source.zip and this download branch. Rockbox code remains GPLv2 or later; SNARTY attribution and CC BY-SA 4.0 credits are retained.
