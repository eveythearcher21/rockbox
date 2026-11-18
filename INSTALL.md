# SNARTY-Y1-16 Wi-Fi / sync test build

Update the existing app without uninstalling. Back up .rockbox and retain revision15. Place SNARTY-Y1-16-wifi-sync.apk beside adb.exe, pause playback and run:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-16-wifi-sync.apk
```

Only after Success:

```powershell
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

This preserves the existing theme, music, Favorites, settings and wheel mappings. It does not flash a ROM. Check Rockbox Info for SNARTY-Y1-16.

Settings → Wi-Fi enables/scans/connects to a compatible home network. Music → Sync Library starts a sync and displays status. Automatic sync needs initial pairing and the computer bridge running; the APK does not log directly into Google. Downloads are verified and do not replace the current queue or silently delete files.

Extract SNARTY-Y1-16-wireless-bridge.zip on your computer and follow WIRELESS-16.md. START-WIFI-SYNC.cmd requires Python3.11+. Choose the existing Syncer export or the optional account adapter (desktop authorization and FFmpeg required). Copy the generated wireless-pairing.json once to .rockbox/snarty/wireless-pairing.json, finish/eject USB transfers and import it through Settings → Wi-Fi → Syncer Pairing / Library. The key is consumed into private app storage. Keep Google credentials off the Y1 and outside the media export.

The source adapter transfers real playable MP3s, all available metadata, covers/artist portraits and exact playlist/source ordering. It fetches real line/plain lyrics where available and preserves existing word-LRC. It cannot guarantee that YouTube supplies every lyric, word timestamp, genre or portrait; missing data is reported. The existing Syncer GUI has not been modified without its repository; the separate bridge and handoff are included.

Build/API17/signature, simulator, actual local-network transfer and recording-provider/controller tests passed. Physical Y1 Wi-Fi/router/idle/video stability, Windows launcher/firewall and live Google-account acceptance remain pending. Read UPDATE-VALIDATION.json and WIRELESS-16.md for limits. This is an experimental update.

Rollback update-install the same-signature prior APK without uninstalling:
https://github.com/eveythearcher21/rockbox/raw/refs/heads/snarty-y1-song-art-15-6ad6e54a/SNARTY-Y1-15-song-menus-artwork.apk

Corresponding source and GPL notices are provided in snarty-y1-16-source.zip.
