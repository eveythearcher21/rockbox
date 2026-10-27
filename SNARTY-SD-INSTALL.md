# SNARTY Y1 revision 4 SD-card update

For an **Innioasis Y1 already running `230f848142-260516`**, the official stable-v0.5 source commit, or the earlier SNARTY package using that same updater. This package uses that release's matching SD updater layout. It does not require USB debugging or a flashing tool.

## Install

1. Back up the entire existing `.rockbox` folder and your playlists to your computer. This customization intentionally replaces `tagnavi_user.config`; preserve your old copy if you customized it. Charge the player first and leave at least 500 MB free on the card.
2. Download **SNARTY-Y1-update-from-v0.5.zip**. Leave it zipped and rename the file to **update.zip**. Ensure the name is not `update.zip.zip` if your computer hides extensions.
3. Connect the Y1 for normal USB file transfer, or put its microSD card in a card reader. Copy `update.zip` into the **existing `.rockbox` folder at the card's root**. Enable hidden-file display if needed. The result must be `.rockbox/update.zip`, not `.rockbox/.rockbox/update.zip`. If an old `update.zip` is present, move it to your computer before replacing it.
4. Safely eject/disconnect the card/player. Reinsert the card if you used a reader. Start Rockbox.
5. Open **Main Menu → System → Firmware Update** and confirm the update. Let it finish and restart automatically; do not remove the card or interrupt power. If Firmware Update is absent, stop here and report that; don't substitute a ROM-flashing procedure.
6. After restart, open **Settings → Theme Settings → Browse Themes** and select **SNARTY-Y1**. The theme applies the library home-menu order and enables Gather Runtime Data. Your music should remain in place.
7. If needed, initialize/update the music database in Settings → General Settings → Database and restart when requested. Most Listened to uses plays actually collected by this device's database.

If the updater does not finish or restart, retain `.rockbox/update.log` and report its contents before trying another update. Do not repeatedly start it or delete system files. Keep the backup and official v0.5 recovery/update files.

## What was prepared and checked

- The official stable-v0.5 `update.zip` was downloaded from https://github.com/rockbox-y1/rockbox/releases/tag/stable-v0.5 and verified against GitHub's SHA-256 digest: `2f1b4e7be0094437d29de24b41303e4e52bd1cbb708923649ccbd19f5909b2c3`.
- Its Rockbox APK and native-library payload were replaced with the signed SNARTY-Y1-4 build. All native library files are taken directly from that signed APK. The APK signing certificate matches official v0.5.
- All other components inside `update/`, including the stock-app APK, helpers, key layouts and updater script, are byte-identical to the official v0.5 package. The official updater reinstalls those matching components as part of its normal workflow.
- The SNARTY theme/fonts and database profile are additional outer-archive entries. The verified installed updater extracts them into `/sdcard/.rockbox/` before processing `update/`.
- ZIP integrity, component equality, APK signatures and the updater's host-simulated extraction/copy sequence were checked. In that simulation, music, playlists, existing `config.cfg` and listening-history journal sentinel files were preserved. Privileged mount/chown/package-install/reboot commands were mocked; this is not a device installation test.

**Physical Y1 installation remains untested.** This is a development update, not an officially supported release. Speech controls have been removed. See `UPDATE-VALIDATION.json` for the recorded checks.

## Files

- `SNARTY-Y1-update-from-v0.5.zip`: installable SD update; rename to `update.zip` without extracting.
- `snarty-y1-source.zip`: source patch and SNARTY customization sources corresponding to this Rockbox build; based on repository commit `9c92b93a5d582b3819a119162a14ad0b4178d2cd`.
- `UPDATE-VALIDATION.json` and `SHA256SUMS`: validation details and update-archive digest.

The SNARTY adaptation retains its CC BY-SA 4.0 credits. Rockbox changes retain the project's GPL licensing. See the source archive and Rockbox's COPYING/LICENSES files.

## Revision 4: internal MP4 player

This Y1 build lists .mp4 files in Database → Videos. Opening an MP4 under the storage-root Videos folder (including nested folders) launches Rockbox's internal Android video screen with SNARTY colors, a seekable progress bar, elapsed/total time, Play/Pause/Replay, and Back. MP4 files elsewhere retain their existing music-browser behavior. Existing MPEG files still use Rockbox's MPEG plugin.

Copy an actual MP4 into `Videos` at the card root, beside `.rockbox`. Merely creating that folder does not download videos. If a downloader saved MP3 audio, obtain the actual video first; audio cannot be converted back into the missing video. This update does not modify an external sync/downloader app.

The player uses the Y1 Android platform's installed media decoder. H.264 Baseline video with AAC-LC audio, yuv420p, 480x360 or smaller, 25/30 fps is the recommended starting point; the actual supported profiles/resolutions depend on the device. Unsupported or audio-only files display an error. No claim is made that every MP4 codec works. Download the separate SNARTY-video-test.mp4 clip from this branch and copy it into Videos to test independently of the sync app.

Controls: center/Play toggles playback; previous/next seek ten seconds; wheel backward/forward seek five seconds; Android Back or the Back button returns to the Videos browser. The progress bar updates during playback and can be dragged on touch-capable input. Normal volume buttons adjust media volume. Leaving the screen releases video playback. Interrupted video resumes within the same Activity session; reopening a file starts from the beginning. Music is paused before opening the video and its queue is retained; it is not automatically restarted after exit.

The existing navigation fixes, Podcasts folder, color album art, local Wrapped history and Carlink removal are retained. Physical Y1 video decoding, sound, button behavior and installation still require testing on the actual device. The desktop simulator does not emulate Android media codecs or this Activity.

The optional SNARTY-video-test.zip contains a Videos folder with the test clip. Extract that test ZIP to the card root beside .rockbox. It is separate from the firmware update ZIP, which must remain zipped as .rockbox/update.zip.
