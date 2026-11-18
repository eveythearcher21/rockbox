# SNARTY-Y1-10 layout test APK

This is an experimental navigation/animation update for the Innioasis Y1, retaining the revision9 video worker, complete-queue Shuffle, listening journal and automatic startup/standby changes. It updates the Android application, not the ROM or wheel mapping.

## Install on Windows

Download SNARTY-Y1-10-layout-test.apk and place it beside adb.exe. Pause music, then run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-10-layout-test.apk
```

Only after Success:

```powershell
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Finish file transfers, safely eject the Windows storage drive, then unplug USB so Android can mount the card. Do not run an old firmware-update ZIP or change the working wheel mapping. Existing music, playlists, history and config.cfg are retained by this release. The prior one-time idle-poweroff migration and service partial wake lock remain; standby battery use is higher than allowing deep sleep.

## New layout

Home has exactly Music, Videos, Podcasts and Settings. Music contains Songs, Albums, Artists, Playlists, Currently Playing, Genre, Year, Search and Spotify Wrapped, in that order. The library's database remains internal; you do not have to open a Database folder. Videos and Podcasts open their existing card-root folders directly.

Settings retains the existing detailed controls, adds System and Files, and groups FM Radio, Shortcuts and Plugins in Additional Features. Back returns to the parent folder and preserves its selection. Menu/Home returns Home. On native startup the player opens the new Home.

The new Home, Music, Settings and Additional Features screens have theme-colored icons and a roughly 1/6-second growth/shrink transition for the selected label, icon and card. Regular content lists and detailed settings retain their existing list controls. Albums uses the old database glyph; Playlists uses its original glyph; the other folder/category glyphs are purpose-specific, including the Wrapped circle/arcs. This icon does not add Spotify account/API support.

## Test on the player

Check the four Home entries and all nine Music entries. Verify Back from Songs/Albums/Artists returns Music, Videos/Podcasts return Home, and System/Files/Additional Features return Settings. Try music playback while moving through these menus. Check that the current selection grows smoothly and the old one shrinks during slow and fast wheel scrolling. Confirm hardware FM Radio, video playback, screen-off wake and reboot behavior on the actual Y1. Those physical checks cannot be established by the cloud simulator.

See UPDATE-VALIDATION.json for precise build, regression, simulator and signing evidence. Previews are actual 320x240 shared-code simulator captures, not photographs of the 480x360 Y1. The simulator cannot launch the Android FM app. Y1 animation timing/performance and standby reliability remain pending owner acceptance.

## Return to the previous APK

The previous revision9 APK remains available:
https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-video-9-1ddadb3a/SNARTY-Y1-9-video.apk

Install it with `adb install --no-streaming -r -f SNARTY-Y1-9-video.apk`, without uninstalling the app. Both versions retain versionCode1 and the same platform certificate. Keep your card backup.

The source ZIP contains a complete binary patch against the documented base, new files, assets, build instructions and tests. Full source is also on this download branch. Rockbox code is GPLv2 or later; SNARTY attribution and CC BY-SA4 glyph/skin licenses are retained. See NAVIGATION.md for implementation scope.

Simulator checks passed for Home, all nine Music routes, media folders, existing sound controls, System/Files, Shortcuts/Plugins and Back to their new parents. Animation capture shows six distinct actual SDL frames during one selection change. A 320x240 preview may be smaller than the Y1 layout.
