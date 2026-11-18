/* Y1 ELF plugin staging on an executable application-owned filesystem. GPLv2+. */
package org.rockbox;
import java.io.*;
import java.security.*;
public final class PluginCache {
 public static synchronized File prepare(File directory,File source)throws Exception {
  if(!source.isFile() || source.length()<52 || source.length()>32*1024*1024)throw new IOException("Missing or invalid plugin: "+source.getName());
  if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("Cannot create executable plugin cache");
  File temporary=File.createTempFile("plugin-",".tmp",directory);
  try {
   MessageDigest digest=MessageDigest.getInstance("SHA-256");
   FileInputStream in=new FileInputStream(source);FileOutputStream out=new FileOutputStream(temporary);
   byte[] b=new byte[65536];int n;long size=0;
   try {while((n=in.read(b))!=-1){if(size==0){if(n<52||b[0]!=127||b[1]!='E'||b[2]!='L'||b[3]!='F'||b[4]!=1||b[5]!=1||b[16]!=3||b[17]!=0||b[18]!=40||b[19]!=0)throw new IOException("Plugin must be a 32-bit ARM shared ELF");}size+=n;if(size>32*1024*1024)throw new IOException("Plugin too large");digest.update(b,0,n);out.write(b,0,n);}out.getFD().sync();}
   finally{try{in.close();}finally{out.close();}}
   StringBuilder key=new StringBuilder();for(byte x:digest.digest())key.append(String.format(java.util.Locale.US,"%02x",x&255));
   File target=new File(directory,key+".rock");
   if(!target.isFile() || !hash(target).equals(key.toString())) {if(!temporary.setReadable(true,true)||!temporary.setExecutable(true,true)||!temporary.renameTo(target))throw new IOException("Cannot publish executable plugin cache");}
   return target;
  }finally{temporary.delete();}
 }
 private static String hash(File file)throws Exception {
  MessageDigest digest=MessageDigest.getInstance("SHA-256");FileInputStream in=new FileInputStream(file);
  try{byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1)digest.update(buffer,0,n);}finally{in.close();}
  StringBuilder value=new StringBuilder();for(byte b:digest.digest())value.append(String.format(java.util.Locale.US,"%02x",b&255));return value.toString();
 }
 private PluginCache(){}
}
