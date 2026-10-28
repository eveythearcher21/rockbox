from pathlib import Path
import subprocess
r=Path('/tmp/snarty7-async-test');r.mkdir(exist_ok=True)
files={
'android/content/Context.java':'package android.content; public class Context {}',
'android/net/Uri.java':'package android.net; public class Uri {}',
'android/os/Looper.java':'package android.os; public class Looper { public static Looper getMainLooper(){return new Looper();}}',
'android/os/Handler.java':'''package android.os; public class Handler { public Handler(Looper l){} public boolean post(Runnable r){ synchronized(queue){queue.add(r);} return true;} static java.util.List<Runnable> queue=new java.util.ArrayList<Runnable>(); public static void drain(){while(true){Runnable r; synchronized(queue){if(queue.isEmpty())return;r=queue.remove(0);}r.run();}}}''',
'android/view/SurfaceHolder.java':'''package android.view; public interface SurfaceHolder {interface Callback{void surfaceCreated(SurfaceHolder h);void surfaceChanged(SurfaceHolder h,int f,int w,int t);void surfaceDestroyed(SurfaceHolder h);} void addCallback(Callback c);}''',
'android/view/SurfaceView.java':'''package android.view; public class SurfaceView {android.content.Context c; public SurfaceView(android.content.Context x){c=x;} public android.content.Context getContext(){return c;} public SurfaceHolder getHolder(){return new SurfaceHolder(){public void addCallback(SurfaceHolder.Callback c){}};} public void requestLayout(){} protected void onMeasure(int a,int b){} protected int getDefaultSize(int a,int b){return b;} protected void setMeasuredDimension(int w,int h){} }''',
'android/media/AudioManager.java':'package android.media; public class AudioManager {public static final int STREAM_MUSIC=3;}',
'android/util/Log.java':'package android.util; public class Log {public static int e(String t,String s,Throwable e){return 0;}}',
'android/media/MediaPlayer.java':'''package android.media;
public class MediaPlayer {
 public static volatile boolean blockOpen, unblock, throwSeek; public static volatile int opens,releases; public static volatile MediaPlayer latest; public static Thread ui;
 public interface OnPreparedListener{void onPrepared(MediaPlayer m);} public interface OnErrorListener{boolean onError(MediaPlayer m,int w,int e);} public interface OnCompletionListener{void onCompletion(MediaPlayer m);}
 public static class TrackInfo{public static final int MEDIA_TRACK_TYPE_VIDEO=1;public int getTrackType(){return 1;}}
 OnPreparedListener prepared; OnErrorListener error; OnCompletionListener complete;
 void check(){if(Thread.currentThread()==ui)throw new AssertionError("Decoder call on UI thread");}
 public MediaPlayer(){check();latest=this;}
 public void setOnPreparedListener(OnPreparedListener l){check();prepared=l;} public void setOnErrorListener(OnErrorListener l){check();error=l;} public void setOnCompletionListener(OnCompletionListener l){check();complete=l;}
 public void setAudioStreamType(int n){check();} public void setDisplay(android.view.SurfaceHolder h){check();}
 public void setDataSource(android.content.Context c,android.net.Uri u){check();opens++;while(blockOpen&&!unblock){try{Thread.sleep(5);}catch(Exception e){}}}
 public void prepareAsync(){check();prepared.onPrepared(this);} public int getDuration(){check();return 20000;} public int getVideoWidth(){check();return 320;}public int getVideoHeight(){check();return 240;} public TrackInfo[] getTrackInfo(){check();return new TrackInfo[]{new TrackInfo()};}
 public void start(){check();}public void pause(){check();}public void seekTo(int n){check();if(throwSeek)throw new IllegalStateException();}public int getCurrentPosition(){check();return 5000;}public boolean isPlaying(){check();return true;}public void reset(){check();}public void release(){check();releases++;}
 public void lateComplete(){complete.onCompletion(this);}
}''',
'org/rockbox/AsyncVideoViewTest.java':'''package org.rockbox;
import android.media.MediaPlayer;import android.os.Handler;
public class AsyncVideoViewTest {
 static void check(boolean b){if(!b)throw new AssertionError();} static void waitFor(java.util.concurrent.Callable<Boolean> done)throws Exception{long end=System.currentTimeMillis()+3000;while(!done.call()){Handler.drain();if(System.currentTimeMillis()>end)throw new AssertionError("timeout");Thread.sleep(5);}Handler.drain();}
 public static void main(String[] args)throws Exception{
 MediaPlayer.ui=Thread.currentThread(); final int[] prepared={0},errors={0},completed={0};
 AsyncVideoView view=new AsyncVideoView(new android.content.Context());view.setOnPreparedListener(new MediaPlayer.OnPreparedListener(){public void onPrepared(MediaPlayer p){prepared[0]++;}});view.setOnErrorListener(new MediaPlayer.OnErrorListener(){public boolean onError(MediaPlayer p,int w,int e){errors[0]++;return true;}});view.setOnCompletionListener(new MediaPlayer.OnCompletionListener(){public void onCompletion(MediaPlayer p){completed[0]++;}});
 view.surfaceCreated(view.getHolder());view.setVideoURI(new android.net.Uri());waitFor(()->prepared[0]==1);check(view.hasVideoTrack()&&view.getDuration()==20000);
 view.start();view.pause();view.seekTo(1000);view.poll();waitFor(()->view.getCurrentPosition()==5000);
 MediaPlayer.throwSeek=true;view.seekTo(2000);waitFor(()->errors[0]==1);MediaPlayer.throwSeek=false;
 MediaPlayer old=MediaPlayer.latest;view.stopPlayback();old.lateComplete();Handler.drain();check(completed[0]==0);
 MediaPlayer.blockOpen=true;view.setVideoURI(new android.net.Uri());waitFor(()->MediaPlayer.opens==2);
 long before=System.nanoTime();for(int i=0;i<100;i++)view.poll();view.stopPlayback();view.close();check(System.nanoTime()-before<200000000);MediaPlayer.unblock=true;waitFor(()->MediaPlayer.releases>=2);check(prepared[0]==1);
 System.out.println("PASS: decoder calls off UI, cached metadata, seek error, stale completion suppression, bounded polling, nonblocking close during stalled open");
 }
}'''}
for name,body in files.items():p=r/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
src=Path(__file__).resolve().parents[3]/'android/y1/src/org/rockbox/AsyncVideoView.java';subprocess.run(['/workspace/setup/sysroot/usr/lib/jvm/java-17-openjdk-amd64/bin/javac','-d',str(r/'classes'),*[str(r/n) for n in files],str(src)],check=True);subprocess.run(['/workspace/setup/sysroot/usr/lib/jvm/java-17-openjdk-amd64/bin/java','-cp',str(r/'classes'),'org.rockbox.AsyncVideoViewTest'],check=True)
