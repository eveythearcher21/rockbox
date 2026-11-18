/* User-cropped idle artwork, bounded to the Y1 LCD. GPLv2+. */
package org.rockbox;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.os.SystemClock;
import java.io.File;
final class SnartyScreensaver {
    private volatile long touched=SystemClock.uptimeMillis();
    private volatile Bitmap image;
    private long checked,modified;
    private final String path;
    SnartyScreensaver(){this("/sdcard/.rockbox/snarty/screensaver.jpg");}
    SnartyScreensaver(String file){path=file;}
    boolean visible(){return image!=null&&SystemClock.uptimeMillis()-touched>=60000;}
    boolean touch(){boolean was=visible();touched=SystemClock.uptimeMillis();return was;}
    void refresh(){
        long now=SystemClock.uptimeMillis();if(now-checked<5000)return;checked=now;
        File f=new File(path);long stamp=f.isFile()?f.lastModified():0;
        if(stamp==modified)return;modified=stamp;
        Bitmap next=null;
        if(stamp!=0&&f.length()<=2*1024*1024){
            BitmapFactory.Options options=new BitmapFactory.Options();options.inJustDecodeBounds=true;
            BitmapFactory.decodeFile(path,options);
            if(options.outWidth==480&&options.outHeight==360){options.inJustDecodeBounds=false;next=BitmapFactory.decodeFile(path,options);}
        }
        // UI thread refresh; rendering and replacement synchronize through draw().
        synchronized(this){Bitmap old=image;image=next;if(old!=null)old.recycle();}
    }
    synchronized boolean draw(Canvas c){
        if(!visible())return false;
        c.drawBitmap(image,null,new Rect(0,0,c.getWidth(),c.getHeight()),null);return true;
    }
    synchronized void close(){modified=0;checked=0;if(image!=null){image.recycle();image=null;}}
}
