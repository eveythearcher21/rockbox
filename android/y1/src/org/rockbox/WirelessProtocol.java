/* SNARTY authenticated local-network sync. GPLv2 or later. */
package org.rockbox;

import java.io.File;
import java.io.IOException;
import java.net.InetAddress;
import java.net.URI;
import java.security.MessageDigest;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.text.Normalizer;
import java.util.Locale;

/** Shared wire rules; no Android dependencies or Google credentials. */
public final class WirelessProtocol {
    public static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) result.append(String.format(Locale.US, "%02x", b & 255));
        return result.toString();
    }
    public static byte[] key(String value) throws IOException {
        if (value == null || !value.matches("[a-fA-F0-9]{64}"))
            throw new IOException("Pairing key must contain 64 hexadecimal characters");
        byte[] bytes = new byte[32];
        for (int i=0;i<32;i++) bytes[i]=(byte)Integer.parseInt(value.substring(i*2,i*2+2),16);
        return bytes;
    }
    public static String hmac(byte[] key, byte[] value) throws IOException {
        try {
            Mac mac=Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(key,"HmacSHA256"));return hex(mac.doFinal(value));
        } catch (Exception e) { throw new IOException("Cannot authenticate sync",e); }
    }
    public static boolean equal(String first, String second) throws IOException {
        return first!=null && second!=null && MessageDigest.isEqual(
            first.getBytes("UTF-8"),second.getBytes("UTF-8"));
    }
    public static URI endpoint(String text) throws IOException {
        try {
            URI uri=new URI(text);
            if (!"http".equals(uri.getScheme()) || uri.getHost()==null ||
                uri.getUserInfo()!=null || uri.getQuery()!=null || uri.getFragment()!=null ||
                !(uri.getPath().isEmpty() || uri.getPath().equals("/")) ||
                uri.getPort()<1 || uri.getPort()>65535)
                throw new IOException("Use http://YOUR-COMPUTER-IP:8787 on your home Wi-Fi");
            // Numeric private IPv4 only: no DNS rebinding, redirects or public Internet endpoint.
            if (!uri.getHost().matches("[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+"))
                throw new IOException("Use the computer's numeric local IPv4 address");
            InetAddress address=InetAddress.getByName(uri.getHost());
            if (!(address.isSiteLocalAddress() || address.isLoopbackAddress()))
                throw new IOException("Sync is restricted to a private home network");
            return new URI("http",null,address.getHostAddress(),uri.getPort(),null,null,null);
        } catch (IOException e) { throw e; }
          catch (Exception e) { throw new IOException("Invalid Syncer address",e); }
    }
    public static String collisionKey(String path) {
        return Normalizer.normalize(path,Normalizer.Form.NFC).toLowerCase(Locale.ROOT);
    }
    public static File destination(File root, String path) throws IOException {
        if (path==null || path.getBytes("UTF-8").length>239 || path.startsWith("/") ||
            path.indexOf('\\')>=0 || path.matches(".*[\\x00-\\x1f\\x7f:*?\"<>|].*"))
            throw new IOException("Invalid sync path");
        String[] parts=path.split("/",-1);
        for (String part:parts)
            if (part.isEmpty() || part.equals(".") || part.equals("..") ||
                part.endsWith(".") || part.endsWith(" ")) throw new IOException("Unsafe sync path");
        String lower=path.toLowerCase(Locale.ROOT);
        boolean allowed=(path.startsWith("Music/") &&
            lower.matches(".*\\.(mp3|flac|m4a|ogg|opus|wav|lrc|lrc8|txt|jpg|jpeg|bmp|radio\\.m3u8|lyrics\\.meta\\.json)$")) ||
            (path.startsWith("Artist_Images/") && parts.length==2 &&
             lower.matches(".*\\.(jpg|jpeg|bmp|png|webp)$")) ||
            (path.startsWith("Playlists/") && lower.matches(".*\\.m3u8?$")) ||
            path.equals(".rockbox/snarty/library-v1.bin");
        if (!allowed) throw new IOException("Path is outside managed music/art/playlists");
        File base=root.getCanonicalFile(),file=new File(base,path).getCanonicalFile();
        if (!file.getPath().startsWith(base.getPath()+File.separator))
            throw new IOException("Sync path escapes storage");
        if(!file.equals(new File(base,path).getAbsoluteFile()))
            throw new IOException("Symlinked sync paths are not supported");
        return file;
    }
    private WirelessProtocol() { }
}
