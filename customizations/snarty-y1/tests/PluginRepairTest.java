package org.rockbox;
import java.io.*;import java.nio.file.*;import java.util.zip.*;
public class PluginRepairTest{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args)throws Exception{
 File root=Files.createTempDirectory("plugin-repair-").toFile(),cache=new File(root,"private");
 try{PluginCache.prepare(cache,new File(root,"missing.rock"));throw new AssertionError();}catch(IOException expected){}
 byte[] elf=new byte[128];elf[0]=127;elf[1]='E';elf[2]='L';elf[3]='F';elf[4]=1;elf[5]=1;elf[16]=3;elf[18]=40;
 File source=new File(root,"lyric.rock");Files.write(source.toPath(),elf);File first=PluginCache.prepare(cache,source);check(first.canExecute()&&first.isFile());check(PluginCache.prepare(cache,source).equals(first));check(java.util.Arrays.equals(Files.readAllBytes(first.toPath()),elf));
 Files.write(first.toPath(),new byte[]{4});check(PluginCache.prepare(cache,source).length()==elf.length);
 elf[127]=1;Files.write(source.toPath(),elf);check(!PluginCache.prepare(cache,source).equals(first));elf[18]=3;Files.write(source.toPath(),elf);try{PluginCache.prepare(cache,source);throw new AssertionError();}catch(IOException expected){}
 File archive=new File(root,"assets.zip");try(ZipOutputStream z=new ZipOutputStream(new FileOutputStream(archive))){for(String name:new String[]{"sdcard/.rockbox/rocks/apps/lrcplayer.rock","sdcard/.rockbox/rocks/games/game.rock","sdcard/.rockbox/rocks/demos/demo.rock","sdcard/.rockbox/rocks/viewers/view.rock","sdcard/.rockbox/rocks.data/test.dat"}){z.putNextEntry(new ZipEntry(name));z.write(new byte[]{1,2,3});z.closeEntry();}}
 File rb=new File(root,"sd/.rockbox"),old=new File(rb,"rocks/apps/lrcplayer.rock"),data=new File(rb,"rocks.data/test.dat");old.getParentFile().mkdirs();Files.write(old.toPath(),new byte[]{9});data.getParentFile().mkdirs();Files.write(data.toPath(),new byte[]{8});PairedPlugins.install(archive,rb);check(old.length()==3);check(new File(old+".before-plugins15").isFile());check(Files.readAllBytes(data.toPath())[0]==8);Files.write(old.toPath(),new byte[]{7});PairedPlugins.install(archive,rb);check(Files.readAllBytes(old.toPath())[0]==7);
 System.out.println("PASS: actual cache ELF/ARM checks, byte identity, executable staging, unchanged reuse, changed refresh; full category install, original backup, resource preservation and restart/once-only behavior");
 }
}
