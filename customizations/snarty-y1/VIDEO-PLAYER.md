# SNARTY Y1 internal MP4 player

This Y1 build lists .mp4 files in Database → Videos. Opening an MP4 under the storage-root Videos folder (including nested folders) launches Rockbox's internal Android video screen with SNARTY colors, a seekable progress bar, elapsed/total time, Play/Pause/Replay, and Back. MP4 files elsewhere retain their existing music-browser behavior. Existing MPEG files still use Rockbox's MPEG plugin.

Copy an actual MP4 into `Videos` at the card root, beside `.rockbox`. Merely creating that folder does not download videos. If a downloader saved MP3 audio, obtain the actual video first; audio cannot be converted back into the missing video. This update does not modify an external sync/downloader app.

The player uses the Y1 Android platform's installed media decoder. H.264 Baseline video with AAC-LC audio, yuv420p, 480x360 or smaller, 25/30 fps is the recommended starting point; the actual supported profiles/resolutions depend on the device. Unsupported or audio-only files display an error. No claim is made that every MP4 codec works. Download the separate SNARTY-video-test.mp4 clip from this branch and copy it into Videos to test independently of the sync app.

Controls: center/Play toggles playback; previous/next seek ten seconds; wheel backward/forward seek five seconds; Android Back or the Back button returns to the Videos browser. The progress bar updates during playback and can be dragged on touch-capable input. Normal volume buttons adjust media volume. Leaving the screen releases video playback. Interrupted video resumes within the same Activity session; reopening a file starts from the beginning. Music is paused before opening the video and its queue is retained; it is not automatically restarted after exit.

The existing navigation fixes, Podcasts folder, color album art, local Wrapped history and Carlink removal are retained. Physical Y1 video decoding, sound, button behavior and installation still require testing on the actual device. The desktop simulator does not emulate Android media codecs or this Activity.

## Implementation and validation

The file browser routes MP4 files under /sdcard/Videos/ to an explicit internal Android Activity before the audio queue branch. MP4 elsewhere retains normal audio behavior. A JNI byte-array bridge preserves UTF-8 filenames without shell commands. Service and Activity share canonical-root validation. The Activity is not exported.

Android VideoView handles aspect-fit video and platform decoding; the iPod S5L8702 H.264 hardware driver is not enabled on this device. Prepared/error/completion callbacks update controls, seeking is clamped to duration, and a handler updates elapsed time/progress every 250 ms. Dragging pauses and resumes only if previously playing. onPause removes handlers and releases playback. Media buttons are routed to the video before the music engine. Unsupported codecs, audio-only files and loading timeouts receive a readable error. Music is paused without replacing its queue.

Host tests cover file policy (canonical roots, Unicode and symlink escapes), timeline bounds/overflow/formatting, and the real JNI bridge's UTF-8 transport, failure exceptions and reference release. Native build, Java compilation and APK verification are separate checks. No Android emulator or physical Y1 video/audio playback is available in this environment. Test the provided clip on the device before relying on codec support or button behavior. This player does not download missing video or modify an external sync app.

## Test clip and conversion

SNARTY-video-test.zip contains only Videos/SNARTY-video-test.mp4. Extract that optional test ZIP to the card root, beside .rockbox; do not put it inside .rockbox or rename it update.zip. The clip is a self-generated 20-second moving test pattern with a quiet tone: H.264 Constrained Baseline Level 3.0, yuv420p, 320x240 at 25 fps, AAC-LC. Its container/streams were checked and decoded on the host; that is not a Y1 decoder test.

If an actual video uses an unsupported profile, a computer with FFmpeg can convert it:

```sh
ffmpeg -i input.mp4 -vf "scale=480:360:force_original_aspect_ratio=decrease:force_divisible_by=2" -c:v libx264 -profile:v baseline -level 3.0 -pix_fmt yuv420p -r 25 -maxrate 1M -bufsize 2M -c:a aac -ac 2 -ar 44100 -b:a 96k -movflags +faststart output.mp4
```

This requires an input that contains video. Copy output.mp4 into Videos. Naming an MP3 with an MP4 extension does not supply the missing picture.

## Revision 5 corrections and installation

Use the APK installer, not the old SD firmware ZIP. The app is ZIP-aligned and signed with the same platform certificate as the working recovery build, compiled with API17 Java/resource stubs, and declared internal-only. Install with `adb install --no-streaming -r -f SNARTY-Y1-8-video.apk`. This does not change key-layout files or the stock package. The pre-MP4 aligned recovery APK remains available for rollback without uninstalling or wiping data.

The main-thread SD sleep loop was removed in favor of a tested asynchronous StorageStartGate. Missing/shared/read-only storage shows a responsive waiting screen, retries automatically, and offers the existing stock-switch flow. Settings load after mount. While already running, Videos/Podcasts and the MP4 launch path check media storage availability before proceeding. Legacy config reading no longer uses the newer AutoCloseable contract, and libmisc follows Android's nativeLibraryDir. The screen preserves the user's play/pause intent over interruptions and logs numeric decoder errors with the RockboxVideo tag.

Actual playback is still the hardware acceptance step: install, check ordinary menu/wheel behavior, then test the supplied MP4 picture, quiet tone, moving timeline, pause/resume, seek and Back. No Android emulator or connected Y1 is available in the cloud. Host tests and API17 compilation do not establish the device's supported codec profiles. The external sync/downloader has not been modified.

## Revision 6 fullscreen and decoder errors

The video has the entire screen viewport and retains its aspect ratio (black bars for mismatched proportions). No permanent title or controls reserve screen space. Wheel or previous/next seeking and horizontal swipes reveal an overlay progress bar; it hides 1.2 seconds after interaction. Center or tapping toggles playback without revealing the bar. Back returns to Videos. Decoder runtime exceptions during prepare, start, pause, seek, polling and release are logged and handled; late callbacks while inactive are ignored. This does not establish that every possible crash is fixed: physical device testing and any reported crash trace remain necessary.

## Revision 7 decoder thread

The user reports one MP4 works and others do not; the supplied log has no Rockbox crash or decoder error. Codec/profile/resolution differences are plausible, not confirmed. VideoView was replaced by AsyncVideoView: all MediaPlayer creation, file opening, preparation, metadata, playback, seek, polling, reset and release execute on one decoder worker. UI reads cached position/dimensions/state, never waits for that worker, and shows the existing timeout while a stalled open runs. Session generation rejects stale callbacks/commands; polling allows one outstanding request. Back/cleanup do not wait for decoder release. No new codecs or on-device transcoder are provided. A wedged vendor decoder may outlive a closed screen; UI isolation cannot restart Android's media server or guarantee every file plays. Fullscreen aspect-fit and transient seek overlay remain.
