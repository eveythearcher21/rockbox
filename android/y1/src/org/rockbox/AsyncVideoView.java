/* Rockbox GPLv2 or later. API17 video decoder isolated from the UI thread. */
package org.rockbox;

import android.content.Context;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicInteger;

/** Vendor codec calls can block without throwing. Never call them on the UI. */
public final class AsyncVideoView extends SurfaceView implements SurfaceHolder.Callback {
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final ExecutorService decoder = Executors.newSingleThreadExecutor(new ThreadFactory() {
        public Thread newThread(Runnable task) {
            Thread thread = new Thread(task, "Y1-video-decoder");thread.setDaemon(true);return thread;
        }
    });
    private final AtomicInteger generation = new AtomicInteger();
    private MediaPlayer player; // decoder thread only
    private Uri source;
    private boolean surfaceReady;
    private volatile boolean closed;
    private volatile int duration, position, width, height;
    private volatile boolean playing, videoTrack;
    private MediaPlayer.OnPreparedListener preparedListener;
    private MediaPlayer.OnErrorListener errorListener;
    private MediaPlayer.OnCompletionListener completionListener;

    public AsyncVideoView(Context context) { super(context);getHolder().addCallback(this); }
    public void setOnPreparedListener(MediaPlayer.OnPreparedListener listener) { preparedListener = listener; }
    public void setOnErrorListener(MediaPlayer.OnErrorListener listener) { errorListener = listener; }
    public void setOnCompletionListener(MediaPlayer.OnCompletionListener listener) { completionListener = listener; }
    public int getDuration() { return duration; }
    public int getCurrentPosition() { return position; }
    public boolean isPlaying() { return playing; }
    public boolean hasVideoTrack() { return videoTrack; }
    private void submit(final Runnable task) {
        if (!closed) {
            try { decoder.execute(task); }
            catch (java.util.concurrent.RejectedExecutionException shuttingDown) { }
        }
    }
    private void reportError(final int session, final int what, final int extra) {
        if (session != generation.get() || closed) return;
        playing = false;
        ui.post(new Runnable() { public void run() {
            if (session == generation.get() && !closed && errorListener != null)
                errorListener.onError(null, what, extra);
        }});
    }
    private void release() {
        if (player != null) {
            MediaPlayer old = player;player = null;
            try { old.reset(); } catch (RuntimeException ignored) { }
            try { old.release(); } catch (RuntimeException ignored) { }
        }
    }
    public void setVideoURI(Uri uri) {
        source = uri;if (surfaceReady) open();
    }
    private void open() {
        final int session = generation.incrementAndGet();final Uri uri = source;
        duration = position = width = height = 0;playing = videoTrack = false;
        submit(new Runnable() { public void run() {
            release();if (session != generation.get()) return;
            try {
                final MediaPlayer media = new MediaPlayer();player = media;
                media.setOnPreparedListener(new MediaPlayer.OnPreparedListener() {
                    public void onPrepared(MediaPlayer ignored) {
                        submit(new Runnable() { public void run() {
                            if (session != generation.get() || player != media) return;
                            try {
                                duration = Math.max(0, media.getDuration());
                                width = media.getVideoWidth();height = media.getVideoHeight();
                                videoTrack = width > 0 && height > 0;
                                try {
                                    MediaPlayer.TrackInfo[] tracks = media.getTrackInfo();
                                    if (tracks != null) for (MediaPlayer.TrackInfo track : tracks)
                                        if (track.getTrackType() == MediaPlayer.TrackInfo.MEDIA_TRACK_TYPE_VIDEO)
                                            videoTrack = true;
                                } catch (RuntimeException unsupported) { }
                                ui.post(new Runnable() { public void run() {
                                    if (session != generation.get() || closed) return;
                                    requestLayout();
                                    if (preparedListener != null) preparedListener.onPrepared(null);
                                }});
                            } catch (RuntimeException error) { reportError(session, -1, 0); }
                        }});
                    }
                });
                media.setOnErrorListener(new MediaPlayer.OnErrorListener() {
                    public boolean onError(MediaPlayer ignored, int what, int extra) {
                        reportError(session, what, extra);return true;
                    }
                });
                media.setOnCompletionListener(new MediaPlayer.OnCompletionListener() {
                    public void onCompletion(MediaPlayer ignored) {
                        if (session != generation.get()) return;
                        playing = false;position = duration;
                        ui.post(new Runnable() { public void run() {
                            if (session == generation.get() && !closed && completionListener != null)
                                completionListener.onCompletion(null);
                        }});
                    }
                });
                media.setAudioStreamType(android.media.AudioManager.STREAM_MUSIC);
                media.setDataSource(getContext(), uri);
                if (session != generation.get()) { release();return; }
                media.setDisplay(getHolder());media.prepareAsync();
            } catch (Exception error) {
                android.util.Log.e("RockboxVideo", "Open decoder", error);
                reportError(session, -1, 0);release();
            }
        }});
    }
    private void command(final int kind, final int target) {
        final int session = generation.get();
        submit(new Runnable() { public void run() {
            if (session != generation.get() || player == null) return;
            try {
                if (kind == 0) { player.start();playing = true; }
                else if (kind == 1) { player.pause();playing = false; }
                else if (kind == 2) { player.seekTo(target);position = target; }
                else { position = player.getCurrentPosition();playing = player.isPlaying(); }
            } catch (RuntimeException error) { reportError(session, -1, 0); }
        }});
    }
    public void start() { playing = true;command(0, 0); }
    public void pause() { playing = false;command(1, 0); }
    public void seekTo(int target) { position = target;command(2, target); }
    // One outstanding poll at most, even if a vendor operation stalls.
    private final java.util.concurrent.atomic.AtomicBoolean polling = new java.util.concurrent.atomic.AtomicBoolean();
    public void poll() {
        if (!polling.compareAndSet(false, true)) return;
        final int session = generation.get();
        submit(new Runnable() { public void run() {
            try {
                if (session == generation.get() && player != null) {
                    position = player.getCurrentPosition();playing = player.isPlaying();
                }
            } catch (RuntimeException error) { reportError(session, -1, 0); }
            finally { polling.set(false); }
        }});
    }
    public void stopPlayback() {
        generation.incrementAndGet();source = null;playing = false;
        submit(new Runnable() { public void run() { release(); }});
    }
    public void close() {
        stopPlayback();closed = true;decoder.shutdown();
    }
    public void surfaceCreated(SurfaceHolder holder) { surfaceReady = true;if (source != null) open(); }
    public void surfaceChanged(SurfaceHolder holder, int format, int w, int h) { }
    public void surfaceDestroyed(SurfaceHolder holder) { surfaceReady = false;stopPlayback(); }
    @Override protected void onMeasure(int wSpec, int hSpec) {
        int w = getDefaultSize(0, wSpec), h = getDefaultSize(0, hSpec);
        if (width > 0 && height > 0) {
            if ((long)width * h > (long)height * w) h = (int)((long)w * height / width);
            else w = (int)((long)h * width / height);
        }
        setMeasuredDimension(w, h);
    }
}
