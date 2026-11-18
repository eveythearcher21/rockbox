/* Offline continuation: synced per-track radio, then honest metadata fallback.
 * Recommendation order is preserved. No on-device streaming/downloading. GPLv2+. */
#include "config.h"
#include <string.h>
#include "string-extra.h"
#include <strings.h>
#include <stdio.h>
#include <stdlib.h>
#include "file.h"
#include "rbpaths.h"
#include "kernel.h"
#include "metadata.h"
#include "audio.h"
#include "playlist.h"
#include "tagcache.h"
#include "splash.h"
#include "misc.h"
#include "action.h"
#include "filetypes.h"
#include "settings.h"
#include "snarty_radio.h"
#include "snarty_library.h"
#define RADIO_MAX 128
static struct candidate { int score;char path[MAX_PATH]; } candidates[RADIO_MAX];
static bool same(const char*a,const char*b){return a&&b&&*a&&*b&&!strcasecmp(a,b);}
static int compare_radio(const void*a,const void*b)
{
    const struct candidate*x=a,*y=b;
    if(x->score!=y->score)return x->score>y->score?-1:1;
    return strcasecmp(x->path,y->path);
}
static bool playable(const char*path,const char*seed)
{
    return path[0]=='/'&&!strstr(path,"/../")&&!strstr(path,"/./")&&
        !strchr(path,'\r')&&!strchr(path,'\n')&&!strchr(path,'\t')&&
        !snarty_device_paths_equal(path,seed)&&file_exists(path)&&((filetype_get_attr(path)&FILE_ATTR_MASK)==FILE_ATTR_AUDIO);
}
static bool duplicate(int count,const char*path)
{for(int i=0;i<count;i++)if(snarty_device_paths_equal(candidates[i].path,path))return true;return false;}
int snarty_play_similar_for(const struct mp3entry *selected)
{
    const struct mp3entry *now=selected?selected:audio_current_track();
    if(!now || global_settings.party_mode)return 0;
    char seed[MAX_PATH],sidecar[MAX_PATH+32];
    static char artist[TAG_MAXLEN],album[TAG_MAXLEN],genre[TAG_MAXLEN],group[TAG_MAXLEN],title[TAG_MAXLEN];
    strlcpy(seed,now->path,sizeof(seed));strlcpy(artist,now->albumartist&&*now->albumartist?now->albumartist:now->artist?now->artist:"",sizeof(artist));
    strlcpy(album,now->album?now->album:"",sizeof(album));strlcpy(genre,now->genre_string?now->genre_string:"",sizeof(genre));
    strlcpy(group,now->grouping?now->grouping:"",sizeof(group));strlcpy(title,now->title?now->title:"",sizeof(title));int year=now->year;
    snprintf(sidecar,sizeof(sidecar),"%s.radio.m3u8",seed);
    int fd=open(sidecar,O_RDONLY),count=0;
    if(fd>=0)
    {
        char path[MAX_PATH];int length;
        while(count<RADIO_MAX&&(length=read_line(fd,path,sizeof(path)))>0)
        {
            if(strlen(path)>=sizeof(path)-1){char ch;while(read(fd,&ch,1)==1&&ch!='\n'){};continue;}
            if(path[0]=='#'||!playable(path,seed)||duplicate(count,path))continue;
            strlcpy(candidates[count].path,path,MAX_PATH);candidates[count++].score=1000;
        }
        close(fd);
    }
    bool service_radio=count>0;
    if(!count && tagcache_is_usable())
    {
        splash(0,"Finding local metadata matches...");
        struct tagcache_search search;
        if(tagcache_search(&search,tag_filename))
        {
            char path[MAX_PATH];static char ca[TAG_MAXLEN],al[TAG_MAXLEN],ge[TAG_MAXLEN],gr[TAG_MAXLEN],ti[TAG_MAXLEN];int scanned=0;
            while(tagcache_get_next(&search,path,sizeof(path)))
            {
                if((scanned++%16)==0&&action_userabort(TIMEOUT_NOBLOCK)){count=0;break;}
                if(!playable(path,seed))continue;
                ca[0]=al[0]=ge[0]=gr[0]=ti[0]=0;
                tagcache_retrieve(&search,search.idx_id,tag_virt_canonicalartist,ca,sizeof(ca));
                tagcache_retrieve(&search,search.idx_id,tag_album,al,sizeof(al));
                tagcache_retrieve(&search,search.idx_id,tag_genre,ge,sizeof(ge));
                tagcache_retrieve(&search,search.idx_id,tag_grouping,gr,sizeof(gr));
                tagcache_retrieve(&search,search.idx_id,tag_title,ti,sizeof(ti));
                if(same(artist,ca)&&same(title,ti))continue;
                int score=0;bool related_artist=same(artist,ca),related_genre=same(genre,ge),related_group=same(group,gr);
                if(related_artist)score+=45;
                if(related_genre)score+=30;
                if(related_group)score+=30;
                if(same(album,al)&&related_artist)score+=4;
                int cy=tagcache_get_numeric(&search,tag_year);
                if(year>0&&year<10000&&cy>0&&cy<10000){int delta=abs(cy-year);if(delta<=3)score+=8;else if(delta<=8)score+=4;}
                if(score<35||(!related_artist&&!related_genre&&!related_group))continue;
                int at=count;
                if(count==RADIO_MAX){at=0;for(int i=1;i<count;i++)if(candidates[i].score<candidates[at].score)at=i;if(score<=candidates[at].score)continue;}
                else count++;
                candidates[at].score=score;strlcpy(candidates[at].path,path,MAX_PATH);
                yield();
            }
            tagcache_search_finish(&search);
        }
        if(count)qsort(candidates,count,sizeof(candidates[0]),compare_radio);
    }
    if(!count){splash(HZ*3,"No related tracks on device. Sync radio recommendations.");return 0;}
    const char *temp=ROCKBOX_DIR "/snarty-radio.tmp.m3u8";
    fd=open(temp,O_WRONLY|O_CREAT|O_TRUNC,0666);if(fd<0){splash(HZ*2,"Cannot prepare radio queue");return 0;}
    bool ok=true;for(int i=0;i<count;i++)if(fdprintf(fd,"%s\n",candidates[i].path)<=0)ok=false;
    if(close(fd)<0)ok=false;
    now=audio_current_track();
    if(ok&&warn_on_pl_erase())
    {
        bool same_track=now&&snarty_device_paths_equal(now->path,seed);
        if(!same_track && !selected){remove(temp);return 0;}
        if(!same_track){
            if(playlist_create(NULL,NULL)<0||playlist_insert_track(NULL,seed,PLAYLIST_INSERT_LAST,false,true)<0||playlist_insert_playlist(NULL,temp,PLAYLIST_INSERT_LAST,false)<0){splash(HZ*2,"Cannot start selected-song radio");remove(temp);return 0;}
            playlist_sync(NULL);playlist_start(0,0,0);remove(temp);return 1;
        }
        if(playlist_remove_all_tracks(NULL)>=0 && playlist_insert_playlist(NULL,temp,PLAYLIST_INSERT_LAST,false)>=0)
        {playlist_sync(NULL);splash(HZ,service_radio?"Synced radio queued":"Local metadata matches queued");}
        else splash(HZ*2,"Could not update radio queue");
    }
    remove(temp);return 0;
}

int snarty_play_similar(void){return snarty_play_similar_for(NULL);}
