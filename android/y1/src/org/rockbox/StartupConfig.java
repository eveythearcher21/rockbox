/* Rockbox GPLv2 or later. One-time preference migration requested by the owner. */
package org.rockbox;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
public final class StartupConfig {
    private StartupConfig() { }
    public static void disableIdlePoweroffOnce(File directory) throws IOException {
        File marker = new File(directory, ".snarty-always-ready-v1");
        if (marker.exists()) return;
        if (!directory.isDirectory() && !directory.mkdirs()) throw new IOException("No settings directory");
        // Preserve existing config bytes. Rockbox's text loader uses the last value.
        append(new File(directory, "config.cfg"));
        // Some builds promote the pending settings file at the next native boot.
        File pending = new File(directory, "config.cfg.new");
        if (pending.exists()) append(pending);
        FileOutputStream output = new FileOutputStream(marker);
        try { output.write(1);output.getFD().sync(); } finally { output.close(); }
    }
    private static void append(File config) throws IOException {
        FileOutputStream output = new FileOutputStream(config, true);
        try {
            output.write("\n# SNARTY: remain on while idle (change later in Settings if desired)\nidle poweroff: 0\n".getBytes("UTF-8"));
            output.getFD().sync();
        } finally { output.close(); }
    }
}
