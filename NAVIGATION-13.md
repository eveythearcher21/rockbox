# SNARTY Y1 navigation and Favorites 13

This test APK includes all prior revision12 playback, video, startup, lyrics and rebrand features.

## Five visible items

Album, artist, song and media artwork lists now allocate five rows to the available list viewport. A real smaller Kode Mono font is used on unselected titles and subtitles; selected titles and artwork are larger. The album's track pane also has five rows; this sizing survives theme/redraw events. Bracketed actions stay above the first real entry and remain reachable by scrolling up. Where a short list has fewer than five items, no dummy items are added. Playlist catalog/current queue use the shared compact list styling.

The selected-title marquee now clears its previous text rectangle using the selection background before drawing each frame. Selected card titles can scroll too. This prevents new letters from being drawn on top of old ones; subtitles/artwork remain outside the cleared title area.

## Back

The top Menu button means Back for shared menus and lists. On the physical Y1 its release returns one level, including after a held press; holding it no longer opens Quick Screen. From playback it returns to the previous screen instead of forcing Home. Music's Currently Playing route returns to Music; a song opened from Songs returns to that song list. The separate left/previous playback key retains normal track/seek controls. Android-owned screens and plugin-specific controls remain independent.

## Remembered sorts

Songs, Albums and Artists retain separate sort preferences across leaving/reopening and process restart, in `.rockbox/snarty-sorts-v1.bin`. [Alphabetical] explicitly restores ordinary order; [Recently Added] selects recent order. Albums also has [By Artist], sorting by canonical album artist then album title. Synthetic [Untagged] artist/album groups are hidden; playable tracks without title tags retain the filename fallback rather than being silently deleted.

Recently Added prefers genuine YouTube Music ranks from the unchanged sync library file. Tracks without those ranks are sorted newest-device-date first after the ranked tracks. A rank alone does not contain an absolute YouTube date, so the player cannot honestly interleave the two timelines by date. Albums/artists use the most recent matching known track's key. Missing dates go last.

Newly scanned music records a stable first-indexed timestamp in `.rockbox/snarty-device-added-v1.bin`, preserving it across tag edits/rescans. Existing indexed tracks are bootstrapped from their file date when needed. Original transfer dates of old files cannot be recovered if they were not recorded; copied source modification dates can differ from transfer dates. No YouTube manifest is required for this fallback. The disk hash index is bounded to65536 slots and256 probes, stores normalized paths to check collisions, and can occupy about17.6MB at its maximum seek extent on FAT. Retain it during sync/backup; do not regenerate it from download dates. A functioning device clock is required for new first-seen dates.

## Favorites

Music now has Favorites immediately below Currently Playing. Playback's single-click sheet is Album, Artist, Play Similar Songs, Lyrics, Favorite (star), Add to Playlist..., Current Playlist. Favorite opens Song?, Album?, Artist?. Selecting a rule toggles it and reports added/removed/error.

Song rules match a normalized device path. Album rules match album title plus album artist (falling back to track artist). Artist rules match artist metadata and continue to include newly indexed songs by that artist. Missing required tags produce an error instead of broad matching. Rules are stored as collision-checked, atomically replaced files under `.rockbox/snarty-favorites-v1/` with a FAV1 active/FAV0 inactive marker. A song is included if any active rule matches; removing a song rule does not exclude it from a still-active album or artist rule.

Favorites shows every matching local song, with [Song], [Album], [Artist] sort actions above the list. Selecting a song starts playback from the filtered list. It does not download additional tracks. Existing album-name grouping elsewhere in Rockbox remains; metadata alone cannot disambiguate identical releases by the same artist. Preserve rule files during update/sync. Renamed song paths need an explicit managed migration; artist/album rules remain metadata based.

## Syncer compatibility and acceptance

Revision11 library-v1.bin, enhanced LRC and radio sidecars, plus revision12 portraits/podcast layout/idle image, remain compatible. Back up the new preferences/date index/Favorites directory along with music/history. These are player-managed stores; the current sync contract does not authorize a desktop app to silently rewrite them. No new paired theme reset is needed when updating from revision12.

Host tests exercise actual persistence/date/rule functions with ASan/UBSan. Shared-code320x240 simulator tests use a private expanded14-track fixture and capture five-row views, independent sorts, Back from playback and Favorite rule creation/browsing. Physical Y1 button release timing, animation, actual480x360 typography, video and standby acceptance remain owner checks. This APK changes the application, not the ROM or system key layout.
