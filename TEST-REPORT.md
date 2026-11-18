# Verification

Passed:

* Original v15 source commit and APK SHA256 identified and inspected.
* Clean full target310 ARMv7 build at480x360, including 167 .rock plugins and six .ovl viewers.
* Android Java/resources compiled against API17; package org.rockbox unchanged.
* Actual cache Java test: exact copied bytes, executable private file, stable identity across reuse, changed-source refresh, corrupted-cache recovery and invalid ARM ELF rejection.
* Actual paired installer Java test: Applications/Games/Demos/Viewers paths, replaced-binary backup, preserved existing plugin data, once-only behavior across restart.
* Actual APK payload ELF test: all167 plugin headers have target125, plugin API285 and identical API table size1608; ELF32 ARM ET_DYN. Compiled core contains expected storage category and LRC paths. Six overlays and71 hosted resources included.
* All plugin/overlay strong dynamic imports resolve against NDK API17 public symbols or exported core symbols.
* APK signatures verified for API17 and full v1/v2; zipalign checked after signing. Certificate matches original releases.
* Complete matching plugin ZIP is extracted directly from the signed APK's paired payload.
* Preservation check: existing v15 feature source files remain unchanged except plugin paths, loader, extraction and packaging. Lyrics mode source is unchanged.

Pending, not claimed:

* No physical Y1 or Android emulator was attached. Actual Android dlopen/cache execution, Applications/Games/Demos launch, direct .rock launch, LRC audio-clock/word highlighting, viewer resource consumption, physical wheel/video/standby and individual game behavior require device acceptance.
* Host tests record installation/cache behavior; they do not execute ARM instructions or establish that every third-party game/data combination works.

Reproduction: configure target310 normal480x360 from the exact v15 base plus source.patch, using retained NDKr10e/GCC4.9, Java/resources android17 and Build Tools28.0.3. Build all native targets, classes, zip and unsigned-apk with VERSION=SNARTY-Y1-15-PLUGINS-FIXED. Align before signing with the existing platform certificate, then verify API17/full signatures and final alignment. Run PluginRepairTest.java with production PluginCache/PairedPlugins, and plugin_package_test.py on the signed APK. The environment setup/build foundation is documented in customizations/snarty-y1/README.md. Do not replace keys or bypass signature checks.
