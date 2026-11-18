package org.rockbox;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
public class StartupConfigTest {
    static void check(boolean result) { if (!result) throw new AssertionError(); }
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("snarty-startup-");
        Path config = root.resolve("config.cfg");
        byte[] original = "volume: -20\n# café\nidle poweroff: 3".getBytes(StandardCharsets.UTF_8);
        Files.write(config, original);
        Path pending = root.resolve("config.cfg.new");
        Files.write(pending, original);
        StartupConfig.disableIdlePoweroffOnce(root.toFile());
        check(new String(Files.readAllBytes(pending), StandardCharsets.UTF_8).endsWith("idle poweroff: 0\n"));
        byte[] updated = Files.readAllBytes(config);
        for (int i=0;i<original.length;i++) check(original[i] == updated[i]);
        check(new String(updated, StandardCharsets.UTF_8).endsWith("idle poweroff: 0\n"));
        // A later user-selected timer must survive every future startup.
        Files.write(config, "idle poweroff: 20\n".getBytes(StandardCharsets.UTF_8));
        StartupConfig.disableIdlePoweroffOnce(root.toFile());
        check(new String(Files.readAllBytes(config), StandardCharsets.UTF_8).equals("idle poweroff: 20\n"));
        Path fresh = root.resolve("fresh");StartupConfig.disableIdlePoweroffOnce(fresh.toFile());
        check(Files.exists(fresh.resolve("config.cfg")));
        Path invalid = root.resolve("not-a-directory");Files.write(invalid, new byte[]{1});
        try { StartupConfig.disableIdlePoweroffOnce(invalid.toFile());throw new AssertionError(); }
        catch (java.io.IOException expected) { }
        System.out.println("PASS: idle shutdown migration preserves config bytes, applies once, retains later user settings and reports inaccessible storage");
    }
}
