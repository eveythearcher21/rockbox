# SNARTY Y1 playback/sync contract v1

The player is an offline Android-4.2/API17 Rockbox app. It does not authenticate to YouTube Music, download lyrics, stream recommendations, or run a forced aligner. The desktop companion supplies account-derived ordering, locally matched recommendations and correctly timed lyrics. Missing data is shown honestly; filesystem dates are never substituted for YouTube-library order.

## Library ordering

Install `.rockbox/snarty/library-v1.bin` on the card, publishing it atomically after all media transfers complete. Use the reference writer `tools/compile_sync_library.py` rather than duplicating its binary encoding. JSON input is:

```json
{"version":1,"tracks":[{"device_path":"/sdcard/Music/Artist/Album/song.mp3","song_added_rank":1,"album_added_rank":3}]}
```

Ranks are independent: 1 is newest in the user's actual YouTube Music Songs or Albums library; increasing numbers mean older. Zero/null/absent means unknown. Obtain them from the provider's actual added-order listing/timestamps, including full pagination. Preserve stable source song/album IDs in the companion's own database. Do not infer order from downloads, file modification times, scan order or the listening journal. If the provider cannot expose an order, mark it unavailable.

Binary header is 16 bytes: ASCII `SNRTLIB1` (8 bytes), little-endian uint32 record count, little-endian uint32 record size=268. Each record is a 260-byte NUL-terminated UTF-8 absolute device path (zero-padded), uint32 song rank, uint32 album rank. Sort records by the UTF-8 path bytes, case-sensitively; no duplicate normalized paths. Ranks must be 0..2147483646. Maximum count is 1,000,000; the reader uses constant-memory binary search, not a million-entry RAM allocation. Actual Rockbox directory/list buffer limits still apply: dynamic recent sorting refuses an incomplete buffer instead of silently sorting chunks independently. Increase the directory limit when a clear buffer-full message requires it.

Known aliases `/storage/sdcard0/` and `/mnt/sdcard/` normalize to `/sdcard/` on this Y1. Other absolute paths are kept exactly; use the paths actually indexed by Rockbox, including case. Do not write Windows drive-letter paths or temporary download URLs. The reference writer validates Unicode, byte limits, traversal/duplicate paths and rank bounds. Keep final music paths under 240 UTF-8 bytes so sidecar suffixes also fit the device limit.

The UI adds `[Recently Added]` to Songs and the top Albums view. It toggles between synced newest-first order and ordinary order, retaining the existing helper rows. Unknown ranks sort last by title. With no valid rank file the action explains that sync is required. Album order follows Rockbox's existing album-name grouping; the group uses the lowest known album rank among its tracks. The companion must flag ambiguous releases with identical album names rather than claiming separate source album IDs are distinct native groups. Artist-specific album browsing retains its filters.

## Lyrics

For `song.mp3`, write `song.lrc` next to it, replacing the audio extension. UTF-8 with BOM is recommended; the reader also accepts `.lrc8`. Use enhanced LRC word tags for word highlighting:

```text
[00:10.00]<00:10.00>Paper <00:10.90><00:11.20>stars <00:12.00><00:12.30>shine<00:13.50>
```

The text above is an original synthetic timing example, not fetched song lyrics. Square-bracket tags start a display line; angle-bracket tags carry absolute audio timestamps. End tags followed by an empty interval preserve gaps between words. Times are relative to the exact local recording, with 10ms device precision. Keep each encoded line below 480 UTF-8 bytes; split long lines only at word boundaries. `tools/encode_word_lyrics.py` is the reference encoder. Its input is `{ "duration_ms": 10000, "lines": [{"words":[{"text":"Paper ","start_ms":0,"end_ms":900}, ...]}] }`. It requires real explicit intervals, verifies order/duration and never invents timestamps.

Prefer lyrics belonging to the exact YouTube Music recording ID. Word timing is not guaranteed from YouTube Music. If only line timing/text is available, the companion can run local forced alignment against the matching local audio (optionally a vocal stem), validate its result and label it estimated. Preserve provenance in a companion database/optional `song.lyrics.meta.json`: recording ID, local audio SHA256, language, source, granularity, method, confidence and offsets. Do not distribute provider tokens/cookies to the player or repository.

If alignment is unavailable or fails, publish real line-synced LRC or plain `.txt` text without fabricating words. The device shows Words/Lines/Text/Missing. Line-only lyrics highlight the current line without pretending to know individual words. Plain text is manually scrolled, not automatically distributed across the song's duration. The Lyrics screen uses the real playback clock and follows track changes/seeking. The Snarty mode is launched from the song menu; Back/Menu returns to playback. Ordinary LRC Player settings outside this mode remain intact.

## Similar Songs / radio continuation

For `/sdcard/Music/song.mp3`, write `/sdcard/Music/song.mp3.radio.m3u8` (append the full suffix to the complete audio filename). UTF-8 lines, for example:

```text
#SNARTY-RADIO	1
#seed_video_id=companion-owned-source-id
/sdcard/Music/Artist/Album/related-one.mp3
/sdcard/Music/Other Artist/Album/related-two.flac
```

Fetch per-recording YouTube Music radio/watch-next recommendations through a supported authenticated provider and map stable source IDs to files actually installed on the Y1. Keep the service's ranked order. No URLs, speculative filename matching or tracks that are absent from the device. The native reader accepts at most 128 distinct playable recommendations, skipping the seed, missing files, duplicates and non-audio files. Known card aliases and case variations are treated as the same device file for deduplication. Store recommendation provenance/coverage/missing-source IDs on the desktop for diagnostics. Do not download extra tracks silently.

Selecting Play Similar Songs preserves the currently playing track and position, clears only its old continuation, and appends valid recommendations. It does not reshuffle the recommendation order. If no matched synced radio exists, a disclosed local fallback ranks artist/genre/grouping/nearby-year evidence and refuses weak matches; it is not described as Apple's or YouTube's recommendation model. If no candidates exist, the current queue is kept and the player asks for radio sync.

## Covers and metadata

Keep standard TITLE, ARTIST, ALBUM, ALBUMARTIST, track/disc and year tags. Artist/year/genre tags improve local fallback, but never synthesize library-added dates. Write a modest baseline JPEG `cover.jpg` (around 200x200 or larger but modest in size) in each album folder. The native browser also finds conventional per-track/album artwork and embedded JPEG artwork. JPEG/BMP are supported by the existing native art pipeline; convert PNG/WebP on the desktop. Do not rename an unsupported image file to `.jpg`. Missing/oversized/unsupported art uses an explicit placeholder.

The new album rows keep their helper/sort actions above the first album, show cover/title/album artist, and enlarge the selected cover/title. Opening a row animates its cover into the playback-sized location and shows the album's track list beside it. Music and files are not moved by the APK.

## Desktop APK update button

The owner uses Windows and already has a rooted, ADB-authorized Y1 running Android SDK17. Implement a graphical updater that bundles official platform-tools/ADB and notices (or locates a verified installed copy). No Android SDK/Studio installation or manual terminal commands should be required. USB debugging/authorization and a working USB transport are still necessary; an APK cannot be installed merely by copying it to the card.

Identify connected devices, let the owner choose if several are present, verify Android API17 compatibility/package `org.rockbox`, and use argument arrays rather than shell-concatenated paths. Known releases use versionCode1 and the same platform certificate (SHA256 `c8a2e9bccf597c2fb6dc66bee293fc13f2fc47ec77bc6b2b0d52c11f51192ab8`). Verify the published SHA256 for downloaded APKs and use Android's package manager to enforce update signatures. Never uninstall to bypass a mismatch, flash firmware, rewrite key layouts, disable stock firmware, factory reset or clear music/settings as an update workaround.

The effective update operation is bundled `adb -s SERIAL install --no-streaming -r -f APK`, then after Success `adb -s SERIAL shell am start -n org.rockbox/.RockboxActivity`. Display progress, exact failure details, a useful log-export button, and success only after package-manager success/version verification. Keep backups of config/history and the last known-good APK. Music and metadata sync remains a separate operation.

When Windows exports the card as USB mass storage, Android cannot access it. Finish transfers and safely eject before unsharing/mounting or unplugging. The UI must never forcibly unmount an actively written Windows drive. An installed app may wait for storage until safe eject/unplug; that is not an installation failure. Do not require a new GitHub release token merely to download a public APK.
