/* Actual production transfer engine driven by the paired test server. GPLv2+. */
package org.rockbox;
import java.io.*;
import java.nio.file.*;
public class WirelessTransferTest {
    static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception{
        final String mode=args[0];File root=new File(args[1]);root.mkdirs();
        final boolean[] changed={false};final String[] status={""};
        WirelessSync.Host host=new WirelessSync.Host(){
            public boolean ready(){return !mode.equals("offline");}
            public void progress(String text){status[0]=text;}
            public void changed(){changed[0]=true;}
        };
        int result=-1;IOException error=null;
        try{result=new WirelessSync(root,args[2],args[3],host).run();}catch(IOException e){error=e;}
        if(mode.equals("first")){
            check(error==null,"first transfer: "+error);check(result==8,"eight files: "+result);
            check(changed[0],"core notified");
            check(new File(root,"Artist_Images/Artist A.jpg").isFile(),"portrait");
            check(new File(root,"Music/A/song.lrc").isFile(),"lyrics");
            check(new File(root,".rockbox/snarty/library-v1.bin").isFile(),"source ranks");
            check(status[0].contains("Missing lyrics: 0"),"source coverage");
        }else if(mode.equals("same")){
            check(error==null&&result==0&&!changed[0],"incremental unchanged: "+error);
        }else if(mode.equals("update")){
            check(error==null&&result==1&&changed[0],"one managed update: "+error);
        }else{
            check(error!=null,"expected failure: "+mode);
            if(mode.equals("local-edit"))check(error.getMessage().contains("Local file differs"),"local edit preserved");
            if(mode.equals("bad-manifest"))check(error.getMessage().contains("authentication"),"manifest authentication");
            if(mode.equals("corrupt"))check(error.getMessage().contains("checksum"),"file hash");
            if(mode.equals("escape"))check(error.getMessage().contains("path"),"path rejection");
            if(mode.equals("collision"))check(error.getMessage().contains("colliding"),"collision rejection");
            check(!changed[0],"failed preflight/download must not publish");
        }
        for(String path:new String[]{"../Music/no.mp3","Music/../../no.mp3","/Music/no.mp3","Music/a\\b.mp3",".rockbox/config.cfg","Artist_Images/sub/a.jpg","Music/foo./a.mp3","Music/a\n.mp3"}){
            boolean rejected=false;try{WirelessProtocol.destination(root,path);}catch(IOException expected){rejected=true;}
            check(rejected,"unsafe path: "+path);
        }
        for(String url:new String[]{"https://192.168.1.3:8787","http://example.com:8787","http://1.1.1.1:8787","http://127.0.0.1:8787/?secret=x","http://a@127.0.0.1:8787"}){
            boolean rejected=false;try{WirelessProtocol.endpoint(url);}catch(IOException expected){rejected=true;}
            check(rejected,"unsafe endpoint: "+url);
        }
        System.out.println("PASS: "+mode+" actual production wireless transfer/policy");
    }
}
