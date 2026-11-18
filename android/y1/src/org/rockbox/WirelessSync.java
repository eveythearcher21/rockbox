/* SNARTY paired computer to Y1 library transfer. GPLv2 or later. */
package org.rockbox;

import java.io.*;
import java.net.*;
import java.security.*;
import java.util.*;
import org.json.*;

/** Streaming, authenticated and non-destructive. Runs only on the worker thread. */
public final class WirelessSync {
    public interface Host {
        boolean ready();
        void progress(String text);
        void changed();
    }
    public static class SourceBusy extends IOException {
        public SourceBusy() { super("Syncer is preparing the source library; will retry"); }
    }
    private final File root;
    private final URI endpoint;
    private final byte[] key;
    private final Host host;
    private final SecureRandom random=new SecureRandom();
    private static final long MAX_FILE=2L*1024*1024*1024;
    private static final int MAX_MANIFEST=8*1024*1024;
    public WirelessSync(File storage,String address,String secret,Host callback) throws IOException {
        root=storage.getCanonicalFile();endpoint=WirelessProtocol.endpoint(address);
        key=WirelessProtocol.key(secret);host=callback;
    }
    private void check() throws IOException {
        if (Thread.currentThread().isInterrupted() || !host.ready())
            throw new IOException("Sync paused: Wi-Fi or mounted storage unavailable");
    }
    private File privateFile(File file) throws IOException {
        File canonical=file.getCanonicalFile();
        if(!canonical.equals(file.getAbsoluteFile()) ||
           !canonical.getPath().startsWith(root.getPath()+File.separator))
            throw new IOException("Unsafe sync state/staging path");
        return canonical;
    }
    private HttpURLConnection connect(String path, String nonce) throws IOException {
        check();
        HttpURLConnection connection=(HttpURLConnection)new URL(endpoint.toString()+path).openConnection();
        connection.setInstanceFollowRedirects(false);connection.setConnectTimeout(10000);
        connection.setReadTimeout(30000);connection.setUseCaches(false);
        connection.setRequestProperty("X-Snarty-Nonce",nonce);
        connection.setRequestProperty("X-Snarty-Auth",WirelessProtocol.hmac(key,
            ("GET\n"+path+"\n"+nonce).getBytes("UTF-8")));
        return connection;
    }
    private String nonce() { byte[] n=new byte[16];random.nextBytes(n);return WirelessProtocol.hex(n); }
    private byte[] manifest() throws IOException {
        String nonce=nonce();HttpURLConnection c=connect("/v1/manifest",nonce);
        try {
            int status=c.getResponseCode();
            if (status==202) throw new SourceBusy();
            if (status!=200) throw new IOException("Syncer response "+status+"; check pairing/source on computer");
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            InputStream in=c.getInputStream();byte[] buffer=new byte[8192];int n;
            try { while ((n=in.read(buffer))!=-1) {check();
                if (bytes.size()+n>MAX_MANIFEST) throw new IOException("Sync manifest too large");
                bytes.write(buffer,0,n);
            }} finally { in.close(); }
            byte[] body=bytes.toByteArray(),prefix=(nonce+"\n").getBytes("UTF-8");
            ByteArrayOutputStream signed=new ByteArrayOutputStream();signed.write(prefix);signed.write(body);
            if (!WirelessProtocol.equal(c.getHeaderField("X-Snarty-Auth"),
                WirelessProtocol.hmac(key,signed.toByteArray()))) throw new IOException("Sync manifest authentication failed");
            return body;
        } finally { c.disconnect(); }
    }
    private String hash(File file) throws IOException {
        try {
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            InputStream in=new FileInputStream(file);byte[] buffer=new byte[65536];int n;
            try { while ((n=in.read(buffer))!=-1) {check();digest.update(buffer,0,n);} }
            finally { in.close(); }
            return WirelessProtocol.hex(digest.digest());
        } catch (NoSuchAlgorithmException e) { throw new IOException(e); }
    }
    private static final class Entry {
        String path,sha;long size;File target,stage;boolean changed;int index;
    }
    private void download(Entry e, File stageRoot) throws IOException {
        e.stage=privateFile(new File(stageRoot,e.sha+"-"+e.index+".part"));
        if (e.stage.isFile() && e.stage.length()==e.size && hash(e.stage).equals(e.sha)) return;
        if (root.getUsableSpace()<e.size+4*1024*1024) throw new IOException("Not enough space for library sync");
        HttpURLConnection c=connect("/v1/file/"+e.sha,nonce());
        try {
            if (c.getResponseCode()!=200) throw new IOException("Download failed; retry when Syncer is ready");
            InputStream in=c.getInputStream();
            FileOutputStream out=new FileOutputStream(e.stage);byte[] buffer=new byte[65536];long size=0;int n;
            try { while ((n=in.read(buffer))!=-1) {
                check();size+=n;if (size>e.size) throw new IOException("Download size mismatch");
                out.write(buffer,0,n);
            } out.getFD().sync(); } finally { try {in.close();} finally {out.close();} }
            if (size!=e.size || !hash(e.stage).equals(e.sha)) throw new IOException("Download checksum mismatch");
        } finally { c.disconnect(); }
    }
    private static int order(Entry e) {
        return e.path.equals(".rockbox/snarty/library-v1.bin")?2:
               e.path.startsWith("Playlists/")?1:0;
    }
    private Properties ownership(File file) throws IOException {
        Properties result=new Properties();
        if (file.isFile()) {
            InputStream in=new FileInputStream(file);
            try { result.load(in); } finally {in.close();}
        }
        return result;
    }
    /** Returns number of changed files; status never claims unavailable lyrics were supplied. */
    public int run() throws IOException {
        host.progress("Checking Syncer library...");
        final JSONObject document;
        try {document=new JSONObject(new String(manifest(),"UTF-8"));}
        catch (JSONException e) {throw new IOException("Invalid Syncer manifest",e);}
        File state=privateFile(new File(root,".rockbox/snarty/wireless-owned.properties"));
        Properties owned=ownership(state);List<Entry> entries=new ArrayList<Entry>();
        Set<String> paths=new HashSet<String>();
        try {
            if (document.getInt("version")!=1) throw new IOException("Unsupported wireless sync version");
            JSONArray files=document.getJSONArray("files");
            if (files.length()>20000) throw new IOException("Too many sync files");
            for (int i=0;i<files.length();i++) {
                JSONObject item=files.getJSONObject(i);Entry e=new Entry();e.index=i;e.path=item.getString("path");
                e.target=WirelessProtocol.destination(root,e.path);e.sha=item.getString("sha256");e.size=item.getLong("size");
                if (!e.sha.matches("[a-f0-9]{64}") || e.size<1 || e.size>MAX_FILE ||
                    !paths.add(WirelessProtocol.collisionKey(e.path))) throw new IOException("Invalid/colliding sync file");
                check();boolean exists=e.target.exists();
                if(exists&&!e.target.isFile())throw new IOException("File path is a directory: "+e.path);
                String fingerprint=e.target.length()+":"+e.target.lastModified();
                String cached=owned.getProperty(e.path);
                // Unchanged files need not reread the entire music collection on every
                // connection. Before ANY replacement we still hash the old file below,
                // so even an edit that preserves size/mtime cannot be overwritten.
                String current=exists && e.target.isFile()?
                    (cached!=null && cached.matches("[a-f0-9]{64}") && fingerprint.equals(owned.getProperty("@stat:"+e.path))?cached:hash(e.target)):null;
                if (exists && !e.sha.equals(current) && !ObjectsCompat.equal(current,owned.getProperty(e.path)))
                    throw new IOException("Local file differs; resolve in Syncer first: "+e.path);
                e.changed=!e.sha.equals(current);entries.add(e);
            }
        } catch (JSONException e) {throw new IOException("Incomplete Syncer manifest",e);}
        File stageRoot=privateFile(new File(root,".rockbox/snarty/wireless-staging"));
        if (!stageRoot.isDirectory() && !stageRoot.mkdirs()) throw new IOException("Cannot create sync staging folder");
        Set<String> expectedStages=new HashSet<String>();
        for(Entry e:entries)expectedStages.add(e.sha+"-"+e.index+".part");
        File[] oldStages=stageRoot.listFiles();
        if(oldStages!=null)for(File old:oldStages){
            check();
            if(old.getName().matches("[a-f0-9]{64}-[0-9]+\\.part") && !expectedStages.contains(old.getName()))
                if(!privateFile(old).delete())throw new IOException("Cannot clean obsolete sync staging file");
        }
        int count=0;
        // Stage and verify ALL changed files before making any visible. Audio/sidecars first,
        // playlist references next, library ordering last. No deletions of local media.
        for (Entry e:entries) if (e.changed) {
            host.progress("Downloading "+(++count)+": "+e.path);download(e,stageRoot);
        }
        Collections.sort(entries,new Comparator<Entry>() {public int compare(Entry a,Entry b){return order(a)-order(b);}});
        int installed=0;
        try { for (Entry e:entries) {
            check();
            if (e.changed) {
                File checked=WirelessProtocol.destination(root,e.path);
                File parent=checked.getParentFile();
                if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("Cannot create music folder");
                // Recheck local edits made while downloads were in flight.
                if (checked.exists() && !ObjectsCompat.equal(hash(checked),owned.getProperty(e.path)))
                    throw new IOException("Local file changed during sync: "+e.path);
                if (!e.stage.renameTo(checked)) throw new IOException("Cannot publish file: "+e.path);
                installed++;
            }
            owned.setProperty(e.path,e.sha);
            owned.setProperty("@stat:"+e.path,e.target.length()+":"+e.target.lastModified());
        }} finally {
            // Identical files can be adopted after an interrupted first sync. This checkpoint
            // records only published files, and keeps older ownership for unfinished entries.
            if(host.ready()) {
                File temporary=privateFile(new File(state.getPath()+".tmp"));
                FileOutputStream out=new FileOutputStream(temporary);
                try {owned.store(out,"SNARTY wireless-owned hashes; no user files are deleted");out.getFD().sync();}
                finally {out.close();}
                check();if (!temporary.renameTo(state)) throw new IOException("Cannot save sync ownership");
            }
            if(installed>0)host.changed();
        }
        int missing=document.optInt("missing_lyrics",0), portraits=document.optInt("missing_artist_images",0);
        int gaps=document.optInt("metadata_gaps",-1);
        host.progress("Sync complete: "+installed+" files. Missing lyrics: "+missing+", portraits: "+(portraits<0?"unknown":portraits)+". Metadata gaps: "+(gaps<0?"unknown":gaps));
        return installed;
    }
    /** java.util.Objects is not available on API17. */
    private static class ObjectsCompat {static boolean equal(Object a,Object b){return a==b || a!=null&&a.equals(b);}}
}
