# SNARTY Y1 playback update 11

This experimental paired APK keeps revision10's Home/Music/Settings navigation and prior video/startup/full-queue Shuffle changes. It changes the application, not the Android ROM. Physical Y1 installation and animation performance remain owner acceptance checks.

## Playing-song screen

One center click opens a sheet with exactly Album, Artist, Play Similar Songs, Lyrics, Add to Playlist..., Current Playlist, in that order. Album and Artist display the actual current metadata. Back closes the sheet to the playing screen; the opening/closing transitions slide the playing screen vertically. Album/Artist shortcuts retain the existing temporary database navigation restoration. Their Back action returns to playback rather than trapping ordinary Music browsing inside the shortcut.

Play Similar Songs preserves the currently playing song and playback position, removes its old continuation, and queues the recording's synced recommendations in ranked order. Only existing supported audio files are accepted; the seed, duplicates and missing files are skipped. If recommendations are unavailable, a disclosed local fallback ranks exact artist/genre/grouping and nearby year metadata, requiring a meaningful match. It cannot reproduce Apple's proprietary recommendations, understand the audio itself or fetch YouTube Music without companion data. Empty results leave the existing queue intact.

## Lyrics

Lyrics opens the included enhanced-LRC player with mint/lavender styling and returns to playback with Back. Genuine word timestamps drive word highlighting; line-only timestamps highlight the current line. Plain text remains manually scrollable. The screen indicates Words, Lines, Text or Missing so unsynchronized text is not presented as word-accurate. Missing lyrics do not interrupt playback.

Place `song.lrc` alongside `song.mp3` (or corresponding audio extension), using the same basename. The companion should fetch the exact recording's YouTube Music lyrics where available. YouTube Music does not reliably supply word timing: local forced alignment can produce explicitly labeled estimates, or the app must retain line/plain lyrics. This APK does not log in to YouTube Music or download lyrics. See SYNC-CONTRACT.md and the reference encoder for exact timing/line-length rules. Do not simulate word timing by distributing words evenly.

## Recently Added and album cards

Songs and top-level Albums retain their bracketed controls, with [Recently Added] immediately above the first real entry. Select it to toggle between alphabetical and true synced library order. Unknown ranks sort last. Without a synced order file, the player requests sync rather than treating file dates as account-library dates. Account Songs and Albums ranks are independent.

Album browsing shows actual color artwork on the left and album title/artist beside it. The selected cover and title grow. Opening the album animates its cover into the playback-sized panel, with tracks beside it. Use external JPEG/BMP covers or supported embedded JPEG; bounded decoding falls back to a placeholder for unsupported/missing art. This does not introduce online artwork lookup. Rockbox's existing album-name grouping can merge identically named releases; the companion must flag ambiguous source mappings. Directory-buffer limits still apply; Recently Added refuses an incomplete sort instead of misleadingly sorting separate chunks.

## Paired update and backups

On the first mounted-card launch, revision11 validates and installs its bundled theme assets and lyrics plugin, backing up replaced files as `.before-snarty11`. It appends matching WPS/SBS/font/color settings to `config.cfg` and any pending `config.cfg.new`, preserving the original bytes in backups and leaving unrelated settings intact. It never replaces tagnavi_user.config. A one-byte `.rockbox/.snarty-playback-v11` marker makes the migration once-only. Later theme changes are preserved. A failed preflight leaves assets untouched; a failed write is reported and startup retries.

Before updating, back up `.rockbox` and keep the previous APK. Returning to the old APK alone does not undo the new card theme; restore backed-up theme/config files if desired. Do not uninstall, flash a ROM, alter wheel mappings or factory reset to apply this update.

## Acceptance on the actual Y1

Check single center click and Back, all six routes, album shortcut return, uninterrupted radio playback and complete continuation, real enhanced-LRC synchronization/seek, plain/missing lyrics, account-ranked recent lists, album art/selection/zoom, and large libraries. Recheck video, screen-off wake and reboot. Shared-code SDL captures and host policy tests cannot establish Android decoder compatibility or physical standby reliability. Synthetic test lyrics/recommendations are not shipped as user library data.
