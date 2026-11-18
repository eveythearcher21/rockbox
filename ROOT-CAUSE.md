# Plugin repair findings

Base: exact SNARTY-Y1-15 commit 951d8aa303199ae9c544179bb7c5f5e32ff7551f. The existing APK was inspected and matched SHA256 6ad6e54a108efb9ee499a7f5be1a7ae610e82ce7d4025ab391a87c85dbce6f17. This work is isolated from v12 and the later desktop Wi-Fi experiment.

Confirmed source/package defects:

* Y1 PLUGIN_DIR pointed into ROCKBOX_LIBRARY_PATH/.rockbox/rocks while storage had .rockbox/rocks. Plugin menus, viewers and song Lyrics inherit this macro.
* Resource extraction removed only the sdcard component, then appended the remaining .rockbox component to a destination already ending in .rockbox. This creates a duplicated private .rockbox/.rockbox layout and fails to populate the menu path.
* Hosted PLUGIN_DATA_DIR is .rockbox/rocks.data, but the original APK had no rocks.data entries. Categorized resources were packaged under rocks/apps, rocks/games, etc.
* lc_open used dlopen directly on the requested filesystem. External Android storage commonly cannot supply executable mappings. The actual Y1 mount/error was not captured here; this restriction is handled defensively rather than reported as an observed device errno.

The fix defines discovery using ROCKBOX_DIR/rocks, preserves the existing storage mapper and translates legacy private plugin shortcuts. Startup extraction now normalizes the complete archive prefix and prevents traversal. A once-only paired installer publishes all 167 matching plugins and six overlays on mounted storage, backing up originals; resources/settings already present are preserved. Categorized resource files are also paired at the hosted rocks.data paths.

Only .rock/.ovl execution passes through an application-owned cache. Java validates a bounded ELF32 little-endian ARM shared object, computes SHA256, stages/syncs bytes in getDir(plugin-cache), sets owner execute/read permissions and atomically publishes the content-addressed file. Changed sources generate new identities; damaged cache files are detected and repaired. C dlopen loads that private file, while plugin.c retains the original requested identity and existing target/API/size checks. Codec .so loading is unchanged. Loader/cache failures produce Android log diagnostics. Full compatibility remains checked by the native caller; ELF validation is not a security proof of arbitrary third-party plugin code.

All UI, button, playback, artwork, navigation, Favorites, video, screensaver, library ordering, recommendations and history implementations remain from exact v15. The LRC Player source and timed/word/selected-preview modes are unchanged; the rebuild changes their paths and pairs the loader/resources. Some games need separately supplied assets; this repair does not bundle commercial game data.
