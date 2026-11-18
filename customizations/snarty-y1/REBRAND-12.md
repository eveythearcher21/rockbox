# SNARTY rebrand 12 and RockBlock Syncer handoff

The owner's Home screenshot is the reference: background #232234, selection #302e43, mint #a5e6ba, lavender #a2accd, Kode Mono pixel font, left accent on the selected row, flat square imagery, restrained enlargement. The physical Y1 LCD is 480x360 landscape (4:3); the supplied preview is enlarged 960x720. Do not export a 960x720 wallpaper as the device asset.

## Player implementation

Home/Music retain the revision10 structure. The shared native list renderer applies the palette, selected accent, enlarged selected label and generous rows to normal settings, search, year, genre, playlist/catalog, file/media and Wrapped lists. These remain the real functional controls. Specialized plugin/game/editor renderers are independent and are not all rewritten. The Android storage-wait screen now has a mint heading and themed stock-switch button; the Android/system USB-sharing dialog outside Rockbox is not replaced.

Albums, artists and title lists use artwork cards. Artists load a genuine portrait from the representative audio's complete path plus `.artist.jpg` (example `song.mp3.artist.jpg`), then `artist.jpg` in that album folder. Missing portraits show a placeholder, never an album cover falsely presented as an artist. Artist, album and song selections enlarge; opening animates the image to the WPS cover coordinates (20,70,200,200). Artist activation retains native artist->albums navigation; the next list is the artist's filtered album list. WPS retains that same cover position, with a matching Now Playing header, mint title and shuffle/volume information. Album tracks use the same new list colors alongside expanded artwork.

Videos/Podcasts/Playlists file browsers show image cards. Conventional per-media JPEG art or folder `cover.jpg` supplies imagery; missing art stays a placeholder. Playlist catalog and current queue use the shared styled rows. This does not add a video decoder or change codec support. MPEG/plugin-owned video UI is independent.

Podcasts use one folder per show, then episodes in sortable chronological filename order. Existing flat files are not destructively moved by firmware. The syncer must group/tag/order them on the next managed sync, retaining ID mappings and fixing managed playlists if paths change. Y1 podcast browsing forces ascending natural filename order within `/sdcard/Podcasts`. The visible row uses episode title/artist tags when available, so the sortable prefix need not clutter the title.

## New companion assets

- Artist portraits: JPEG 200x200 recommended. Per-track `.artist.jpg` takes priority over album-folder `artist.jpg`. Cache one source image per canonical artist on the desktop, copy into managed album folders or write all per-track sidecars when different artists share a directory. Never overwrite album covers with portraits.
- Podcast layout: `/sdcard/Podcasts/<safe show name> [stable-ID]/000001 - <episode title>.mp3`, increasing chronological rank (oldest first). Stable IDs remain in the desktop manifest, not inferred from title alone. Sort by publication time then season/episode number and stable-ID ties; expose a policy when source dates conflict. Use ALBUM=show, TITLE=episode, ARTIST=creator and valid track numbers. Folder cover.jpg is the show image; episode-specific basename.jpg is optional. Undated episodes go last, deterministically, with unavailable dates reported.
- Video artwork: matching basename.jpg next to the real video, or a folder cover.jpg. Keep MP4 media and metadata accurate; an MP3 renamed MP4 is not a video.
- Screensaver: optional `/sdcard/.rockbox/snarty/screensaver.jpg`, exact480x360 JPEG, max2MiB. The player refreshes changed files while running and shows it after60seconds without input; the next physical key or touch dismisses it. It does not change playback or keep a dark screen awake. Invalid-size/missing/oversized images disable the idle artwork. Delete this file to reset. The uploader must atomically replace it after conversion; UI must call this an idle image, not a fully implemented configurable wallpaper or OS lockscreen. Hardware wake/input integration needs actual Y1 testing.

## Existing revision11 sync formats stay compatible

Read SYNC-CONTRACT.md for binary account-library ranks, real enhanced-LRC word intervals, matched radio sidecars, artwork and safe APK updates. Words require real provider timing or explicitly labeled forced alignment; ordinary text must not be evenly spaced to fake karaoke. The firmware itself does not authenticate or fetch YouTube Music. The syncer retains provider credentials securely on the computer.

## First launch and validation

Revision12 uses a new once-only paired asset marker and `.before-snarty12` backups, retaining revision11 backups. It installs matching skins/fonts/plugin and appends only matching theme settings. User music/history/account metadata are preserved. API17, matching certificate, no uninstall, no ROM/keymap changes. Build target310. Shared320x240 simulator evidence does not establish physical480x360 performance, video compatibility or standby stability.
