# SNARTY Y1 regression checks

These scripts use the retained cloud onboarding tools and controlled four-track fixture. They run the shared-code iPod 6G simulator at 320x240, not a physical Y1. They create isolated /tmp copies and private Xvfb displays; original simulator music, settings and database are retained. Dummy audio exercises decoding/playback without physical audio output.

Run the portable statistics tests with a host C compiler:

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -g -I apps apps/listening_stats.c customizations/snarty-y1/tests/listening_stats_test.c -o /tmp/snarty-stats-test
/tmp/snarty-stats-test
```

The codec tests cover escaping, UTF-8 limits, malformed dates/records, calendar filtering, top ten, deterministic ties, collision path verification, full tables and saturated counters.

After building /workspace/builds/ipod6g-sim with the current source, run:

```sh
python3 customizations/snarty-y1/tests/navigation_smoke.py
python3 customizations/snarty-y1/tests/wrapped_smoke.py
python3 customizations/snarty-y1/tests/journal_smoke.py
python3 customizations/snarty-y1/tests/media_navigation_smoke.py
```

Dependencies: Pillow, Tesseract, ImageMagick import, local Xvfb and xdotool from onboarding. GUI checks preserve screenshots and runtime logs in the reported /tmp evidence directory. OCR tolerates only known bitmap-font menu spelling errors and fixture Artist A/Album A letter A misread as 4; selected titles, periods and rank order are asserted. Play-count arithmetic is checked by the portable C tests, because bitmap digits such as 5/7 can be misread by OCR. Wrapped fixtures contain artificial historical dates only inside the private test disk; no fake journal is distributed to the player.

Navigation checks cover Album/Artist Back → playing screen, restoration of the original song-list selection, and explicit Database reset after both Back and Home exits. Wrapped checks cover Database Playlists/Currently Playing actions, monthly ordering, and separate yearly winners. Journal checks enable Gather Runtime Data, play a real short fixture track to completion, validate its timestamped seven-field rows, then open the live results in Wrapped.

These checks do not validate Y1 firmware installation, hardware button double-click timing, color rendering on the physical LCD. Use the target-specific CheckWPS parser for 480x360 skin syntax. Host updater simulation mocks privileged system/package/reboot operations.

The revision 3 media navigation check exercises default Songs/Artist/Album selection, first-letter search, scrolling up to bracketed actions, automatic root-folder creation, Back to Database, and local podcast audio playback. Hardware folder paths are /sdcard/Videos and /sdcard/Podcasts; the simulator uses /Videos and /Podcasts within its private fixture.

## Y1 internal MP4 player (revision 4)

The Java policy/timeline and native JNI bridge tests run on the host. They do not emulate VideoView, decode on Android, or verify hardware buttons. Activate the onboarding tools, then run:

```sh
source /workspace/setup/env.sh
mkdir -p /tmp/snarty-video-java-test
javac -d /tmp/snarty-video-java-test android/y1/src/org/rockbox/VideoTimeline.java android/y1/src/org/rockbox/VideoFiles.java customizations/snarty-y1/tests/VideoPlayerTest.java
java -cp /tmp/snarty-video-java-test org.rockbox.VideoPlayerTest
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -g -I customizations/snarty-y1/tests/jni-stubs -I firmware/target/hosted/android -I /workspace/setup/sysroot/usr/lib/jvm/java-17-openjdk-amd64/include -I /workspace/setup/sysroot/usr/lib/jvm/java-17-openjdk-amd64/include/linux firmware/target/hosted/android/video-android.c customizations/snarty-y1/tests/video_bridge_test.c -o /tmp/snarty-video-bridge-test
/tmp/snarty-video-bridge-test
```

Build target 310 with VERSION=SNARTY-Y1-4, compile Java, package/sign the APK and verify its certificate. Hardware acceptance requires copying the provided 20-second H.264 Baseline/AAC-LC test clip to the card-root Videos folder, selecting it, verifying picture/sound/progress, center pause/resume, wheel/previous/next seeking, background/reentry and Back to Videos. Also test an audio-only MP4 and an unsupported codec: they should display an error rather than launch music playback. The desktop iPod simulator cannot validate this Android Activity.

## Revision 5 storage startup and API17

The actual device was identified as Android SDK17. USB storage sharing was observed as state 7 Shared-Unmounted at /storage/sdcard0; returning it to Android restored .rockbox accessibility. The aligned pre-MP4 recovery APK was installed successfully through the package manager, and its menu/wheel were confirmed working after restoring the matching mapping. This establishes a recovery baseline, not proof that the new video Activity decodes on hardware.

Compile all production Java/resources with ANDROID_PLATFORM_VERSION=17. This caught and removed try-with-resources config code that relies on a newer AutoCloseable contract. The service now follows ApplicationInfo.nativeLibraryDir. Run StorageStartGateTest with StorageStartGate.java using the host JDK. It tests unavailable-card polling, mounted transition, repeated/reentrant requests, cancellation (including an already-queued callback), immediate mounted startup, and manual retry after a failed library start. The real JNI bridge test now checks the mounted/unavailable/error result as well as UTF-8 video launch.

Build and sign a paired APK, ZIP-align before signing, verify API17 JAR signatures and final alignment, inspect internal-only install location and API17 resource version, and compare required main-library symbols against NDK API17 public exports. Do not overwrite system APK/libraries manually for deployment. Use adb install --no-streaming -r -f so Android installs matching native libraries internally without changing the wheel mapping.

New device acceptance: ordinary boot/menu/wheel; a responsive storage waiting screen when started with USB sharing or no card; automatic startup after safe eject/unplug/remount; the supplied H.264 Baseline/AAC test clip's picture, sound, progress, pause/seek and Back. Videos/Podcasts while storage is unavailable should show a storage message. Physical acceptance of revision 5 remains pending until the owner reports these outcomes. The host tests do not emulate Android VideoView or the Y1 decoder.

## Revision 7 decoder thread

Run `python3 customizations/snarty-y1/tests/async_video_smoke.py` in the cloud setup. It compiles the actual AsyncVideoView against small recording Android stubs and runs a fake vendor decoder. It asserts all decoder calls execute off the test UI thread, cached metadata, seek-error routing, stale completion suppression, and immediate close while setDataSource is deliberately blocked. Poll submissions are bounded. This is a scheduling/lifecycle regression test, not an Android emulator or codec compatibility test.

## Revision 8 automatic startup

Compile StorageStartGateTest and StartupConfigTest with their production helper classes and run both on the host. Tests cover automatic delayed retries after synchronous/asynchronous pre-core failures, mounted transitions, single/reentrant startup, cancellation, append-only config migration, preserved UTF8/unrelated bytes, later user-selected timers, fresh settings directories and inaccessible-storage errors. These tests do not measure the physical device's idle battery use or prove its kernel/firmware never reboots.

## Full-queue shuffle regression
Run `python3 customizations/snarty-y1/tests/shuffle_all_test.py` to compile actual production shuffle functions against recording host dependencies with ASan/UBSan. It reproduces the old origin mismatch, then verifies complete unique permutations and current/logical/persisted origin zero for 1..26 entries, every prior origin, both Play Selected First values and 20 seeds, plus empty queues. Run `python3 customizations/snarty-y1/tests/shuffle_queue_smoke.py` after rebuilding the simulator for real 26-file catalog/viewer Shuffle and WPS/control-file assertions.

## Launcher revision 10

Rebuild /workspace/builds/ipod6g-sim, then run launcher_smoke.py and launcher_animation.py with the onboarding environment enabled. They use private fixtures and the 15-KodeMono font appropriate to the simulator's 320px LCD (the Y1 uses its installed 480px theme font). Real screenshots, menu/content/back-navigation assertions, active playback and selection-animation frames are retained under the reported /tmp path. The simulator has no Android FM app; Y1's Radio route requires physical testing.

Run launcher_font_test.py and root_selection_test.py to compile the actual production functions against recording host dependencies under ASan/UBSan. They check resolved-ID font pinning across cache reads and clipped glyph rendering, plus bounded configured-menu selection with missing/sparse routes. The latter reproduces the empty-root-entry crash exposed by new routes.

## Revision11 playback features

Run sync_library_test.py for actual C-reader/reference-writer cross-language ASan/UBSan checks (including storage aliases and corrupt input) and explicit word-interval encoding. Compile/run PairedAssetsTest.java with production PairedAssets.java for migration preflight, backups, preserved settings and once-only behavior. After rebuilding the shared simulator, run playback_features_smoke.py for true recent rank playback, color album cards/detail, one-click sheet/Back, synced recommendation deduplication/preserved playback, actual word-highlight changes and current-queue navigation. Fixtures are private and synthetic. Known bitmap-font OCR substitutions are explicit in the harness. The companion's provider access/forced alignment and an actual Y1 remain separate acceptance checks.

## Revision15 selected-song menus and artwork

Run `artist_images_test.py` for actual Java conversion/cache policy using ImageIO-backed Android adapters, and compile/run PairedAssetsTest with production PairedAssets.java for the additional once-only lyrics plugin update/backups. Rebuild the shared simulator, run navigation14_smoke.py to create its expanded fixture, then set SNARTY_FIXTURE to that reported simdisk path and run navigation15_smoke.py. It verifies selected-song metadata/actions without replacing the playing queue, correct Album/Artist return navigation, manual selected lyric preview, selected radio membership/order, named portrait JPEG and PNG-cache lookup, four distinct playlist tiles/duplicate-album skipping/relative paths, and held playlist-song menus. Synthetic artwork/media only; physical Y1 and actual Android bitmap decoder/performance remain separate acceptance.

## Revision16 Wi-Fi and paired sync

Run `make dep` before incremental native builds after adding source/generated icons, so all new source/header dependencies enter the build database. Build API17 Y1 and the shared simulator. Run `wireless_menu_smoke.py` for real Music/Settings menu rendering; its bitmap-font OCR explicitly normalizes only Sync→Syne. The Wi-Fi screenshot is visually inspected because full-screen OCR misreads the selected Wi-Fi label. The simulator route reports its lack of Android Wi-Fi support.

Set SNARTY_JSON_JAR to an upstream org.json implementation JAR (tested20240303), activate the setup JDK, then run `wireless_sync_test.py`. This compiles actual WirelessSync/WirelessProtocol, runs actual Python bridge HTTP/HMAC transfers and invokes wireless_android_test.py for the actual controller against recording Android service adapters. It does not emulate the chipset/binder. Run `youtube_wireless_test.py` with the desktop wireless-requirements dependencies on PYTHONPATH and FFmpeg on PATH for real MP3 tag/JPEG/LRC/binary encoding with a synthetic recording provider. No account content/authentication is used by these fixtures.

Compile/run wireless_bridge_test.c with actual firmware/target/hosted/android/wireless-android.c, the existing jni-stubs, JDK JNI include/linux headers and ASan/UBSan, as for video_bridge_test.c. It checks UTF8 input/output, dispatch, bounds and JNI reference/exception cleanup. Verify the signed APK against API17 and current certificate, final ZIP alignment and exact paired assets. Physical480×360 radio/router/idle/decoder, Windows launcher/firewall and real provider-account acceptance remain pending.
