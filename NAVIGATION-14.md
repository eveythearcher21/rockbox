# SNARTY Y1 Favorites shuffle and eight-track albums 14

Includes all revision13 features: persistent Song/Album/Artist favorite rules, star menu below Lyrics, Favorites immediately below Currently Playing, Favorites Song/Album/Artist sorts, independent library sorts, local added-date fallback, Back behavior, and previous video/idle artwork features. Rules continue to match newly indexed music by a favorited artist. Album matching now also treats the database's <Untagged> album-artist marker as missing and falls back to the track artist.

## Eight album tracks

Album pages use a compact64px cover and album/artist header, followed by a full-width track list with eight rows. The selected title is emphasized and long titles retain a cleared marquee. Real smaller album/song/artist/media card lists remain five rows; only album track views become eight. A short album displays only its actual tracks. Shuffle remains above the first real track and can be reached by scrolling up. Dirty/theme redraws retain the eight-row geometry. Opening an album animates artwork into the compact header; starting a song still expands art into the normal playback-cover position.

## Quick Right, Left, Right, Left

On native Home/Music browsing, the playlist viewer and playback, press and release Right, Left, Right, Left quickly. Consecutive directional presses must begin within350ms of one another, and the whole gesture must finish within1.2seconds. Release every button; this is not a held chord. The player must be awake/unlocked. Android video playback, external Android screens, text-entry/plugin-specific screens and some independent plugin controls are outside this native gesture path.

The input filter buffers the directional press/release events. A completed gesture consumes all eight events, avoiding intermediate navigation or track skips. An incomplete, wrong, held or slow sequence replays as ordinary input, retaining event data. A lone Right can therefore wait up to350ms before its ordinary action. USB/system events cancel a partial gesture and pass through immediately. Hardware timing still requires physical Y1 acceptance.

A successful shortcut scans the current database against all active favorite rules and creates a new shuffled dynamic queue. A random favorite starts at logical position1; every other matching playable file is queued once for the same pass. The existing queue is replaced, while saved playlist files and favorite rules remain unchanged. It uses the complete-queue shuffle routine, resetting both queue origins to avoid skipping the beginning of the shuffled pass. Repeat mode remains the user's setting.

An empty Favorites set, unavailable database, cancelled preparation, or too-small Max Playlist Size leaves the current queue intact. Preparation is checked before replacement; low-level card failure during the subsequent queue write can still fail and is reported. Party Mode must be disabled to replace its queue. Unsupported/missing audio files are excluded. The shortcut does not download any music.

## Syncer and update compatibility

No new sync-file schema is required. Preserve the revision13 preference/date index/Favorites rule files. Existing revision11 library order/lyrics/radio and revision12 artwork/podcast/idle image formats remain valid. The current player is an API17 Android application, not a ROM; update-install it without uninstalling or rewriting system wheel maps. No additional theme reset is forced when upgrading from revision12/13.

Host tests exercise the actual raw gesture filter with a timed recording queue, including correct pattern, ordinary/incorrect/held/late input replay, context cancellation, original event data, and USB priority. Existing actual favorite-rule/date persistence and full-queue shuffle tests remain relevant. Shared320x240 simulator tests use a synthetic14-track library, an eight-track favorite album, complete saved-queue membership/origin assertions, an empty-Favorites no-op, and real screenshots of the album layout. Physical480x360 typography, wheel timing, video/standby and device installation remain owner acceptance checks.
