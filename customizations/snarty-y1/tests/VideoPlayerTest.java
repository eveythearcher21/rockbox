/* Host-side policy/timeline tests; this does not emulate Android decoding. */
package org.rockbox;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
public final class VideoPlayerTest {
    private static void check(boolean ok) { if (!ok) throw new AssertionError(); }
    private static void rejects(File root, String path) throws Exception {
        try { VideoFiles.resolve(root, path);throw new AssertionError("Accepted " + path); }
        catch (IOException expected) { }
    }
    public static void main(String[] args) throws Exception {
        Path temp = Files.createTempDirectory("snarty-video-policy-");
        Path root = Files.createDirectory(temp.resolve("Videos"));
        Path nested = Files.createDirectory(root.resolve("Nested"));
        Path video = Files.write(nested.resolve("A quote's & emoji \uD83C\uDFF9.MP4"), new byte[]{1});
        check(VideoFiles.resolve(root.toFile(),video.toString()).equals(video.toFile()));
        Path alias = Files.createSymbolicLink(temp.resolve("card-alias"), root);
        check(VideoFiles.resolve(alias.toFile(), alias.resolve("Nested").resolve(video.getFileName()).toString()).equals(video.toFile()));
        Path outside = Files.write(temp.resolve("outside.mp4"),new byte[]{1});
        Path escape = Files.createSymbolicLink(root.resolve("escape.mp4"),outside);
        rejects(root.toFile(),escape.toString());
        rejects(root.toFile(),root.resolve("../outside.mp4").toString());
        Path prefix = Files.createDirectory(temp.resolve("Videos-other"));
        rejects(root.toFile(),Files.write(prefix.resolve("clip.mp4"),new byte[]{1}).toString());
        rejects(root.toFile(),Files.write(root.resolve("audio.mp3"),new byte[]{1}).toString());
        rejects(root.toFile(),root.resolve("missing.mp4").toString());
        rejects(root.toFile(),nested.toString());rejects(root.toFile(),null);
        check(VideoTimeline.seek(12000,-10000,60000)==2000);
        check(VideoTimeline.seek(2000,-10000,60000)==0);
        check(VideoTimeline.seek(59000,10000,60000)==60000);
        check(VideoTimeline.seek(Integer.MAX_VALUE,10000,Integer.MAX_VALUE)==Integer.MAX_VALUE);
        check(VideoTimeline.clamp(100,0)==0);
        check(VideoTimeline.clamp(-1,1000)==0);
        check(VideoTimeline.time(0).equals("0:00"));
        check(VideoTimeline.time(-1).equals("0:00"));
        check(VideoTimeline.time(65000).equals("1:05"));
        check(VideoTimeline.time(3661000).equals("1:01:01"));
        System.out.println("PASS: local MP4/Unicode/canonical-root policy, symlink escapes, seek bounds/overflow, time display");
        Files.delete(alias);Files.delete(escape);Files.delete(video);Files.delete(nested);
        Files.delete(root.resolve("audio.mp3"));Files.delete(root);Files.delete(outside);
        Files.delete(prefix.resolve("clip.mp4"));Files.delete(prefix);Files.delete(temp);
    }
}
