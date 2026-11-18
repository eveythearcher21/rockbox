# SNARTY-Y1-15 plugin repair

This is based on exact v15 commit 951d8aa303199ae9c544179bb7c5f5e32ff7551f, not v12 or the Wi-Fi experiment. Keep a backup of the existing .rockbox folder and v15 APK.

Put SNARTY-Y1-15-PLUGINS-FIXED.apk beside adb.exe and update without uninstalling:

```powershell
.\adb.exe install --no-streaming -r -f SNARTY-Y1-15-PLUGINS-FIXED.apk
.\adb.exe shell am start -n org.rockbox/.RockboxActivity
```

Run the second command only after the install reports Success. The package remains org.rockbox and uses the original signing certificate. No data clearing, ROM flashing or wheel-map changes are required.

First mounted startup installs all matching bundled plugins automatically to .rockbox/rocks, backing up replaced binaries with .before-plugins15. Existing plugin resource/settings files are preserved. The .snarty-plugins-fixed15 marker makes this once-only so later manual additions are retained.

The separate SNARTY-Y1-15-PLUGINS.zip contains the same complete plugin/resource payload. For manual installation: back up D:\.rockbox, extract the ZIP and merge its .rockbox directory into D:\ so D:\.rockbox\rocks\apps\lrcplayer.rock exists. Replace the matching binaries; preserve user-modified resource/settings files. Safely eject Windows transfers before opening Rockbox; Android cannot access a USB-shared card.

Test Settings > Additional Features > Plugins > Applications/Games/Demos, Files > .rockbox > rocks > apps > lrcplayer.rock, and Lyrics from the playing-song menu. Song-menu Lyrics retains v15's timed SNARTY mode; a nonplaying held song retains its manual Preview. Check real word-LRC highlighting on the player.

Application-private plugin-cache files are generated automatically; do not copy plugins into /data or change permissions manually. Android errors are logged with RockboxPlugin or RockboxService tags. To collect diagnostics:

```powershell
.\adb.exe logcat -d > Y1-plugin-log.txt
```

Physical Y1/plugin execution and all gameplay remain owner acceptance checks. Some plugins require separately supplied game/media data; this package includes the build's resources, not commercial game assets. Do not describe missing game data as a proven loader failure.
