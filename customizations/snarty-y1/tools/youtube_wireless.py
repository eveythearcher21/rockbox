#!/usr/bin/env python3
"""Optional desktop-only YouTube Music adapter for the paired wireless bridge.

Uses the owner's ytmusicapi browser authorization and yt-dlp/FFmpeg. This is an
unofficial provider integration, not a Google-supported offline-download API.
Unavailable recordings/metadata/lyrics are never replaced with guessed matches.
"""
import hashlib
import io
import json
import re
import shutil
import tempfile
import time
from pathlib import Path

from compile_sync_library import encode_library
from wireless_bridge import atomic


def safe_component(value, limit=55):
    value = re.sub(r'[\x00-\x1f\\/:*?"<>|]', '_', str(value)).strip(' .')
    value = value or 'Unknown'
    while len(value.encode('utf-8')) > limit:
        value = value[:-1]
    if value.upper().split('.')[0] in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1, 10)), *('LPT'+str(i) for i in range(1, 10))}:
        value = '_' + value
    return value


def timestamp(ms):
    if isinstance(ms, bool) or not isinstance(ms, int) or ms < 0:
        raise ValueError('Invalid source lyric timestamp')
    centiseconds = ms // 10
    return f'{centiseconds//6000:02}:{centiseconds//100%60:02}.{centiseconds%100:02}'


def encode_lyrics(document, duration_ms):
    """Returns suffix, bytes, actual granularity. No invented word intervals."""
    if not document or not document.get('lyrics'):
        return None
    if document.get('hasTimestamps'):
        lines, previous = [], -1
        for line in document['lyrics']:
            get = (lambda name: line[name]) if isinstance(line, dict) else (lambda name: getattr(line, name))
            start, end, text = get('start_time'), get('end_time'), get('text')
            if not isinstance(start, int) or not isinstance(end, int) or start < previous or not 0 <= start <= end <= duration_ms+1000:
                raise ValueError('Provider lyric timing does not match audio duration')
            if not isinstance(text, str) or '\n' in text or '\r' in text or len(text.encode('utf-8')) > 440:
                raise ValueError('Provider lyric line is invalid/too long')
            lines.append(f'[{timestamp(start)}]{text}')
            previous = start
        return '.lrc', ('\ufeff'+'\n'.join(lines)+'\n').encode('utf-8'), 'lines'
    text = document['lyrics']
    if not isinstance(text, str) or len(text.encode('utf-8')) > 1024*1024:
        raise ValueError('Invalid plain provider lyrics')
    return '.txt', ('\ufeff'+text).encode('utf-8'), 'text'


def collect_library(api):
    """Explicit full pagination and independent source order; recording IDs only."""
    songs = api.get_library_songs(limit=None, order='recently_added')
    albums = api.get_library_albums(limit=None, order='recently_added')
    playlists = api.get_library_playlists(limit=None)
    tracks, song_rank, album_rank, playlist_tracks = {}, {}, {}, []

    def add(track, album=None, number=None):
        video = track.get('videoId')
        if not video or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video):
            raise ValueError('Library contains an unavailable recording; resolve it in YouTube Music first')
        enriched = dict(track)
        if album:
            enriched.setdefault('album', {'id': album['_id'], 'name': album['title']})
            enriched['_album'] = album
            enriched['_track_number'] = number
        existing = tracks.setdefault(video, {})
        existing.update({k: v for k, v in enriched.items() if v is not None})
        return video

    for rank, song in enumerate(songs, 1):
        song_rank[add(song)] = rank
    for rank, item in enumerate(albums, 1):
        browse = item['browseId']
        detail = dict(api.get_album(browse), _id=browse)
        album_rank[browse] = rank
        for number, song in enumerate(detail['tracks'], 1):
            add(song, detail, number)
    for item in playlists:
        detail = api.get_playlist(item['playlistId'], limit=None)
        ids = [add(track) for track in detail['tracks']]
        playlist_tracks.append({'id': item['playlistId'], 'title': detail['title'], 'tracks': ids})
    # Songs and playlist entries may refer to albums not saved in Albums. Enrich by exact
    # browse ID; their album-added rank remains zero unless actually in the album library.
    album_cache = {t['_album']['_id']: t['_album'] for t in tracks.values() if '_album' in t}
    for video, track in tracks.items():
        album_id = (track.get('album') or {}).get('id')
        if album_id and '_album' not in track:
            if album_id not in album_cache:
                album_cache[album_id] = dict(api.get_album(album_id), _id=album_id)
            album = album_cache[album_id]
            track['_album'] = album
            match = next((i for i, t in enumerate(album['tracks'], 1) if t.get('videoId') == video), None)
            track['_track_number'] = match
    return tracks, song_rank, album_rank, playlist_tracks


def fetch_jpeg(thumbnails, session):
    from PIL import Image, ImageOps
    if not thumbnails:
        return None
    best = max(thumbnails, key=lambda t: t.get('width', 0)*t.get('height', 0))
    url = best.get('url', '')
    if not url.startswith('https://'):
        raise ValueError('Artist/cover source is not HTTPS')
    response = session.get(url, timeout=(10, 30), stream=True)
    try:
        response.raise_for_status()
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > 16*1024*1024:
                raise ValueError('Artwork source too large')
    finally:
        response.close()
    Image.MAX_IMAGE_PIXELS = 25_000_000
    with Image.open(io.BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image)
        image = ImageOps.fit(image.convert('RGB'), (200, 200), method=Image.Resampling.LANCZOS)
        result = io.BytesIO()
        image.save(result, format='JPEG', quality=88, progressive=False)
    return result.getvalue()


def prepare_youtube(auth, export, state, cookies=None, api=None, downloader=None, oauth_credentials=None):
    """Prepare complete updated export, then the bridge snapshots it atomically.

    api/downloader injectable for recording-ID/metadata integration tests only.
    No provider API operation is implied to have passed by those offline tests.
    """
    from ytmusicapi import YTMusic
    import requests
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TPE2, TALB, TRCK, TPOS, TDRC, TCON, TXXX
    export, state = Path(export), Path(state)
    for private in (auth, cookies, oauth_credentials):
        if private and (Path(private).resolve()==export.resolve() or export.resolve() in Path(private).resolve().parents):
            raise ValueError('Keep Google authorization/cookies outside the exported media folder')
    if downloader is None and shutil.which('ffmpeg') is None:
        raise ValueError('Install FFmpeg on the computer PATH before starting YouTube sync')
    state.mkdir(parents=True, exist_ok=True)
    export.mkdir(parents=True, exist_ok=True)
    if api is None:
        if oauth_credentials:
            from ytmusicapi.auth.oauth import OAuthCredentials
            config = json.loads(Path(oauth_credentials).read_text('utf-8'))
            api = YTMusic(str(auth), oauth_credentials=OAuthCredentials(config['client_id'], config['client_secret']))
        else:
            api = YTMusic(str(auth))
    tracks, song_ranks, album_ranks, playlists = collect_library(api)
    if len(tracks) > 10000:
        raise ValueError('More than 10000 source recordings; choose a smaller library')
    db_path = state/'catalog.json'
    db = json.loads(db_path.read_text('utf-8')) if db_path.exists() else {'tracks': {}, 'artists': {}}
    warnings, ranks, missing_portraits, artist_attempted = [], [], set(), set()
    session = requests.Session()
    session.headers['User-Agent'] = 'SNARTY-Y1-owner-sync/16'

    class Quiet:
        def debug(self, *_): pass
        def warning(self, *_): pass
        def error(self, *_): pass

    def download(video, output):
        if downloader:
            return downloader(video, output)
        import yt_dlp
        with tempfile.TemporaryDirectory(dir=state, prefix='audio-') as work:
            options = {'format': 'bestaudio/best', 'outtmpl': str(Path(work)/'source.%(ext)s'),
                       'noplaylist': True, 'quiet': True, 'no_warnings': True, 'logger': Quiet(),
                       'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '0'}]}
            if cookies:
                options['cookiefile'] = str(cookies)
            try:
                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info('https://www.youtube.com/watch?v='+video, download=True)
            except yt_dlp.utils.DownloadError as error:
                raise ValueError('Recording '+video+' could not be downloaded. Check FFmpeg, yt-dlp JavaScript runtime and account/recording access on this computer.') from error
            if not info or info.get('id') != video or not (Path(work)/'source.mp3').is_file():
                raise ValueError('Downloader did not produce the exact requested recording')
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(work)/'source.mp3', output)

    for ordinal, (video, track) in enumerate(tracks.items(), 1):
        if ordinal == 1 or ordinal % 25 == 0:
            print(f'Preparing source recordings: {ordinal}/{len(tracks)}', flush=True)
        title = track.get('title')
        artists = track.get('artists') or []
        artist = next((a.get('name') for a in artists if a.get('name')), None)
        album = track.get('_album') or {}
        album_title = album.get('title') or (track.get('album') or {}).get('name')
        missing_metadata = [k for k,v in [('title',title),('artist',artist),('album',album_title)] if not v]
        # Explicit unknown values keep available recordings syncable; do not infer an
        # album, performer or release date from unrelated search results/download dates.
        unknown_album = not album_title
        title,artist,album_title = title or 'Unknown Title',artist or 'Unknown Artist',album_title or 'Unknown Album'
        album_id = album.get('_id') or (track.get('album') or {}).get('id') or ''
        artist_id = next((a.get('id') for a in artists if a.get('name') == artist), None)
        old = db['tracks'].get(video, {})
        path = old.get('path') or ('Music/'+safe_component(artist, 45)+'/'+safe_component(album_title, 45)+'-'+hashlib.sha256(album_id.encode()).hexdigest()[:8]+'/'+safe_component(title, 60)+'-'+video+'.mp3')
        audio = export/path
        album_artists = album.get('artists') or artists
        album_artist = next((a.get('name') for a in album_artists if a.get('name')), artist)
        source_hash = hashlib.sha256(json.dumps({'title':title,'artist':artist,'artists':artists,
            'album':album_title,'album_artist':album_artist,'album_id':album_id,
            'track':track.get('_track_number'),'disc':track.get('discNumber'),
            'year':album.get('year'),'genre':track.get('genre')},sort_keys=True).encode()).hexdigest()
        if not audio.is_file():
            staging = state/(video+'.mp3')
            try:
                download(video, staging)
                MP3(staging)  # real MP3 parser rejects a renamed MP4/HTML/error response
                audio.parent.mkdir(parents=True, exist_ok=True)
                temporary = audio.with_name(audio.name+'.tmp')
                with staging.open('rb') as source, temporary.open('wb') as target:
                    shutil.copyfileobj(source, target, 65536)
                    target.flush()
                    import os
                    os.fsync(target.fileno())
                temporary.replace(audio)
            finally:
                staging.unlink(missing_ok=True)
        parsed = MP3(audio)
        duration = round(parsed.info.length*1000)
        if duration <= 0:
            raise ValueError('Downloaded recording has no valid duration')
        if old.get('metadata_hash') != source_hash:
            temporary = audio.with_name(audio.name+'.tmp')
            shutil.copyfile(audio, temporary)
            tags = ID3(temporary) if parsed.tags is not None else ID3()
            tags.setall('TIT2', [TIT2(encoding=3, text=[title])])
            tags.setall('TPE1', [TPE1(encoding=3, text=[artist])])
            tags.setall('TPE2', [TPE2(encoding=3, text=[album_artist])])
            tags.setall('TALB', [TALB(encoding=3, text=[album_title])])
            if track.get('_track_number'):
                tags.setall('TRCK', [TRCK(encoding=3, text=[str(track['_track_number'])+'/'+str(len(album.get('tracks') or []))])])
            if track.get('discNumber'):
                tags.setall('TPOS', [TPOS(encoding=3, text=[str(track['discNumber'])])])
            if album.get('year'):
                tags.setall('TDRC', [TDRC(encoding=3, text=[str(album['year'])])])
            if track.get('genre'):
                tags.setall('TCON', [TCON(encoding=3, text=[track['genre']])])
            tags.add(TXXX(encoding=3, desc='YOUTUBE_MUSIC_ID', text=[video]))
            tags.add(TXXX(encoding=3, desc='YOUTUBE_MUSIC_ALBUM_ID', text=[album_id]))
            tags.add(TXXX(encoding=3, desc='ARTISTS', text=[a['name'] for a in artists if a.get('name')]))
            tags.save(temporary, v2_version=3)
            temporary.replace(audio)
        missing_metadata += [k for k,v in [('year',album.get('year')),('genre',track.get('genre')),('disc',track.get('discNumber'))] if not v]
        if missing_metadata:
            warnings.append({'video_id': video, 'missing_metadata': missing_metadata})
        cover = audio.with_suffix('.jpg') if unknown_album else audio.parent/'cover.jpg'
        if not cover.is_file():
            try:
                image = fetch_jpeg(album.get('thumbnails') or track.get('thumbnails'), session)
                if image:
                    atomic(cover, image)
            except Exception:
                warnings.append({'video_id': video, 'missing': 'album_cover'})
        portrait_name = safe_component(artist, 180)
        portrait = export/'Artist_Images'/(portrait_name+'.jpg')
        artist_key = artist_id or 'unavailable:'+artist
        conflicting = any(v == portrait_name and k != artist_key for k, v in db['artists'].items())
        native_name = re.sub(r'[\\/:*?"<>|]', '_', artist)
        if portrait_name != native_name:
            missing_portraits.add(artist_key)
            warnings.append({'artist':artist,'missing':'portrait_name_exceeds_safe_native_path_rules'})
        elif conflicting:
            missing_portraits.add(artist_key)
            warnings.append({'artist': artist, 'missing': 'ambiguous_portrait_name'})
        elif not portrait.is_file() and artist_id and artist_key not in artist_attempted:
            artist_attempted.add(artist_key)
            try:
                image = fetch_jpeg(api.get_artist(artist_id).get('thumbnails'), session)
                if image:
                    atomic(portrait, image)
                    db['artists'][artist_key] = portrait_name
                else:
                    missing_portraits.add(artist_key)
            except Exception:
                missing_portraits.add(artist_key)
        elif not portrait.is_file():
            missing_portraits.add(artist_key)
        else:
            db['artists'].setdefault(artist_key,portrait_name)
        if not old.get('lyrics_checked_at') or time.time()-old['lyrics_checked_at'] > 86400:
            try:
                watch = api.get_watch_playlist(videoId=video, limit=1)
                lyric = api.get_lyrics(watch['lyrics'], timestamps=True) if watch.get('lyrics') else None
                try:
                    encoded = encode_lyrics(lyric, duration)
                except ValueError:
                    # Reject incorrect synchronization while still retaining real available text.
                    lyric = api.get_lyrics(watch['lyrics'], timestamps=False)
                    encoded = encode_lyrics(lyric,duration)
                if encoded:
                    suffix, data, granularity = encoded
                    # Preserve a user/Syncer-supplied enhanced LRC with genuine word timings.
                    existing = audio.with_suffix('.lrc')
                    word_lrc = existing.is_file() and re.search(r'<\d+:\d+\.\d+>', existing.read_text('utf-8-sig'))
                    if not word_lrc:
                        atomic(audio.with_suffix(suffix), data)
                        atomic(Path(str(audio)+'.lyrics.meta.json'), json.dumps({'video_id': video, 'audio_sha256': hashlib.sha256(audio.read_bytes()).hexdigest(), 'source': lyric.get('source'), 'granularity': granularity, 'method': 'provider', 'estimated': False}).encode())
                old['lyrics_checked_at'] = time.time()
            except Exception:
                warnings.append({'video_id': video, 'missing': 'lyrics_fetch_or_timing_validation'})
        db['tracks'][video] = dict(old, path=path, metadata_hash=source_hash)
        ranks.append({'device_path': '/sdcard/'+path, 'song_added_rank': song_ranks.get(video, 0), 'album_added_rank': album_ranks.get(album_id, 0)})
        # Bounded checkpoints avoid rewriting a whole large catalog once per song.
        # Failed later source refresh never replaces the bridge's last manifest.
        if ordinal % 50 == 0:
            atomic(db_path, json.dumps(db, ensure_ascii=False).encode())
    atomic(db_path, json.dumps(db, ensure_ascii=False).encode())
    for playlist in playlists:
        name = safe_component(playlist['title'], 100)+'-'+hashlib.sha256(playlist['id'].encode()).hexdigest()[:8]+'.m3u8'
        content = '#EXTM3U\n'+''.join('/sdcard/'+db['tracks'][video]['path']+'\n' for video in playlist['tracks'])
        atomic(export/'Playlists'/name, content.encode('utf-8'))
    atomic(export/'.rockbox/snarty/library-v1.bin', encode_library({'version': 1, 'tracks': ranks}))
    atomic(export/'wireless-source-report.json', json.dumps({'source': 'youtube-music-unofficial-owner-authorized', 'missing_artist_images': len(missing_portraits), 'warnings': warnings}, ensure_ascii=False).encode())
    session.close()

