# SNARTY-Y1-11 playback test

An experimental paired APK for Innioasis Y1 Android4.2/API17. Includes all previous Home/Music, video, startup and complete-queue Shuffle changes. Read PLAYBACK-FEATURES.md for scope and SYNC-CONTRACT.md for the companion data required by new features.

Back up the card's .rockbox folder and keep the previous APK. Download SNARTY-Y1-11-playback-test.apk beside adb.exe. Pause playback and run on Windows:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-11-playback-test.apk
```

Only after Success:

```powershell
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Finish transfers and safely eject Windows storage before unplugging so Android can mount the card. First launch installs the paired theme/plugin with .before-snarty11 backups and a once-only marker; it appends matching theme settings, preserving unrelated settings. Later user theme changes survive startup. Music/playlists/listening history remain. Never uninstall to bypass a signature error, flash a ROM, replace wheel mappings or apply an old firmware ZIP.

One center click on playback opens Album, Artist, Play Similar Songs, Lyrics, Add to Playlist..., Current Playlist. Back returns to playback. Browse Albums for artwork cards and expanding detail. Songs/Albums have [Recently Added] above the first real item. Genuine account ordering requires the sync manifest; word highlights require enhanced LRC. The APK itself does not fetch YouTube Music.

The other chat should implement the companion using COMPANION-PROMPT.md and SYNC-CONTRACT.md; reference Python writers are in customizations/snarty-y1/tools on the source branch. GUI APK install can bundle ADB so terminal commands are unnecessary, but device USB authorization is still required.

Shared-code simulator and host checks are documented in UPDATE-VALIDATION.json. Physical Y1 animation speed, LCD, video and standby acceptance remain pending.

For rollback, update-install the previous matching-signature revision10 APK without uninstalling:
https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-layout-10-210a651c/SNARTY-Y1-10-layout-test.apk

Restore .before-snarty11 card theme/config backups if reverting the visual layout. Keep the new files backed up first. The source ZIP is a complete corresponding-source patch against the documented base, including new files/tests/assets and retained license attribution.
