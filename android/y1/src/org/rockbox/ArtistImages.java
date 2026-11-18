/* Decode PNG/WebP artist sources to bounded native JPEGs without delaying core startup. GPLv2+. */
package org.rockbox;
import java.io.*;
import java.util.*;
import android.graphics.*;
import android.util.Log;
public final class ArtistImages {
 private static boolean running;
 private ArtistImages(){}
 public static synchronized void start(final File rockbox){
  if(running)return;running=true;
  Thread worker=new Thread(new Runnable(){public void run(){try{convert(rockbox);}catch(OutOfMemoryError e){Log.w("ArtistImages","Artist folder exceeds available memory",e);}
  catch(Exception e){Log.w("ArtistImages","Cannot scan artist folder",e);}finally{synchronized(ArtistImages.class){running=false;}}}},"Artist artwork");
  worker.setPriority(Thread.MIN_PRIORITY);worker.setDaemon(true);worker.start();
 }
 static void convert(File rockbox){
  File source=new File(rockbox.getParentFile(),"Artist_Images");File[] files=source.listFiles();if(files==null)return;
  Arrays.sort(files,new Comparator<File>(){public int compare(File a,File b){return a.getName().compareToIgnoreCase(b.getName());}});
  File cache=new File(rockbox,"snarty/artist-images");if(!cache.isDirectory()&&!cache.mkdirs())return;
  HashSet<String> seen=new HashSet<String>();int processed=0;
  for(File file:files){
   String name=file.getName();int dot=name.lastIndexOf('.');if(dot<1||!file.isFile())continue;
   String ext=name.substring(dot).toLowerCase(Locale.ROOT);if(!ext.equals(".png")&&!ext.equals(".webp"))continue;
   String stem=name.substring(0,dot);if(!seen.add(stem.toLowerCase(Locale.ROOT)))continue;
   if(++processed>2048)break;
   File out=new File(cache,stem+".jpg");if(out.isFile()&&out.lastModified()==file.lastModified())continue;
   Bitmap decoded=null,cropped=null;File temporary=new File(out.getPath()+".tmp");
   try{
    if(file.length()>16*1024*1024)continue;
    BitmapFactory.Options o=new BitmapFactory.Options();o.inJustDecodeBounds=true;BitmapFactory.decodeFile(file.getPath(),o);
    int w=o.outWidth,h=o.outHeight;if(w<=0||h<=0||w>32768||h>32768||(long)w*h>100000000)continue;
    o.inSampleSize=1;while(w/o.inSampleSize>1024||h/o.inSampleSize>1024)o.inSampleSize*=2;
    o.inJustDecodeBounds=false;decoded=BitmapFactory.decodeFile(file.getPath(),o);if(decoded==null)continue;
    cropped=Bitmap.createBitmap(200,200,Bitmap.Config.RGB_565);Canvas c=new Canvas(cropped);int side=Math.min(decoded.getWidth(),decoded.getHeight());int x=(decoded.getWidth()-side)/2,y=(decoded.getHeight()-side)/2;
    c.drawBitmap(decoded,new Rect(x,y,x+side,y+side),new Rect(0,0,200,200),new Paint(Paint.FILTER_BITMAP_FLAG));
    FileOutputStream stream=new FileOutputStream(temporary);try{if(!cropped.compress(Bitmap.CompressFormat.JPEG,88,stream))throw new IOException("Cannot encode portrait");stream.getFD().sync();}finally{stream.close();}
    if(!temporary.renameTo(out))throw new IOException("Cannot install portrait");out.setLastModified(file.lastModified());
   }catch(OutOfMemoryError e){Log.w("ArtistImages","Portrait exceeds available memory: "+name,e);}
   catch(Exception e){Log.w("ArtistImages","Portrait conversion failed: "+name,e);}
   finally{if(decoded!=null)decoded.recycle();if(cropped!=null)cropped.recycle();if(temporary.exists())temporary.delete();}
  }
 }
}
