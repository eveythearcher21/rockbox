/* Install paired playback assets once on the mounted card, with backups. GPLv2+. */
package org.rockbox;
import java.io.*;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.zip.ZipFile;
import java.util.zip.ZipEntry;
public final class PairedAssets {
    private PairedAssets() { }
    private static final String PREFIX="sdcard/.rockbox/";
    private static final String MARKER="# SNARTY playback layout v12";
    private static final String THEME="\n"+MARKER+"\nwps: SNARTY-Y1.wps\nsbs: SNARTY-Y1.sbs\nfont: 22-KodeMono-SemiBold.fnt\nbackground color: 232234\nforeground color: a2accd\niconset: SNARTY.bmp\nviewers iconset: SNARTY_viewer.bmp\nscrollbar: off\n";
    private static void copy(InputStream input,File destination) throws IOException {
        File parent=destination.getParentFile();
        if(!parent.isDirectory()&&!parent.mkdirs())throw new IOException("Cannot create "+parent);
        FileOutputStream output=new FileOutputStream(destination);
        try {byte[] data=new byte[8192];int count;long total=0;while((count=input.read(data))!=-1){total+=count;if(total>8*1024*1024)throw new IOException("Asset too large");output.write(data,0,count);}output.getFD().sync();}
        finally {output.close();}
    }
    private static void backup(File file) throws IOException {
        File saved=new File(file.getPath()+".before-snarty12");
        if(file.isFile()&&!saved.exists()) {
            FileInputStream input=new FileInputStream(file);File temporary=new File(saved.getPath()+".tmp");
            try {copy(input,temporary);} finally {input.close();}
            if(!temporary.renameTo(saved))throw new IOException("Cannot preserve "+file);
        }
    }
    private static void configure(File config) throws IOException {
        if(config.exists()) {
            BufferedReader input=new BufferedReader(new InputStreamReader(new FileInputStream(config),"UTF-8"));
            try {String line;while((line=input.readLine())!=null)if(line.equals(MARKER))return;} finally {input.close();}
        }
        backup(config);File temporary=new File(config.getPath()+".snarty-tmp");
        if(config.exists()) {FileInputStream input=new FileInputStream(config);try {copy(input,temporary);} finally {input.close();}}
        FileOutputStream output=new FileOutputStream(temporary,config.exists());
        try {output.write(THEME.getBytes("UTF-8"));output.getFD().sync();} finally {output.close();}
        if(!temporary.renameTo(config))throw new IOException("Cannot update theme settings");
    }
    public static void install(File archive,File root) throws IOException {
        File marker=new File(root,".snarty-playback-v12");
        if(marker.isFile()&&marker.length()==1) {FileInputStream in=new FileInputStream(marker);try {if(in.read()==12)return;} finally {in.close();}}
        if(!root.isDirectory()&&!root.mkdirs())throw new IOException("No Rockbox settings folder");
        ZipFile zip=new ZipFile(archive);
        try {
            ZipEntry manifest=zip.getEntry(PREFIX+"snarty-playback-v12-assets.txt");
            if(manifest==null)throw new IOException("Paired playback asset manifest missing");
            BufferedReader lines=new BufferedReader(new InputStreamReader(zip.getInputStream(manifest),"UTF-8"));
            ArrayList<String> names=new ArrayList<String>();HashSet<String> seen=new HashSet<String>();
            boolean lyrics=false,wps=false,sbs=false;String base=root.getCanonicalPath()+File.separator;
            try {
                String name;
                while((name=lines.readLine())!=null) {
                    if(name.length()==0)continue;
                    if(names.size()>=256 || name.length()>250 || name.startsWith("/") || name.indexOf('\\')>=0 || name.indexOf("..")>=0 || !seen.add(name) ||
                       !(name.startsWith("fonts/")||name.startsWith("wps/")||name.startsWith("icons/")||name.startsWith("themes/")||name.equals("rocks/apps/lrcplayer.rock")))
                        throw new IOException("Invalid playback asset path");
                    File target=new File(root,name).getCanonicalFile();
                    if(!target.getPath().startsWith(base))throw new IOException("Asset outside Rockbox folder");
                    ZipEntry entry=zip.getEntry(PREFIX+name);
                    if(entry==null||entry.isDirectory()||entry.getSize()<0||entry.getSize()>8*1024*1024)throw new IOException("Paired asset missing or too large: "+name);
                    names.add(name);
                    if(name.equals("rocks/apps/lrcplayer.rock"))lyrics=true;
                    if(name.equals("wps/SNARTY-Y1.wps"))wps=true;
                    if(name.equals("wps/SNARTY-Y1.sbs"))sbs=true;
                }
            } finally {lines.close();}
            if(!lyrics||!wps||!sbs)throw new IOException("Incomplete playback asset set");
            for(String name:names) {
                File target=new File(root,name).getCanonicalFile();backup(target);
                File temporary=new File(target.getPath()+".snarty-tmp");InputStream input=zip.getInputStream(zip.getEntry(PREFIX+name));
                try {copy(input,temporary);} finally {input.close();}
                if(!temporary.renameTo(target))throw new IOException("Cannot install "+name);
            }
            configure(new File(root,"config.cfg"));
            File pending=new File(root,"config.cfg.new");if(pending.exists())configure(pending);
            File temporary=new File(marker.getPath()+".tmp");FileOutputStream output=new FileOutputStream(temporary);
            try {output.write(12);output.getFD().sync();} finally {output.close();}
            if(!temporary.renameTo(marker))throw new IOException("Cannot finish playback update");
        } finally {zip.close();}
    }
}
