package org.rockbox;
import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.zip.*;
public class PairedAssetsTest {
 static void check(boolean x){if(!x)throw new AssertionError();}
 static void entry(ZipOutputStream z,String name,String text)throws Exception {z.putNextEntry(new ZipEntry("sdcard/.rockbox/"+name));z.write(text.getBytes("UTF-8"));z.closeEntry();}
 static File archive(Path root,String extra)throws Exception {
  Path p=root.resolve("assets.zip");ZipOutputStream z=new ZipOutputStream(Files.newOutputStream(p));
  entry(z,"snarty-playback-v12-assets.txt","wps/SNARTY-Y1.wps\nwps/SNARTY-Y1.sbs\nrocks/apps/lrcplayer.rock\n"+extra);
  entry(z,"wps/SNARTY-Y1.wps","new-wps");entry(z,"wps/SNARTY-Y1.sbs","new-sbs");entry(z,"rocks/apps/lrcplayer.rock","new-lyrics");z.close();return p.toFile();
 }
 public static void main(String[] a)throws Exception {
  Path r=Files.createTempDirectory("snarty-assets-");File zip=archive(r,"");Path card=r.resolve("card");Files.createDirectories(card.resolve("wps"));
  Files.write(card.resolve("config.cfg"),"volume: -20\nshuffle: on".getBytes("UTF-8"));Files.write(card.resolve("config.cfg.new"),"volume: -21".getBytes("UTF-8"));Files.write(card.resolve("wps/SNARTY-Y1.wps"),"old-wps".getBytes("UTF-8"));
  PairedAssets.install(zip,card.toFile());
  check(new String(Files.readAllBytes(card.resolve("wps/SNARTY-Y1.wps")),"UTF-8").equals("new-wps"));
  check(new String(Files.readAllBytes(card.resolve("wps/SNARTY-Y1.wps.before-snarty12")),"UTF-8").equals("old-wps"));
  String config=new String(Files.readAllBytes(card.resolve("config.cfg")),"UTF-8");check(config.startsWith("volume: -20\nshuffle: on"));check(config.contains("wps: SNARTY-Y1.wps"));
  check(new String(Files.readAllBytes(card.resolve("config.cfg.before-snarty12")),"UTF-8").equals("volume: -20\nshuffle: on"));
  check(new String(Files.readAllBytes(card.resolve("config.cfg.new")),"UTF-8").startsWith("volume: -21"));
  // Future user changes survive startup. A partially completed marker is repaired.
  Files.write(card.resolve("config.cfg"),"volume: -30".getBytes("UTF-8"));PairedAssets.install(zip,card.toFile());check(Files.size(card.resolve("config.cfg"))==11);
  Files.write(card.resolve(".snarty-playback-v12"),new byte[0]);PairedAssets.install(zip,card.toFile());check(Files.size(card.resolve(".snarty-playback-v12"))==1);
  for(String bad:new String[]{"../outside\n","/absolute\n","config.cfg\n","wps/missing.wps\n","wps/SNARTY-Y1.wps\n"}) {
   File malformed=archive(r,bad);Path clean=Files.createTempDirectory(r,"bad-");
   try{PairedAssets.install(malformed,clean.toFile());throw new AssertionError(bad);}catch(IOException expected){}
   check(!Files.exists(clean.resolve("wps/SNARTY-Y1.wps")));check(!Files.exists(clean.resolve(".snarty-playback-v12")));
  }
  System.out.println("PASS: paired asset migration, original backups, preserved config bytes/pending settings, once-only behavior, corrupt-marker recovery and preflight path/manifest rejection");
 }
}
