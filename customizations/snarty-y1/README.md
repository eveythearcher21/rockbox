# SNARTY Y1 customization

This is a development build for the **Innioasis Y1, 480×360**, based on the selected `rebase-upstream` checkout. It is an Android Rockbox application, not a replacement Android OS or a full ROM. Do not flash an APK or theme ZIP as a ROM.

## Included behavior

- Home starts with Database. Database contains Songs, Albums, Artists, Playlists, Currently Playing, Genre, Year, Search, Videos, Podcasts, and spotify wrapped, in that order. Existing Home shortcuts remain available.
- Songs sort by title. Songs and Artists have a `[Most Listened to]` entry which opens artists ranked by the **sum of the play counts of all their tracks**, highest first. Counts come from this device's database; no listening history is invented. Equal totals currently sort in reverse alphabetical order.
- Search first chooses Artist, Song Title, or Album, then First Letter or Type a Name. First-letter browsing has Numeric, A–Z, and Special Character entries. Composer, a separate First Letter root entry, Shuffle Songs, User Rating, Same as Currently Played, and Tracks By are omitted from the new home/library profile.
- The playing-track context menu starts with album name, artist name, Play Similar Songs, Add to Playlist, and Current Playlist, then retains the existing controls and adds System. Album and artist links open temporary database views. Back returns to the currently playing screen, and explicit Home → Database opens the normal music menu. Choosing a track uses Rockbox's normal queue replacement behavior.
- Play Similar Songs collects tracks with the current track's exact genre tag, replaces the current queue, and shuffles it. Missing genre/database, party mode, or cancellation leaves the queue unchanged.
- Albums and playlists have `[Shuffle]` above song one. Opening a named playlist or entering an album selects song one, so reaching Shuffle requires scrolling up. Shuffling changes the playback queue, not the saved playlist file. Existing explicit empty-playlist behavior is retained.
- On the physical Y1, two short center-button clicks within 400 ms open the context menu. A single click retains browsing behavior after that short delay; long center press remains available.
- The adapted SNARTY WPS and status/list screen use 480×360 layouts, the original palette/fonts, and native color album art. A missing-art label is displayed only when no art is available. Embed cover art in your audio files or use a supported `cover.jpg`/`cover.bmp` beside the album's tracks.

## Install the paired application APK

This revision is **SNARTY-Y1-9**, with Java/resources compiled against the device-confirmed **Android API17 (4.2)**. Use the paired APK through Android's package manager with `adb install --no-streaming -r -f SNARTY-Y1-9-video.apk`. Keep the working aligned SNARTY-Y1-3 recovery APK available. No ROM flashing or key-layout replacement is needed for this application update. Existing SD data and settings are retained.

1. Keep a backup of the card's `.rockbox` folder and music.
2. Place `SNARTY-Y1-9-video.apk` beside `adb.exe` in Windows platform-tools.
3. Run `adb install --no-streaming -r -f SNARTY-Y1-9-video.apk`, and stop if it does not report Success. The `-f` option selects internal application storage; media stays on the microSD card.
4. Open Rockbox with `adb shell am start -n org.rockbox/.RockboxActivity`. If storage is being shared over USB, safely eject its Windows drive and unplug the cable. The new waiting screen retries without a UI-thread sleep loop.
5. Copy the provided test MP4 to the card-root Videos folder (beside `.rockbox`) and open Database → Videos. Use H.264 Baseline/AAC-LC files to test the platform decoder. Actual Y1 decoding remains a device acceptance check.

This APK update does not change the already-working wheel mapping, replace the stock app, or replace system firmware. It has internal-only install location, ZIP alignment and legacy API17 signature verification. See [VIDEO-PLAYER.md](VIDEO-PLAYER.md).

## Media folders, selection, and listening history

**spotify wrapped** shows monthly top ten songs and the most played song for each recorded year using native scrolling lists, two-line ranking cards, and SNARTY's mint/lavender palette. It records qualifying future playback locally in `.rockbox/listening-history-v1.tsv`. No past monthly history is inferred from lifetime database counts. See [LISTENING-HISTORY.md](LISTENING-HISTORY.md) for the export format and sync-app integration contract. No Spotify account connection or official Wrapped import is implemented.

Database lists initially select their first actual song, album, artist, or other tagged item below bracketed actions such as [All Tracks], [Random], [Most Listened to], [untagged], and [Shuffle]. Scroll up to reach those options. Returning with Back retains the previous selection. An empty or untagged-only result keeps its available options usable.

Videos and Podcasts appear after Search in Database. Y1 startup creates `/sdcard/Videos` and `/sdcard/Podcasts`, corresponding to folders `Videos` and `Podcasts` at the card's root, beside `.rockbox`. Existing folder contents are retained. Opening either menu retries creation if necessary. Back from either folder's root returns to Database; subfolders retain normal Back navigation.

Put audio episodes (for example MP3, FLAC, M4A or M4B files supported by Rockbox) in Podcasts. This is local file browsing/playback, without an automatic subscription downloader. Videos lists `.mp4` files on the Y1 in addition to the MPEG-player extensions `.mpg`, `.mpeg`, `.mpv`, and `.m2v`. MP4s under `/sdcard/Videos/` (including subfolders) open an internal Android video Activity styled with SNARTY's palette. It supplies a seekable progress bar, elapsed/total time, play/pause/replay, Back, and hardware seeking. MPEG files retain the existing MPEG-1/2 plugin. See [VIDEO-PLAYER.md](VIDEO-PLAYER.md) for codecs, controls, local file placement and test limits.

Speech controls and recognition hooks have been removed. Search uses typed text or first-letter browsing.

Carlink has been removed. This build removes the old diagnostic menu and deletes its managed script/report files on Y1 startup. No car connection or projection feature is included.

## Validation and limits

The Y1 ARM/native build, Android Java compilation, APK packaging and v1/v2 signature verification pass. Both 480×360 skins pass the target-specific Rockbox CheckWPS parser. Shared menu/database/queue changes were exercised in the native iPod 6G simulator with a four-track, two-artist fixture. Simulator checks covered home order, alphabetical songs, artist aggregate ranking (18 total plays versus 15 despite the latter artist having the highest individual track count), album selection/Shuffle, context-menu order, genre queue replacement, named-playlist selection/Shuffle, and first-letter song filtering.

Physical Y1 installation, double-click timing, and actual-device color rendering have not been tested. The provided app is a development build. The repository's Y1 simulator does not compile its Android notification code; the generic SDL target also has a pre-existing duplicate plugin API member, so those are not claimed as passing workflows. The working iPod simulator exercises the shared implementation; the actual Y1 target compiles successfully.

Album browsing follows the repository's existing album-name grouping. Distinct releases with identical album names can therefore be grouped together. Artist ranking scans matching tracks per artist and can take longer on very large libraries; cancellation/progress remains governed by the existing database browser. Existing Rockbox directory-buffer limits still apply.

## Build

The onboarding installation script installs local tool dependencies outside the checkout. Activate `/workspace/setup/env.sh`, then use:

```sh
cd /workspace/builds/y1
VERSION=SNARTY-Y1-9 make -j5 ANDROID_PLATFORM_VERSION=17 BUILD_TOOLS_VERSION=28.0.3
VERSION=SNARTY-Y1-9 make ANDROID_PLATFORM_VERSION=17 BUILD_TOOLS_VERSION=28.0.3 classes zip unsigned-apk
```

The selected target is `310`, LCD `480×360`, type `n`; NDK r10e/GCC 4.9, SDK platform 17, Build Tools 28.0.3 and JDK 17 are used. Build Tools 28.0.3 is a supported command-line override for the repository's 32-bit 19.1 tools. Source changes are required for the new menu entries; installing only the theme on an older stock build does not implement them.

## Attribution

SNARTY 1.0: Simon Andén / Tirim4, 2025, supplied by the user. Original attribution credits SPAZZ by Chuck Lardo, SNAZZ/SNAZZ2 by Jihoon Kim, SNAZZY by Phil Graves, and elements/code from adwaitapod by even Dook. The SNARTY adaptation is distributed under **CC BY-SA 4.0**, retaining those credits: https://creativecommons.org/licenses/by-sa/4.0/ . Fonts and original assets retain their respective upstream licenses. Rockbox firmware/application changes retain Rockbox's GPL licensing; see `docs/COPYING` and `docs/LICENSES`.

## USB storage startup handling

USB mass-storage sharing unmounts the card from Android (observed on this Y1 as state 7 Shared-Unmounted for /storage/sdcard0). The old Service waited in a sleep loop on Android's main thread. This revision uses a Handler-scheduled StorageStartGate: it does not start the core until storage is mounted/writable, shows a storage message, retries once per second, and avoids native framebuffer/button calls while waiting. The same controller prevents repeated start requests and cancels retries when destroyed. Config is read after the card becomes available, using API17-compatible finally/close handling. Native-library load errors release the startup lock and are shown. Native libmisc resources are read from ApplicationInfo.nativeLibraryDir, matching the package manager's library selection.

The waiting screen retains Retry and the existing stock-switch flow. Media-button routing uses Android controls while waiting, then returns to Rockbox mode when the framebuffer is shown. The app remains in internal storage, so sharing the card does not remove its APK. The video/podcast browser also checks Android's mounted state rather than creating/browsing folders on an unavailable mount point.

## Revision 8 startup and standby

Startup no longer waits on the UI thread for native-library loading. Missing/shared storage is polled automatically every second; failed pre-core initialization retries after five seconds. Returning to the Activity requests startup again if the core is not running, and the waiting screen no longer requires a Retry button. An absent card, USB sharing, corrupt/incompatible native library or failing card can still prevent startup; the reason stays visible.

The service now holds its own partial CPU wake lock throughout its lifetime and stays foreground even when music is stopped. The screen is still allowed to turn off. This trades higher standby battery use for avoiding deep-sleep/service-demotion risks on this dedicated player. Teardown releases both wake locks and removes the foreground notification. A one-time append-only settings migration turns idle poweroff off; later user changes to that setting are preserved. Explicit shutdown, sleep timer and low-battery behavior remain. This addresses identified software risks, not a proven explanation for hardware/Android reboots. Physical screen-off, idle-wake, reboot and recovery testing remains required.

## Revision 9 full queue Shuffle
Album and playlist Shuffle and Play Similar Songs start a new shuffled pass at logical position 1 of N. A dedicated API resets both queue indices, avoiding the normal shuffle API preservation of Play Selected First and an inherited rotated first_index. All entries remain in the new queue; saved playlist files and ordinary selected-track playback are unchanged.
