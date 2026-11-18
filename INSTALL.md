# SNARTY-Y1-15 song menus/artwork test

Includes all revision14 features, plus shared held-song menus, selected-song lyric Preview, automatic playlist collages and named Artist_Images portraits. See NAVIGATION-15.md for controls and limits.

Back up .rockbox and keep the prior APK. Put SNARTY-Y1-15-song-menus-artwork.apk beside adb.exe, pause music, then run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-15-song-menus-artwork.apk
```

Only after Success:

```powershell
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Finish/eject Windows transfers before unplugging so Android can mount the card. Update-install without uninstalling, flashing a ROM or changing system wheel maps. Settings/music/history/Favorites are retained; no extra theme reset from12/13/14. First mounted launch installs the matching lyrics plugin once with .before-snarty15 backup and .snarty-song-menu-v15 marker.

Hold an audio row in music browsing, file browsing or playlists to open Album, Artist, Play Similar Songs, Lyrics, Favorite, Add to Playlist..., Current Playlist. Actions target the held file. Nonplaying Lyrics opens a manual Preview without interrupting music. Selected Album/Artist Back restores the caller.

Artist pictures go in the drive-root Artist_Images folder, e.g. Artist_Images/Daft Punk.jpg or Artist_Images/Björk.png. Match the artist name in the player; JPG/JPEG/BMP load directly. PNG/WebP use a bounded background conversion cache on app/framebuffer reopening. Reopen Artists after conversion; originals are preserved. Keep images modest and paths short. Legacy portrait sidecars remain fallback.

Playlist cards automatically compose up to four distinct albums with artwork into2x2 grids; duplicates don't use extra tiles. Fewer covers leave dark remaining quadrants. No collage upload is required. UTF8 local playlists supported; covers scan at most2048 lines.

Recheck long-click menus/targets/Back, lyric Preview, real artist images and playlist grids on your physical Y1. Cloud previews are actual shared320x240 simulator captures with synthetic music/art, not480x360 device photos. Android bitmap decoder/hardware timing, video and standby acceptance remain pending.

Rollback update-install the matching-signature prior APK, without uninstalling:
https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-favorites-14-d399bcee/SNARTY-Y1-14-favorites-shuffle.apk

Preserve the original lyric plugin backup and all player-managed stores; if manually restoring an older plugin later, remove the specific v15 plugin marker before reapplying15. Source/attribution and full corresponding-source patch are included on this branch.
