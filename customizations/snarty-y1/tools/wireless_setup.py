#!/usr/bin/env python3
"""Local interactive launcher for reference bridge, not the user's Syncer GUI."""
import ipaddress
import os
import shutil
import sys
from pathlib import Path
from wireless_bridge import main


def path_input(prompt, default=None):
    value=input(prompt+(f' [{default}]' if default else '')+': ').strip().strip('"')
    return Path(value) if value else default


def setup():
    state=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local/share'))/'RockBlockWireless'
    print('SNARTY Y1 Wi-Fi Sync reference bridge')
    print('Keep this computer running, connected to your home network. No account credentials go to the Y1.')
    ip=input('This computer\'s home-network IPv4 (shown by ipconfig, e.g. 192.168.1.25): ').strip()
    address=ipaddress.ip_address(ip)
    if address.version!=4 or not address.is_private or address.is_loopback or address.is_unspecified:
        raise ValueError('Use this computer\'s private home-network IPv4 address')
    mode=input('1 = prepared Syncer export, 2 = YouTube Music account [1]: ').strip() or '1'
    extra=[]
    if mode=='1':
        export=path_input('Computer folder containing Music, Playlists and Artist_Images (not the Y1 drive)')
        if export is None or not export.is_dir():raise ValueError('Choose an existing prepared computer export folder')
    elif mode=='2':
        export=state/'export'
        if shutil.which('ffmpeg') is None:
            directory=path_input('Folder containing installed ffmpeg.exe (or cancel and install FFmpeg)')
            if directory is None or not (directory/'ffmpeg.exe').is_file():raise ValueError('FFmpeg is required for playable tagged MP3 output')
            os.environ['PATH']=str(directory)+os.pathsep+os.environ.get('PATH','')
        auth=path_input('Existing desktop-only ytmusicapi authorization JSON')
        if auth is None or not auth.is_file():raise ValueError('Authorize your account locally with ytmusicapi or use your existing Syncer export')
        extra=['--youtube-auth',str(auth)]
        oauth=path_input('OAuth client JSON with client_id/client_secret (blank for browser auth)')
        if oauth:extra+=['--youtube-oauth-credentials',str(oauth)]
        cookies=path_input('Optional desktop yt-dlp Netscape cookies file (blank if unnecessary)')
        if cookies:extra+=['--youtube-cookies',str(cookies)]
    else:raise ValueError('Choose 1 or 2')
    pair=Path.cwd()/'wireless-pairing.json'
    print('Pairing file:',pair)
    print('Copy it to .rockbox/snarty/wireless-pairing.json on the Y1, safely eject, then Settings > Wi-Fi > Syncer Pairing / Library > Import Syncer Pairing.')
    print('Allow Python through Windows Firewall for Private networks only. Ctrl+C stops the bridge.')
    sys.argv=[sys.argv[0],'--export',str(export),'--state',str(state),'--host',ip,'--pair-url',f'http://{ip}:8787','--pair-output',str(pair),*extra]
    main()


if __name__=='__main__':
    try:setup()
    except (ValueError,OSError) as error:
        print('Setup stopped:',error)
        input('Press Enter to close...')
        raise SystemExit(1)
