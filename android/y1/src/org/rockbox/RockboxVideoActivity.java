/* Internal SNARTY Y1 video player. Rockbox GPLv2 or later. */
package org.rockbox;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.PorterDuff;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.LayerDrawable;
import android.graphics.drawable.StateListDrawable;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
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
    private Button play;
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
    private GradientDrawable color(int value) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(value);shape.setCornerRadius(dp(5));return shape;
    }
    private Button button(String label, View.OnClickListener listener) {
        Button button = new Button(this);
        button.setText(label);button.setTextSize(12);button.setTextColor(BACKGROUND);
        button.setTypeface(Typeface.MONOSPACE);button.setMinHeight(0);button.setMinimumHeight(0);
        button.setMinWidth(0);button.setMinimumWidth(0);button.setPadding(dp(4), 0, dp(4), 0);
        StateListDrawable background = new StateListDrawable();
        background.addState(new int[]{android.R.attr.state_pressed}, color(MINT));
        background.addState(new int[]{android.R.attr.state_focused}, color(MINT));
        background.addState(new int[]{}, color(LAVENDER));
        button.setBackgroundDrawable(background);button.setOnClickListener(listener);
        return button;
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
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(BACKGROUND);
        TextView title = text(file.getName(), 13);
        title.setSingleLine(true);title.setEllipsize(android.text.TextUtils.TruncateAt.END);
        title.setTextColor(MINT);root.addView(title, new LinearLayout.LayoutParams(-1, dp(24)));
        FrameLayout frame = new FrameLayout(this);
        video = new VideoView(this);
        frame.setBackgroundColor(Color.BLACK);
        frame.addView(video, new FrameLayout.LayoutParams(-1, -1, Gravity.CENTER));
        message = text("Loading video...", 13);
        message.setPadding(dp(10), dp(4), dp(10), dp(4));
        frame.addView(message, new FrameLayout.LayoutParams(-1, -1, Gravity.CENTER));
        root.addView(frame, new LinearLayout.LayoutParams(-1, 0, 1));
        progress = new SeekBar(this);progress.setEnabled(false);
        if (progress.getProgressDrawable() instanceof LayerDrawable) {
            android.graphics.drawable.Drawable fill = ((LayerDrawable)progress.getProgressDrawable())
                .findDrawableByLayerId(android.R.id.progress);
            if (fill != null) fill.setColorFilter(MINT, PorterDuff.Mode.SRC_IN);
        }
        if (progress.getThumb() != null)
            progress.getThumb().setColorFilter(LAVENDER, PorterDuff.Mode.SRC_IN);
        root.addView(progress, new LinearLayout.LayoutParams(-1, dp(24)));
        times = text("0:00 / 0:00", 11);
        root.addView(times, new LinearLayout.LayoutParams(-1, dp(18)));
        LinearLayout controls = new LinearLayout(this);
        controls.setPadding(dp(4), 0, dp(4), dp(4));
        Button back = button("Back", new View.OnClickListener() {
            public void onClick(View view) { finish(); }
        });
        Button rewind = button("-10s", new View.OnClickListener() {
            public void onClick(View view) { seekBy(-10000); }
        });
        play = button("Pause", new View.OnClickListener() {
            public void onClick(View view) { togglePlay(); }
        });
        Button forward = button("+10s", new View.OnClickListener() {
            public void onClick(View view) { seekBy(10000); }
        });
        for (Button item : new Button[]{back, rewind, play, forward}) {
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, dp(30), 1);
            params.setMargins(dp(2), 0, dp(2), 0);controls.addView(item, params);
        }
        root.addView(controls);setContentView(root);play.requestFocus();
        progress.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar bar, int value, boolean fromUser) {
                if (fromUser) showTime(value);
            }
            public void onStartTrackingTouch(SeekBar bar) {
                dragging = true;resumeAfterDrag = prepared && video.isPlaying();
                if (prepared) video.pause();
            }
            public void onStopTrackingTouch(SeekBar bar) {
                if (prepared) {
                    position = VideoTimeline.clamp(bar.getProgress(), duration);
                    video.seekTo(position);
                    if (resumeAfterDrag && active) video.start();
                }
                dragging = false;
            }
        });
        video.setOnPreparedListener(new MediaPlayer.OnPreparedListener() {
            public void onPrepared(MediaPlayer player) {
                if (!active) return;
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
                play.setText(wantsPlay ? "Pause" : "Play");updateProgress();
            }
        });
        video.setOnErrorListener(new MediaPlayer.OnErrorListener() {
            public boolean onError(MediaPlayer player, int what, int extra) {
                android.util.Log.e("RockboxVideo", "MediaPlayer error " + what + "/" + extra);
                showError("Cannot play video (" + what + "/" + extra + "). Try a small H.264/AAC MP4.");
                return true;
            }
        });
        video.setOnCompletionListener(new MediaPlayer.OnCompletionListener() {
            public void onCompletion(MediaPlayer player) {
                wantsPlay = false;position = duration;progress.setProgress(duration);
                showTime(duration);play.setText("Replay");
                video.setKeepScreenOn(false);
            }
        });
    }
    private void showError(String reason) {
        handler.removeCallbacks(loadTimeout);
        failed = true;prepared = false;wantsPlay = false;
        video.stopPlayback();video.setKeepScreenOn(false);
        progress.setEnabled(false);play.setEnabled(false);
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
            updateProgress();handler.postDelayed(this, 250);
        }
    };
    private final Runnable loadTimeout = new Runnable() {
        public void run() {
            if (active && !prepared && !failed)
                showError("Video did not load. Check the file and its video codec.");
        }
    };
    private void togglePlay() {
        if (!prepared || failed) return;
        if (video.isPlaying()) {
            video.pause();wantsPlay = false;
        } else {
            if (position >= duration) { position = 0;video.seekTo(0); }
            video.start();wantsPlay = true;
        }
        play.setText(wantsPlay ? "Pause" : "Play");updateProgress();
    }
    private void seekBy(int delta) {
        if (!prepared || duration <= 0) return;
        position = VideoTimeline.seek(video.getCurrentPosition(), delta, duration);
        video.seekTo(position);progress.setProgress(position);showTime(position);
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
        video.setVideoURI(Uri.fromFile(file));handler.post(tick);
        handler.postDelayed(loadTimeout, 30000);
    }
    @Override protected void onPause() {
        active = false;
        if (current.get() == this) current.clear();
        handler.removeCallbacks(tick);
        handler.removeCallbacks(loadTimeout);
        clearNativeButtons();
        if (video != null) {
            if (prepared) {
                position = video.getCurrentPosition();
                if (dragging) wantsPlay = resumeAfterDrag;
            }
            prepared = false;dragging = false;video.stopPlayback();video.setKeepScreenOn(false);
        }
        super.onPause();
    }
    @Override protected void onSaveInstanceState(Bundle state) {
        if (prepared && !dragging) position = video.getCurrentPosition();
        state.putInt("position", position);state.putBoolean("playing", wantsPlay);
        super.onSaveInstanceState(state);
    }
}
