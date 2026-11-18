#!/usr/bin/env python3
"""Actual idle artwork policy with recording Android bitmap/clock dependencies."""
from pathlib import Path
import tempfile,subprocess
repo=Path(__file__).resolve().parents[3];root=Path(tempfile.mkdtemp(prefix='snarty-saver-'))
files={
'android/os/SystemClock.java':'package android.os; public class SystemClock {public static long now=10000;public static long uptimeMillis(){return now;}}',
'android/graphics/Bitmap.java':'package android.graphics; public class Bitmap {public void recycle(){}}',
'android/graphics/BitmapFactory.java':'''package android.graphics; public class BitmapFactory {public static int width=480,height=360;public static class Options {public boolean inJustDecodeBounds;public int outWidth,outHeight;} public static Bitmap decodeFile(String p,Options o){o.outWidth=width;o.outHeight=height;return o.inJustDecodeBounds?null:new Bitmap();}}''',
'android/graphics/Rect.java':'package android.graphics;public class Rect{public Rect(int a,int b,int c,int d){}}',
'android/graphics/Canvas.java':'package android.graphics;public class Canvas{public int count;public int getWidth(){return 480;}public int getHeight(){return 360;}public void drawBitmap(Bitmap b,Object a,Rect r,Object p){count++;}}',
'org/rockbox/ScreensaverTest.java':'''package org.rockbox;import java.io.*;import android.os.SystemClock;import android.graphics.*;public class ScreensaverTest{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args)throws Exception{File f=File.createTempFile("saver","jpg");FileOutputStream out=new FileOutputStream(f);out.write(1);out.close();SnartyScreensaver s=new SnartyScreensaver(f.getPath());s.refresh();check(!s.visible());SystemClock.now+=60001;check(s.visible());Canvas c=new Canvas();check(s.draw(c)&&c.count==1);check(s.touch());check(!s.visible());s.close();SystemClock.now+=60001;s.refresh();check(s.visible());s.close();BitmapFactory.width=960;SystemClock.now+=60001;s.refresh();check(!s.visible());s.close();BitmapFactory.width=480;RandomAccessFile big=new RandomAccessFile(f,"rw");big.setLength(2097153);big.close();SystemClock.now+=60001;s.refresh();check(!s.visible());f.delete();s.close();SystemClock.now+=60001;s.refresh();check(!s.visible());System.out.println("PASS: actual screensaver policy accepts480x360, waits60sec, draws full-canvas, dismisses, reloads after lifecycle close, rejects wrong dimensions/oversize/missing files");}}'''}
for name,text in files.items():p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
subprocess.run(['javac','-d',str(root),*[str(root/n) for n in files],str(repo/'android/y1/src/org/rockbox/SnartyScreensaver.java')],check=True)
subprocess.run(['java','-cp',str(root),'org.rockbox.ScreensaverTest'],check=True)
