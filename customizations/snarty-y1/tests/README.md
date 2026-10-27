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
