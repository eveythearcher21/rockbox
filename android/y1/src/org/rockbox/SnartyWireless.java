/* SNARTY Wi-Fi controls and background library sync. GPLv2 or later. */
package org.rockbox;

import android.content.*;
import android.net.*;
import android.net.wifi.*;
import android.os.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import org.json.*;

/** Long network/storage work never runs on Rockbox's or Android's UI thread. */
public final class SnartyWireless {
    private final RockboxService service;
    private final WifiManager wifi;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final android.content.SharedPreferences prefs;
    private final AtomicBoolean running=new AtomicBoolean(),changed=new AtomicBoolean();
    private volatile boolean stopped;
    private volatile String status="Pair the RockBlock Syncer to enable library sync";
    private volatile Thread worker;
    private volatile long lastAttempt;
    private boolean wasConnected;
    private final BroadcastReceiver receiver=new BroadcastReceiver() {
        public void onReceive(Context c,Intent i) {
            NetworkInfo n=(NetworkInfo)i.getParcelableExtra(WifiManager.EXTRA_NETWORK_INFO);
            if(n!=null&&!n.isConnected()){wasConnected=false;lastAttempt=0;}
            handler.removeCallbacks(tick);handler.postDelayed(tick,2000);
        }
    };
    public SnartyWireless(RockboxService context) {
        service=context;wifi=(WifiManager)context.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
        prefs=context.getSharedPreferences("snarty_wireless",Context.MODE_PRIVATE);
    }
    public void start() {
        IntentFilter filter=new IntentFilter(WifiManager.NETWORK_STATE_CHANGED_ACTION);
        filter.addAction(WifiManager.WIFI_STATE_CHANGED_ACTION);
        service.registerReceiver(receiver,filter);handler.post(tick);
    }
    public void stop() {
        stopped=true;handler.removeCallbacks(tick);
        try {service.unregisterReceiver(receiver);} catch (Exception ignored) { }
        Thread w=worker;if(w!=null)w.interrupt();
    }
    private boolean connected() {
        if(wifi==null || !wifi.isWifiEnabled())return false;
        ConnectivityManager c=(ConnectivityManager)service.getSystemService(Context.CONNECTIVITY_SERVICE);
        NetworkInfo n=c==null?null:c.getNetworkInfo(ConnectivityManager.TYPE_WIFI);
        return n!=null && n.isConnected();
    }
    private boolean ready() {return !stopped && connected() && service.mediaStorageReady() && service.isRockboxRunning();}
    private boolean paired() {return !prefs.getString("key","").isEmpty();}
    private final Runnable tick=new Runnable() {
        public void run() {
            if(stopped)return;
            try {
                if(service.mediaStorageReady() && !paired()) importPairing(false);
                boolean now=connected();
                if(now&&!wasConnected)lastAttempt=0;
                wasConnected=now;
                if(ready() && paired() && prefs.getBoolean("auto",true) &&
                    (lastAttempt==0 || SystemClock.elapsedRealtime()-lastAttempt>=15*60*1000)) sync();
            } catch(Exception e) {status="Wi-Fi check failed; open Wi-Fi settings";}
            handler.postDelayed(this,60000);
        }
    };
    private void sync() {
        if(!paired()) {status="Pair Syncer first (Settings > Wi-Fi)";return;}
        if(!ready()) {status="Sync needs connected Wi-Fi and mounted storage";return;}
        if(!running.compareAndSet(false,true))return;
        final String url=prefs.getString("url",""),key=prefs.getString("key","");
        lastAttempt=SystemClock.elapsedRealtime();
        worker=new Thread(new Runnable(){public void run(){
            WifiManager.WifiLock lock=null;
            try {
                if(wifi!=null){lock=wifi.createWifiLock(WifiManager.WIFI_MODE_FULL_HIGH_PERF,"SNARTY:transfer");lock.acquire();}
                new WirelessSync(Environment.getExternalStorageDirectory(),url,key,new WirelessSync.Host(){
                    public boolean ready(){return SnartyWireless.this.ready();}
                    public void progress(String text){status=text;}
                    public void changed(){changed.set(true);ArtistImages.start(new File(Environment.getExternalStorageDirectory(),".rockbox"));}
                }).run();
                prefs.edit().putLong("last_success",System.currentTimeMillis()).commit();
            } catch(WirelessSync.SourceBusy e) {
                status=e.getMessage();lastAttempt=SystemClock.elapsedRealtime()-14*60*1000;
            } catch(Exception e) {
                status="Sync paused: "+(e.getMessage()==null?"transfer failed":e.getMessage());
                lastAttempt=SystemClock.elapsedRealtime()-10*60*1000;
            } catch(OutOfMemoryError e) {
                status="Sync paused: library too large for memory; reduce this export";
                lastAttempt=SystemClock.elapsedRealtime();
            } finally {if(lock!=null&&lock.isHeld())lock.release();running.set(false);}
        }},"SNARTY Wi-Fi sync");
        worker.setPriority(Thread.MIN_PRIORITY);worker.start();
    }
    private String pair(String data) throws Exception {
        String[] fields=data.split("\t",-1);
        if(fields.length!=2)throw new IOException("Enter Syncer address and pairing key");
        String url=WirelessProtocol.endpoint(fields[0]).toString();WirelessProtocol.key(fields[1]);
        if(running.get())throw new IOException("Wait for current sync to finish before changing pairing");
        if(!prefs.edit().putString("url",url).putString("key",fields[1]).commit())
            throw new IOException("Cannot save Syncer pairing");
        lastAttempt=0;status="Paired. Use Music > Sync Library";return status;
    }
    private String importPairing(boolean explicit) throws Exception {
        File file=new File(Environment.getExternalStorageDirectory(),".rockbox/snarty/wireless-pairing.json");
        if(!file.isFile())return explicit?"No wireless-pairing.json from Syncer found":status;
        if(file.length()>4096)throw new IOException("Pairing file is too large");
        ByteArrayOutputStream out=new ByteArrayOutputStream();FileInputStream in=new FileInputStream(file);
        try {int b;while((b=in.read())!=-1){if(out.size()>=4096)throw new IOException("Pairing file too large");out.write(b);}}
        finally{in.close();}
        JSONObject config=new JSONObject(new String(out.toByteArray(),"UTF-8"));
        if(config.getInt("version")!=1)throw new IOException("Unsupported pairing file");
        String result=pair(config.getString("url")+"\t"+config.getString("key"));
        // Key is now in app-private preferences, not in Google/account storage.
        if(!file.delete())return result+". Remove pairing file from card manually";
        return result;
    }
    private String wifiStatus() {
        if(wifi==null)return "Wi-Fi hardware/service unavailable";
        if(!wifi.isWifiEnabled())return "Wi-Fi is off";
        WifiInfo info=wifi.getConnectionInfo();
        return connected()?"Connected: "+info.getSSID():"Wi-Fi on; not connected";
    }
    private String networks() {
        if(wifi==null || !wifi.isWifiEnabled())return "";
        List<ScanResult> list=wifi.getScanResults();if(list==null)return "";
        Collections.sort(list,new Comparator<ScanResult>(){public int compare(ScanResult a,ScanResult b){return b.level-a.level;}});
        Set<String> seen=new HashSet<String>();StringBuilder result=new StringBuilder();
        for(ScanResult n:list)if(n.SSID!=null && !n.SSID.isEmpty() && n.SSID.indexOf('\n')<0 && n.SSID.indexOf('\t')<0 && seen.add(n.SSID)){
            if(seen.size()>32)break;result.append(n.SSID).append('\n');
        }
        return result.toString();
    }
    private String connect(String data) throws Exception {
        if(wifi==null)throw new IOException("Wi-Fi unavailable");
        String[] fields=data.split("\t",-1);
        if(fields.length!=2 || fields[0].isEmpty() || fields[0].getBytes("UTF-8").length>32 ||
           fields[0].indexOf('\n')>=0)throw new IOException("Invalid network name");
        String ssid=fields[0],password=fields[1];
        if(!password.isEmpty() && !(password.length()>=8&&password.length()<=63 || password.matches("[0-9a-fA-F]{64}")))
            throw new IOException("WPA2 password must be 8-63 characters, or 64 hex digits");
        List<ScanResult> scanned=wifi.getScanResults();
        if(scanned!=null)for(ScanResult n:scanned)if(ssid.equals(n.SSID) && (n.capabilities.contains("EAP") || n.capabilities.contains("WEP")))
            throw new IOException("Use a WPA2-Personal home network; WEP/enterprise unsupported");
        if(!wifi.isWifiEnabled())throw new IOException("Enable Wi-Fi first, then connect");
        List<WifiConfiguration> saved=wifi.getConfiguredNetworks();
        if(password.isEmpty()&&saved!=null)for(WifiConfiguration old:saved)if(quote(ssid).equals(old.SSID)){
            if(!wifi.enableNetwork(old.networkId,true))throw new IOException("Cannot reconnect saved network");
            wifi.reconnect();return "Connecting to saved "+ssid+"...";
        }
        WifiConfiguration c=new WifiConfiguration();
        c.SSID=quote(ssid);c.hiddenSSID=true;
        if(password.isEmpty())c.allowedKeyManagement.set(WifiConfiguration.KeyMgmt.NONE);
        else {c.allowedKeyManagement.set(WifiConfiguration.KeyMgmt.WPA_PSK);c.preSharedKey=password.matches("[0-9a-fA-F]{64}")?password:quote(password);}
        int id=-1;
        if(saved!=null)for(WifiConfiguration old:saved)if(c.SSID.equals(old.SSID)){c.networkId=old.networkId;id=wifi.updateNetwork(c);break;}
        if(id<0)id=wifi.addNetwork(c);
        if(id<0 || !wifi.enableNetwork(id,true))throw new IOException("Android rejected this Wi-Fi network");
        wifi.saveConfiguration();wifi.reconnect();return "Connecting to "+ssid+"...";
    }
    private static String quote(String value){return "\""+value.replace("\\","\\\\").replace("\"","\\\"")+"\"";}
    /** Invoked from native UI with UTF-8 bytes; never returns passwords or account cookies. */
    public byte[] command(int code,byte[] bytes) {
        String result;
        try {
            String text=bytes==null?"":new String(bytes,"UTF-8");
            switch(code){
            case 0:result=wifiStatus();break;
            case 1:result=status;break;
            case 2:result=wifi!=null&&wifi.setWifiEnabled(true)?"Enabling Wi-Fi; saved networks reconnect":"Cannot enable Wi-Fi";break;
            case 3:result=wifi!=null&&wifi.setWifiEnabled(false)?"Turning Wi-Fi off":"Cannot disable Wi-Fi";break;
            case 4:result=wifi!=null&&wifi.startScan()?"Scanning; open Available Networks shortly":"Enable Wi-Fi before scanning";break;
            case 5:result=networks();break;
            case 6:result=connect(text);break;
            case 7:sync();result=status;break;
            case 8:boolean enabled=!prefs.getBoolean("auto",true);prefs.edit().putBoolean("auto",enabled).commit();result="Automatic sync "+(enabled?"on":"off");lastAttempt=0;break;
            case 9:result=pair(text);break;
            case 10:result="Auto sync: "+(prefs.getBoolean("auto",true)?"on":"off")+"; "+(paired()?prefs.getString("url",""):"not paired");break;
            case 11:result=service.mediaStorageReady()&&changed.getAndSet(false)?"changed":"";break;
            case 12:result=importPairing(true);break;
            default:result="Unknown wireless command";
            }
        } catch(Exception e){result=e.getMessage()==null?"Wireless operation failed":e.getMessage();}
        try{return result.getBytes("UTF-8");}catch(Exception ignored){return new byte[0];}
    }
}
