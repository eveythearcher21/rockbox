# SNARTY-Y1-3 recovery APK

This is the pre-MP4 SNARTY-Y1-3 application, with ZIP alignment corrected and the same platform signing certificate. Its code, resources and 43 native libraries are byte-identical to the earlier revision-3 APK. Alignment and Android API17 JAR-signature verification pass; physical installation is untested. Source: https://github.com/eveythearcher21/rockbox/tree/snarty-y1-revision-3-25866255 . This does not establish the cause of the later startup hang.

The owner's stock app is currently working and Rockbox has been disabled. Keep stock available during recovery. Do not install another ROM, uninstall the existing app, use downgrade/force flags, or overwrite system libraries manually in response to an installer error. Collect the exact error instead.

## Windows installation checkpoint

1. Keep a backup of the card's .rockbox folder. While Rockbox is disabled, a connected device can be copied with `adb pull /sdcard/.rockbox Y1-before-recovery`.
2. Download SNARTY-Y1-3-recovery.apk into the folder containing adb.exe. Keep it as an APK.
3. Run `adb install --no-streaming -r SNARTY-Y1-3-recovery.apk`. This asks Android's package manager to install the application and extract its matching native libraries together, retaining existing application data if it recognizes an existing install.
4. Stop at the result. Report Success or the exact error, then inspect the package path/version before attempting to start Rockbox. Do not reboot or choose Back to Rockbox yet. The stock wheel mapping is still active; the matching Rockbox mapping must be restored when switching back, after installation and startup are checked.

The API17 signature check verifies signing compatibility, not all runtime behavior. This version retains the prior menu/navigation, Podcasts, local Wrapped history and SNARTY color-art work, but does not include the MP4 Android video player. Existing MPEG video support remains. The MP4 update needs further diagnosis from the actual device logs and package state.
