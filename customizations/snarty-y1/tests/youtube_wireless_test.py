#!/usr/bin/env python3
"""Offline adapter integration using synthetic audio/art and a recording provider.
Tests exact IDs, full-pagination arguments, real ID3/LRC/JPEG/ranks. No live account.
"""
import io,json,shutil,subprocess,sys,tempfile,struct
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from mutagen.mp3 import MP3
repo=Path(__file__).resolve().parents[3];sys.path.insert(0,str(repo/'customizations/snarty-y1/tools'))
from youtube_wireless import prepare_youtube,collect_library,encode_lyrics
from wireless_bridge import snapshot
work=Path(tempfile.mkdtemp(prefix='snarty-youtube-'));audio=work/'fixture.mp3'
subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=3','-c:a','libmp3lame',str(audio)],check=True)
im=Image.new('RGB',(400,200),(25,150,100));buf=io.BytesIO();im.save(buf,'PNG');image=buf.getvalue()
class Response:
    def raise_for_status(self):pass
    def iter_content(self,_):yield image
    def close(self):pass
class Session:
    headers={}
    def get(self,url,**kw):assert url=='https://image.test/exact-id';return Response()
    def close(self):pass
class API:
    def __init__(self):self.calls=[]
    def track(self,v):return {'videoId':v,'title':'First' if v=='AAAAAAAAAAA' else 'Second','artists':[{'name':'Artist A','id':'UC-exact-artist'}],'album':{'id':'MPRE-exact-album','name':'An Album'},'discNumber':1,'genre':'Test genre'}
    def get_library_songs(self,limit,order):assert limit is None and order=='recently_added';self.calls.append('songs-all');return [self.track('BBBBBBBBBBB'),self.track('AAAAAAAAAAA')]
    def get_library_albums(self,limit,order):assert limit is None and order=='recently_added';return [{'browseId':'MPRE-exact-album'}]
    def get_library_playlists(self,limit):assert limit is None;return [{'playlistId':'PL-exact-playlist'}]
    def get_album(self,browse):assert browse=='MPRE-exact-album';return {'title':'An Album','artists':[{'name':'Artist A','id':'UC-exact-artist'}],'year':'2020','thumbnails':[{'url':'https://image.test/exact-id','width':400,'height':200}],'tracks':[self.track('AAAAAAAAAAA'),self.track('BBBBBBBBBBB')]}
    def get_playlist(self,p,limit):assert p=='PL-exact-playlist' and limit is None;return {'title':'My List','tracks':[self.track('AAAAAAAAAAA'),self.track('BBBBBBBBBBB')]}
    def get_artist(self,artist):assert artist=='UC-exact-artist';self.calls.append('portrait-exact-id');return {'thumbnails':[{'url':'https://image.test/exact-id','width':400,'height':200}]}
    def get_watch_playlist(self,videoId,limit):assert videoId in ('AAAAAAAAAAA','BBBBBBBBBBB') and limit==1;return {'lyrics':'MPLYt-'+videoId}
    def get_lyrics(self,browse,timestamps):assert timestamps is True;return {'lyrics':[{'text':'Original words','start_time':500,'end_time':1500}],'hasTimestamps':True,'source':'Synthetic test source'}
api=API();downloaded=[]
def downloader(video,target):assert video in ('AAAAAAAAAAA','BBBBBBBBBBB');downloaded.append(video);shutil.copyfile(audio,target)
export,state=work/'export',work/'state'
with patch('requests.Session',Session):
    prepare_youtube(None,export,state,api=api,downloader=downloader)
    db=json.loads((state/'catalog.json').read_text())
    assert sorted(downloaded)==['AAAAAAAAAAA','BBBBBBBBBBB']
    for video,row in db['tracks'].items():
        file=export/row['path'];tags=MP3(file).tags
        assert tags['TIT2'].text==['First' if video=='AAAAAAAAAAA' else 'Second']
        assert tags['TPE1'].text==['Artist A'] and tags['TALB'].text==['An Album'] and tags['TPE2'].text==['Artist A']
        assert str(tags['TDRC'])=='2020' and str(tags['TPOS'])=='1'
        assert tags['TXXX:YOUTUBE_MUSIC_ID'].text==[video]
        assert '[00:00.50]Original words' in file.with_suffix('.lrc').read_text('utf-8-sig')
        assert (file.parent/'cover.jpg').is_file()
    portrait=Image.open(export/'Artist_Images/Artist A.jpg');assert portrait.format=='JPEG' and portrait.size==(200,200)
    assert api.calls.count('portrait-exact-id')==1
    raw=(export/'.rockbox/snarty/library-v1.bin').read_bytes();assert raw[:8]==b'SNRTLIB1';n,size=struct.unpack('<II',raw[8:16]);assert n==2 and size==268
    rows=[struct.unpack('<260sII',raw[16+i*268:16+(i+1)*268]) for i in range(n)]
    ranks={path.rstrip(b'\0').decode():rank for path,rank,album in rows};assert ranks['/sdcard/'+db['tracks']['BBBBBBBBBBB']['path']]==1 and ranks['/sdcard/'+db['tracks']['AAAAAAAAAAA']['path']]==2
    playlist=next((export/'Playlists').glob('*.m3u8')).read_text();assert playlist.splitlines()[1:]==['/sdcard/'+db['tracks'][v]['path'] for v in ('AAAAAAAAAAA','BBBBBBBBBBB')]
    target=(export/db['tracks']['AAAAAAAAAAA']['path']).with_suffix('.lrc');words='[00:00.00]<00:00.00>Real <00:00.50>word<00:01.00>\n';target.write_text(words)
    db['tracks']['AAAAAAAAAAA']['lyrics_checked_at']=0;(state/'catalog.json').write_text(json.dumps(db))
    prepare_youtube(None,export,state,api=api,downloader=downloader)
    assert len(downloaded)==2 and target.read_text()==words
    manifest=json.loads(snapshot(export,work/'objects'));assert manifest['missing_lyrics']==0 and manifest['missing_artist_images']==0
assert encode_lyrics({'lyrics':'Original plain lyric','hasTimestamps':False},3000)[2]=='text'
class Sparse(API):
    def __init__(self):super().__init__();self.portrait_calls=0
    def track(self,v):
        t=super().track(v);t['album']={'id':'MPRE-exact-album'};t.pop('genre');t.pop('discNumber');return t
    def get_album(self,browse):
        d=super().get_album(browse);d['title']=None;d.pop('year');return d
    def get_artist(self,artist):self.portrait_calls+=1;raise ValueError('No source portrait')
sparse=Sparse()
with patch('requests.Session',Session):prepare_youtube(None,work/'sparse-export',work/'sparse-state',api=sparse,downloader=downloader)
sparse_manifest=json.loads(snapshot(work/'sparse-export',work/'sparse-objects'))
assert sparse.portrait_calls==1 and sparse_manifest['missing_artist_images']==1 and sparse_manifest['metadata_gaps']==2
for file in (work/'sparse-export/Music').rglob('*.mp3'):
    tags=MP3(file).tags;assert tags['TALB'].text==['Unknown Album'] and tags.get('TDRC') is None and tags.get('TCON') is None and tags.get('TPOS') is None
    assert file.with_suffix('.jpg').is_file()
try:encode_lyrics({'lyrics':[{'text':'Wrong edition','start_time':9000,'end_time':9500}],'hasTimestamps':True},3000);raise AssertionError('Invalid timing accepted')
except ValueError:pass
class Unavailable(API):
    def get_library_songs(self,limit,order):return [{'title':'Unavailable','videoId':None}]
try:collect_library(Unavailable());raise AssertionError('Unavailable recording accepted')
except ValueError:pass
print('PASS: full-pagination arguments, exact recording/artist IDs, real playable MP3 tags/track-disc-year-genre, 200px JPEG portraits/covers, chronological ranks, complete playlist order, real line timing/plain fallback, word-LRC preservation, incremental downloads and unavailable-recording rejection; evidence',work)
