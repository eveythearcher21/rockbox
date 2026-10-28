/* Internal SNARTY Y1 video player. Rockbox GPLv2 or later. */
package org.rockbox;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.VideoView;
import java.io.File;
import java.lang.ref.WeakReference;

/** Android decodes the local MP4; Rockbox supplies the browser and music queue.
 * This is an internal screen with SNARTY colors, not an external player app. */
public class RockboxVideoActivity extends Activity {
    private static final int BACKGROUND = Color.rgb(35, 34, 52);
    private static final int LAVENDER = Color.rgb(162, 172, 205);
    private static final int MINT = Color.rgb(165, 230, 186);
    private static WeakReference<RockboxVideoActivity> current =
        new WeakReference<RockboxVideoActivity>(null);
    private final Handler handler = new Handler();
    private VideoView video;
    private SeekBar progress;
    private TextView times, message;
    private LinearLayout seekOverlay;
    private File file;
    private boolean active, prepared, dragging, resumeAfterDrag, failed;
    private boolean wantsPlay = true;
    private int position, duration;

    public static boolean isActive() {
        RockboxVideoActivity activity = current.get();
        return activity != null && activity.active;
    }
    public static boolean handleMediaButton(KeyEvent event) {
        RockboxVideoActivity activity = current.get();
        return activity != null && activity.active && event != null &&
               activity.playbackKey(event);
    }
    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
    private TextView text(String value, int size) {
        TextView view = new TextView(this);
        view.setText(value);view.setTextSize(size);view.setTextColor(LAVENDER);
        view.setTypeface(Typeface.MONOSPACE);view.setGravity(Gravity.CENTER);
        return view;
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                             WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setVolumeControlStream(android.media.AudioManager.STREAM_MUSIC);
        try {
            file = VideoFiles.resolve(new File("/sdcard/Videos"),
                                     getIntent().getStringExtra("video_path"));
        } catch (Exception error) {
            finish();return;
        }
        if (state != null) {
            position = state.getInt("position", 0);
            wantsPlay = state.getBoolean("playing", true);
        }
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);
        video = new VideoView(this);
        root.addView(video, new FrameLayout.LayoutParams(-1, -1, Gravity.CENTER));
        message = text("Loading video...", 13);
        message.setPadding(dp(10), dp(4), dp(10), dp(4));
        root.addView(message, new FrameLayout.LayoutParams(-1, -1, Gravity.CENTER));
        seekOverlay = new LinearLayout(this);
        seekOverlay.setOrientation(LinearLayout.VERTICAL);
        seekOverlay.setBackgroundColor(0xcc232234);
        progress = new SeekBar(this);progress.setEnabled(false);progress.setFocusable(false);
        seekOverlay.addView(progress, new LinearLayout.LayoutParams(-1, dp(32)));
        times = text("0:00 / 0:00", 11);
        seekOverlay.addView(times, new LinearLayout.LayoutParams(-1, dp(20)));
        root.addView(seekOverlay, new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM));
        seekOverlay.setVisibility(View.GONE);
        setContentView(root);
        // Swiping horizontally seeks; a tap pauses/resumes without opening chrome.
        root.setOnTouchListener(new View.OnTouchListener() {
            private float startX;
            private int startPosition;
            private boolean seeking;
            public boolean onTouch(View view, android.view.MotionEvent event) {
                if (!prepared || failed) return true;
                if (event.getAction() == android.view.MotionEvent.ACTION_DOWN) {
                    startX = event.getX();startPosition = position;seeking = false;
                } else if (event.getAction() == android.view.MotionEvent.ACTION_MOVE) {
                    float distance = event.getX() - startX;
                    if (Math.abs(distance) > dp(12)) seeking = true;
                    if (seeking) {
                        int delta = (int)(distance * 60000 / Math.max(1, view.getWidth()));
                        seekTo(VideoTimeline.seek(startPosition, delta, duration));
                    }
                } else if (event.getAction() == android.view.MotionEvent.ACTION_UP) {
                    if (!seeking) togglePlay();
                    hideSeekLater();
                } else if (event.getAction() == android.view.MotionEvent.ACTION_CANCEL) {
                    hideSeekLater();
                }
                return true;
            }
        });
        progress.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar bar, int value, boolean fromUser) {
                if (fromUser) showTime(value);
            }
            public void onStartTrackingTouch(SeekBar bar) {
                handler.removeCallbacks(hideSeek);
                try {
                    dragging = true;resumeAfterDrag = prepared && video.isPlaying();
                    if (prepared) video.pause();
                } catch (RuntimeException error) { dragging = false;playbackFailure(error); }
            }
            public void onStopTrackingTouch(SeekBar bar) {
                try {
                if (prepared && active && !failed) {
                    position = VideoTimeline.clamp(bar.getProgress(), duration);
                    video.seekTo(position);
                    if (resumeAfterDrag && active) video.start();
                }
                } catch (RuntimeException error) { playbackFailure(error); }
                dragging = false;hideSeekLater();
            }
        });
        video.setOnPreparedListener(new MediaPlayer.OnPreparedListener() {
            public void onPrepared(MediaPlayer player) {
                if (!active || failed || isFinishing()) return;
                try {
                handler.removeCallbacks(loadTimeout);
                boolean hasVideo = player.getVideoWidth() > 0 && player.getVideoHeight() > 0;
                try {
                    MediaPlayer.TrackInfo[] tracks = player.getTrackInfo();
                    if (tracks != null) {
                        hasVideo = false;
                        for (MediaPlayer.TrackInfo track : tracks)
                            if (track.getTrackType() == MediaPlayer.TrackInfo.MEDIA_TRACK_TYPE_VIDEO)
                                hasVideo = true;
                    }
                } catch (RuntimeException unsupportedMetadata) {
                    /* Some vendor decoders expose dimensions but no track list. */
                }
                if (!hasVideo) { showError("This MP4 contains no video track.");return; }
                prepared = true;duration = Math.max(0, video.getDuration());
                position = VideoTimeline.clamp(position, duration);
                progress.setMax(Math.max(1, duration));progress.setEnabled(duration > 0);
                video.seekTo(position);message.setVisibility(View.GONE);
                if (wantsPlay) video.start();
                updateProgress();
                } catch (RuntimeException error) { playbackFailure(error); }
            }
        });
        video.setOnErrorListener(new MediaPlayer.OnErrorListener() {
            public boolean onError(MediaPlayer player, int what, int extra) {
                if (!active || failed) return true;
                android.util.Log.e("RockboxVideo", "MediaPlayer error " + what + "/" + extra);
                showError("Cannot play video (" + what + "/" + extra + "). Try a small H.264/AAC MP4.");
                return true;
            }
        });
        video.setOnCompletionListener(new MediaPlayer.OnCompletionListener() {
            public void onCompletion(MediaPlayer player) {
                if (!active || failed) return;
                wantsPlay = false;position = duration;progress.setProgress(duration);
                showTime(duration);
                video.setKeepScreenOn(false);
            }
        });
    }
    private void showError(String reason) {
        handler.removeCallbacks(loadTimeout);
        failed = true;prepared = false;wantsPlay = false;
        releaseVideo();
        progress.setEnabled(false);seekOverlay.setVisibility(View.GONE);
        handler.removeCallbacks(tick);handler.removeCallbacks(hideSeek);
        message.setText(reason);message.setVisibility(View.VISIBLE);
    }
    private void showTime(int at) {
        times.setText(VideoTimeline.time(at) + " / " + VideoTimeline.time(duration));
    }
    private void updateProgress() {
        if (prepared && !dragging) {
            position = VideoTimeline.clamp(video.getCurrentPosition(), duration);
            progress.setProgress(position);showTime(position);
            video.setKeepScreenOn(video.isPlaying());
        }
    }
    private final Runnable tick = new Runnable() {
        public void run() {
            if (!active) return;
            try { updateProgress(); } catch (RuntimeException error) { playbackFailure(error); }
            if (!failed) handler.postDelayed(this, 250);
        }
    };
    private final Runnable loadTimeout = new Runnable() {
        public void run() {
            if (active && !prepared && !failed)
                showError("Video did not load. Check the file and its video codec.");
        }
    };
    private void togglePlay() {
        try { togglePlayback(); } catch (RuntimeException error) { playbackFailure(error); }
    }
    private void togglePlayback() {
        if (!prepared || failed) return;
        if (video.isPlaying()) {
            video.pause();wantsPlay = false;
        } else {
            if (position >= duration) { position = 0;video.seekTo(0); }
            video.start();wantsPlay = true;
        }
        updateProgress();
    }
    private final Runnable hideSeek = new Runnable() {
        public void run() { if (!dragging) seekOverlay.setVisibility(View.GONE); }
    };
    private void hideSeekLater() {
        handler.removeCallbacks(hideSeek);handler.postDelayed(hideSeek, 1200);
    }
    private void seekTo(int target) {
        if (!prepared || failed || !active || duration <= 0) return;
        try {
            position = VideoTimeline.clamp(target, duration);
            video.seekTo(position);progress.setProgress(position);showTime(position);
            seekOverlay.setVisibility(View.VISIBLE);hideSeekLater();
        } catch (RuntimeException error) { playbackFailure(error); }
    }
    private void seekBy(int delta) {
        if (!prepared || failed || !active || duration <= 0) return;
        try { seekTo(VideoTimeline.seek(video.getCurrentPosition(), delta, duration)); }
        catch (RuntimeException error) { playbackFailure(error); }
    }
    private void releaseVideo() {
        if (video == null) return;
        try { video.stopPlayback(); }
        catch (RuntimeException error) { android.util.Log.w("RockboxVideo", "Decoder release", error); }
        video.setKeepScreenOn(false);
    }
    private void playbackFailure(RuntimeException error) {
        android.util.Log.e("RockboxVideo", "Decoder operation failed", error);
        if (active && !failed) showError("Video playback stopped. Press Back and try another MP4.");
    }
    private boolean playbackKey(KeyEvent event) {
        int key = event.getKeyCode();
        boolean toggle = key == KeyEvent.KEYCODE_ENTER || key == KeyEvent.KEYCODE_DPAD_CENTER ||
                         key == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE;
        boolean back = key == KeyEvent.KEYCODE_DPAD_LEFT || key == KeyEvent.KEYCODE_MEDIA_PREVIOUS;
        boolean next = key == KeyEvent.KEYCODE_DPAD_RIGHT || key == KeyEvent.KEYCODE_MEDIA_NEXT;
        boolean wheelBack = key == KeyEvent.KEYCODE_MEDIA_PLAY;
        boolean wheelNext = key == KeyEvent.KEYCODE_MEDIA_PAUSE;
        boolean stop = key == KeyEvent.KEYCODE_MEDIA_STOP;
        if (!(toggle || back || next || wheelBack || wheelNext || stop)) return false;
        if (event.getAction() == KeyEvent.ACTION_DOWN) {
            if (stop) { if (event.getRepeatCount() == 0) finish(); }
            else if (toggle) { if (event.getRepeatCount() == 0) togglePlay(); }
            else seekBy(back ? -10000 : next ? 10000 : wheelBack ? -5000 : 5000);
        }
        return true;
    }
    @Override public boolean dispatchKeyEvent(KeyEvent event) {
        return playbackKey(event) || super.dispatchKeyEvent(event);
    }
    private void clearNativeButtons() {
        RockboxService service = RockboxService.getInstance();
        if (service != null && service.isRockboxRunning())
            RockboxFramebuffer.buttonHandler(KeyEvent.KEYCODE_UNKNOWN, false);
    }
    @Override protected void onResume() {
        super.onResume();
        if (file == null || video == null || failed) return;
        /* The launching key can be released after the native view loses focus.
         * UNKNOWN clears the Y1 native button latch without pressing a key. */
        clearNativeButtons();
        active = true;current = new WeakReference<RockboxVideoActivity>(this);
        message.setText("Loading video...");message.setVisibility(View.VISIBLE);
        seekOverlay.setVisibility(View.GONE);
        try {
            video.setVideoURI(Uri.fromFile(file));handler.post(tick);
            handler.postDelayed(loadTimeout, 30000);
        } catch (RuntimeException error) { playbackFailure(error); }
    }
    @Override protected void onPause() {
        active = false;
        if (current.get() == this) current.clear();
        handler.removeCallbacks(tick);
        handler.removeCallbacks(hideSeek);
        handler.removeCallbacks(loadTimeout);
        clearNativeButtons();
        if (video != null) {
            if (prepared) {
                try { position = video.getCurrentPosition(); }
                catch (RuntimeException error) { android.util.Log.w("RockboxVideo", "Save position", error); }
                if (dragging) wantsPlay = resumeAfterDrag;
            }
            prepared = false;dragging = false;releaseVideo();
        }
        super.onPause();
    }
    @Override protected void onSaveInstanceState(Bundle state) {
        if (prepared && !dragging) {
            try { position = video.getCurrentPosition(); }
            catch (RuntimeException error) { android.util.Log.w("RockboxVideo", "Save state", error); }
        }
        state.putInt("position", position);state.putBoolean("playing", wantsPlay);
        super.onSaveInstanceState(state);
    }
}
