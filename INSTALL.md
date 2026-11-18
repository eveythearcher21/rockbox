# SNARTY-Y1-14 Favorites shuffle test

Includes every revision13 feature plus eight-track album pages and the Right/Left/Right/Left Favorites shuffle shortcut. Read NAVIGATION-14.md and NAVIGATION-13.md for scope and persistence.

Back up .rockbox and retain the previous APK. Put SNARTY-Y1-14-favorites-shuffle.apk beside adb.exe. Pause music, then run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-14-favorites-shuffle.apk
```

Only after Success:

```powershell
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Finish/eject Windows transfers before unplugging so Android mounts the card. Update without uninstalling; no ROM flash/system key-map change. No extra theme reset from12/13. Existing music/settings/history and favorites/sort/date stores are retained.

Favorites: Music -> Favorites below Currently Playing. During playback click -> Favorite (star) -> Song?, Album?, Artist?. Selecting toggles that rule; artist rules match later indexed tracks. Favorites has Song/Album/Artist sort helpers above the first track.

Quick shuffle: awake/unlocked, press/release Right, Left, Right, Left in quick succession (each new direction within350ms; full sequence within1.2seconds). On native music browsing/Home, playlist viewer or playback, this starts a random favorite at1 ofN and queues the complete remaining Favorites pass shuffled. It replaces the dynamic queue, not saved playlist files. An incomplete gesture replays ordinary controls, so a single Right can wait briefly. Empty/unavailable/cancelled or oversized preparation keeps the current queue; Party Mode blocks replacement.

Album pages now use a compact cover/header and eight full-width track rows; shorter albums show only their real songs. Shuffle stays above the first song. Other artwork lists retain five rows.

Physical Y1 acceptance remains pending: real wheel timing, eight-row typography, gesture/Back, video/standby and update behavior. Previews are actual320x240 shared-code simulator captures with synthetic art, not physical-device photographs.

Rollback update-install the previous matching-signature APK without uninstalling:
https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-navigation-13-e57b3437/SNARTY-Y1-13-navigation-favorites.apk
