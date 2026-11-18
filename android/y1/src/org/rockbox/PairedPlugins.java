/* Install the complete matching plugin set without replacing user data. GPLv2+. */
package org.rockbox;
import java.io.*;
import java.util.*;
import java.util.zip.*;
final class PairedPlugins {
 static void install(File archive,File root)throws IOException{
  File marker=new File(root,".snarty-plugins-fixed15");if(marker.isFile())return;
  ZipFile zip=new ZipFile(archive);
  try{Enumeration<? extends ZipEntry> entries=zip.entries();
   while(entries.hasMoreElements()){
    ZipEntry entry=entries.nextElement();String name=entry.getName(),prefix="sdcard/.rockbox/";
    if(entry.isDirectory()||!name.startsWith(prefix))continue;
    String relative=name.substring(prefix.length());
    if(!(relative.startsWith("rocks/")||relative.startsWith("rocks.data/")))continue;
    File target=new File(root,relative);
    if(!target.getCanonicalPath().startsWith(root.getCanonicalPath()+File.separator)||relative.contains(".."))throw new IOException("Unsafe plugin archive path");
    boolean binary=relative.endsWith(".rock")||relative.endsWith(".ovl");
    if(target.exists()&&!binary)continue;
    if(!target.getParentFile().isDirectory()&&!target.getParentFile().mkdirs())throw new IOException("Cannot create plugin directory");
    if(target.isFile()&&binary){File backup=new File(target.getPath()+".before-plugins15");if(!backup.exists()){copy(new FileInputStream(target),backup);}}
    File temp=new File(target.getPath()+".paired-tmp");copy(zip.getInputStream(entry),temp);
    if(!temp.renameTo(target))throw new IOException("Cannot install matching plugin: "+relative);
   }
   File temp=new File(marker.getPath()+".tmp");copy(new ByteArrayInputStream(new byte[]{1}),temp);if(!temp.renameTo(marker))throw new IOException("Cannot save plugin marker");
  }finally{zip.close();}
 }
 static void copy(InputStream in,File destination)throws IOException{
  FileOutputStream out=new FileOutputStream(destination);try{byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);out.getFD().sync();}finally{try{in.close();}finally{out.close();}}
 }
}
