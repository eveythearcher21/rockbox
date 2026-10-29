/* Rockbox GPLv2 or later. Shared local-file policy for the video launcher/UI. */
package org.rockbox;
import java.io.File;
import java.io.IOException;
import java.util.Locale;
public final class VideoFiles {
    private VideoFiles() { }
    public static File resolve(File root, String path) throws IOException {
        if (path == null) throw new IOException("Missing video path");
        File file = new File(path).getCanonicalFile();
        String prefix = root.getCanonicalPath() + File.separator;
        if (!file.isFile() || !file.getPath().startsWith(prefix) ||
            !file.getName().toLowerCase(Locale.US).endsWith(".mp4"))
            throw new IOException("Not a local MP4 in Videos");
        return file;
    }
}
