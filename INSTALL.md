# SNARTY-Y1-13 navigation/Favorites test

Includes revision12 features plus five-row lists, cleared marquees, independent remembered sorts, album By Artist, local Recent Added fallback, Back and Favorites. Read NAVIGATION-13.md for details/limits.

Back up .rockbox and keep the previous APK. Put SNARTY-Y1-13-navigation-favorites.apk beside adb.exe, pause music, then run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-13-navigation-favorites.apk
```

Only after Success:

```powershell
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Finish/eject Windows transfers before unplugging so Android can mount the card. Update the application without uninstalling; do not flash a ROM or replace key-layout files. The included Y1 button map is part of the app. Revision12 paired assets/backups remain; updating from12 does not force another theme reset. Music/settings/history are retained.

Music -> Favorites is below Currently Playing. Click during playback -> Favorite (star) -> Song?, Album?, Artist?. Rules toggle on/off; any matching active rule includes a song. Artist rules automatically match later indexed music. Favorites has Song/Album/Artist sorting. Top returns one screen; holding Top then releasing also returns one level on Y1.

Recently Added uses YouTube ranks where supplied; other songs follow in device-date order. Legacy file dates are approximate; future first-indexed dates are preserved. Back up .rockbox/snarty-device-added-v1.bin, .rockbox/snarty-sorts-v1.bin, and .rockbox/snarty-favorites-v1. See NAVIGATION-13.md before editing these stores.

Check five album/song/artist/playlist entries, album track density, clean long-title scrolling, reopen/restart sorting, favorite rule types/future additions, Back from each entry path and prior video/wake behavior on your actual Y1. Shared320x240 simulator and host policy tests cannot prove physical480x360 behavior, decoder compatibility or standby reliability.

Rollback by update-installing the prior matching-signature APK without uninstalling:
https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-rebrand-12-f9b28607/SNARTY-Y1-12-rebrand-test.apk

The old APK ignores the new persistent stores; keep them for later updates. Source and license attribution are included on this branch and in the complete source patch ZIP.
