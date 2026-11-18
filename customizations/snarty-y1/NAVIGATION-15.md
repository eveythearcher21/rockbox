# SNARTY Y1 selected-song menus, playlist collages and named portraits 15

All revision14 features remain, including eight-track album pages, five-row artwork lists, Favorites rules, RLRL complete Favorites shuffle, remembered sorting/device dates, Back, video and idle artwork.

## Hold a song anywhere

Held audio rows in database Songs, Albums, Artists, Favorites, searches, audio file browsing and playlist/current-queue viewers open the same seven-option design used by Now Playing: selected Album, selected Artist, Play Similar Songs, Lyrics, Favorite (star), Add to Playlist..., Current Playlist. Folder/virtual-action rows and explicit configured hotkeys keep their existing controls. A video file that cannot be parsed as audio reports unavailable metadata rather than acting on another song.

Actions use the selected file's metadata. Favorite and Add to Playlist affect that file. Album/Artist browse the selected tags without changing playback; Back restores the calling song list or playlist. Temporary nested library browsing is bounded to two selected-song browsers and restores search/runtime clauses as well as selection. A deeper request asks the user to close a browser first. An uninitialized music database produces a message instead of opening an invalid view.

For a selected song that is not currently playing, Play Similar Songs starts that song then its matched ordered continuation; for the current song it preserves playback position and replaces only its continuation. Missing recommendations leave the queue intact. Same synced-radio and disclosed metadata fallback rules from11 still apply.

Lyrics for the playing file stays timed. Lyrics for another file opens a clearly labeled manual Preview with that file's lyrics and duration; the wheel scrolls, Back returns, and the background song keeps playing. Preview does not pretend to highlight words against the wrong playback clock. Seek/play/track-change/editor actions are disabled inside Preview. Missing selected lyrics remains an honest missing state.

The revised lyrics plugin is installed once on first mounted launch, with `.before-snarty15` backup and `.rockbox/.snarty-song-menu-v15` marker. Matching revision12 theme settings are not reset again. A failed plugin copy is reported through existing startup retries. If manually restoring an old plugin later, remove this specific marker before reinstall/relaunch to apply the paired preview plugin again.

## Four-album playlist covers

Native playlist catalog/file cards generate a2x2 cover grid from the first four distinct albums with readable artwork. Identity uses album title plus album artist/artist. Duplicate tracks from one album do not consume additional tiles. UTF8 M3U/M3U8 paths may be absolute or relative to the playlist; comments/BOM and dot segments are handled. Missing/non-audio files and stream URLs are skipped.

The scan is bounded to the first2048 playlist lines per cover. Fewer than four usable albums leave remaining quadrants dark; none uses the existing placeholder. Conventional JPEG/BMP or supported embedded JPEG artwork is used. This is on-device UI composition, not a rewritten playlist or an uploaded generated cover file. Custom playlist folders are detected by the catalog's M3U filter. Covers refresh when the gallery is reopened; no network access is needed.

## Artist_Images at the drive root

Put portraits alongside the Music/Videos/Podcasts folders in `Artist_Images`, for example:

```
Artist_Images/Daft Punk.jpg
Artist_Images/Björk.png
Artist_Images/Artist A.bmp
```

The stem must match the artist displayed in the artist list, not an audio filename or album title. Extension/name matching is case-insensitive for ordinary ASCII names; Unicode spellings should match exactly. Replace Windows-forbidden filename characters `/\\:*?"<>|` with underscores. Keep paths within the existing Rockbox limits.

Root-folder JPEG/JPEG-extension/BMP portraits take priority over legacy per-track `.artist.jpg` and album-folder `artist.jpg` sidecars. Native JPEG/BMP load directly. At app startup and when the Android framebuffer is reopened, a low-priority background worker converts PNG/WebP sources into bounded200x200 JPEG cache files under `.rockbox/snarty/artist-images`, retaining originals. It handles at most2048 PNG/WebP stems per launch, skips corrupt/oversized sources, preserves names, center-crops and reuses unchanged timestamps. No account access or synchronous boot-blocking decoder job is introduced.

After adding PNG/WebP sources, reopen the app to run conversion, then reopen Artists once it finishes. JPEG/BMP changes need only reopening Artists. Absent/unsupported portraits use placeholders or legacy fallback. The background worker's Android bitmap decoding/performance and card-sharing behavior need actual Y1 acceptance; host ImageIO-backed tests exercise conversion policy rather than claiming Android decoder emulation.

## Validation and sync compatibility

Existing lyrics/radio/library/Favorites/podcast/screen-image schemas remain valid. Syncers should now target root Artist_Images names; no playlist collage upload is required. Preserve player-managed stores and user originals. Update-install the matching API17 APK without uninstalling, ROM flashing or system wheel-map replacement. The source branch/ZIP includes all changes and tests.

Actual shared320x240 simulator tests target a nonplaying song while another plays, check correct Album/Artist/Favorite, restore caller selection, preview without queue changes, selected-song radio queue membership, mixed-case named portraits/PNG-cache lookup, four distinct tile colors with a duplicated album and relative path, and playlist held-menu album navigation. Host tests exercise the one-time plugin installer and image conversion/cache policy. Physical480x360 installation, all hardware long-press locations, new-image refresh, PNG/WebP decoding, video/standby and fast input remain owner acceptance checks.
