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
```

Dependencies: Pillow, Tesseract, ImageMagick import, local Xvfb and xdotool from onboarding. GUI checks preserve screenshots and runtime logs in the reported /tmp evidence directory. OCR tolerates only known bitmap-font menu spelling errors; selected titles, periods and rank order are asserted. Play-count arithmetic is checked by the portable C tests, because bitmap digits such as 5/7 can be misread by OCR. Wrapped fixtures contain artificial historical dates only inside the private test disk; no fake journal is distributed to the player.

Navigation checks cover Album/Artist Back → playing screen, restoration of the original song-list selection, and explicit Database reset after both Back and Home exits. Wrapped checks cover Database Playlists/Currently Playing actions, monthly ordering, and separate yearly winners. Journal checks enable Gather Runtime Data, play a real short fixture track to completion, validate its timestamped seven-field rows, then open the live results in Wrapped.

These checks do not validate Y1 firmware installation, hardware button double-click timing, color rendering on the physical LCD, root execution of the diagnostic, USB negotiation, or car projection. Use the target-specific CheckWPS parser for 480x360 skin syntax. Host updater simulation mocks privileged system/package/reboot operations.
