/* Rockbox GPLv2 or later. Pure timeline arithmetic shared by UI and tests. */
package org.rockbox;
import java.util.Locale;
public final class VideoTimeline {
    private VideoTimeline() { }
    public static int clamp(long position, int duration) {
        return (int)Math.max(0L, Math.min(position, Math.max(0, duration)));
    }
    public static int seek(int position, int delta, int duration) {
        return clamp((long)position + delta, duration);
    }
    public static String time(int milliseconds) {
        long seconds = Math.max(0, milliseconds) / 1000L;
        if (seconds >= 3600)
            return String.format(Locale.US, "%d:%02d:%02d", seconds / 3600,
                                 (seconds / 60) % 60, seconds % 60);
        return String.format(Locale.US, "%d:%02d", seconds / 60, seconds % 60);
    }
}
