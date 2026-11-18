/* Persistent explicit song/album/artist rules. Future tracks match at browse time. GPLv2+. */
#include "config.h"
#include <string.h>
#include <strings.h>
#include <stdio.h>
#include <stdint.h>
#include "file.h"
#include "dir.h"
#include "rbpaths.h"
#include "metadata.h"
#include "string-extra.h"
#include "snarty_library.h"
#include "snarty_favorites.h"
#define FAVDIR ROCKBOX_DIR "/snarty-favorites-v1"
struct rule { char magic[4],kind;char path[260],artist[256],album[256]; };
static bool tagged(const char *s){return s&&*s&&strcasecmp(s,"<Untagged>");}
static bool key(struct rule *r,int kind,const char *path,const char *artist,const char *album)
{
    memset(r,0,sizeof(*r));memcpy(r->magic,"FAV1",4);r->kind=kind;
    if(kind==1)return snarty_device_path(path,r->path,sizeof(r->path));
    if(!tagged(artist)||strlen(artist)>=sizeof(r->artist))return false;
    strcpy(r->artist,artist);
    if(kind==2){if(!tagged(album)||strlen(album)>=sizeof(r->album))return false;strcpy(r->album,album);}
    return true;
}
static int access_rule(const struct rule *wanted,bool toggle)
{
    uint32_t hash=2166136261U;const unsigned char *p=(const unsigned char*)wanted;
    for(unsigned i=0;i<sizeof(*wanted);i++){unsigned char c=p[i];if(c>='A'&&c<='Z')c+='a'-'A';hash=(hash^c)*16777619U;}
    char file[MAX_PATH],empty[MAX_PATH]={0};struct rule found;bool removing=false;
    for(int i=0;i<16;i++){
        snprintf(file,sizeof(file),FAVDIR "/%08lx-%02d.fav",(unsigned long)hash,i);
        int fd=open(file,O_RDONLY);
        if(fd<0){strlcpy(empty,file,sizeof(empty));break;}
        bool ok=read(fd,&found,sizeof(found))==sizeof(found);close(fd);
        if(ok&&memcmp(found.magic,"FAV",3)==0&&found.kind==wanted->kind&&
           memchr(found.path,0,sizeof(found.path))&&memchr(found.artist,0,sizeof(found.artist))&&memchr(found.album,0,sizeof(found.album))&&
           !strcasecmp(found.path,wanted->path)&&!strcasecmp(found.artist,wanted->artist)&&!strcasecmp(found.album,wanted->album)){
            bool active=found.magic[3]=='1';
            if(!toggle)return active?1:0;
            removing=active;strlcpy(empty,file,sizeof(empty));break;
        }
    }
    if(!toggle)return 0;
    if(!empty[0])return -1;
    if(!dir_exists(FAVDIR)&&mkdir(FAVDIR)<0)return -1;
    char temp[MAX_PATH+8];snprintf(temp,sizeof(temp),"%s.tmp",empty);
    int fd=open(temp,O_WRONLY|O_CREAT|O_TRUNC,0666);if(fd<0)return -1;
    struct rule output=*wanted;if(removing)output.magic[3]='0';
    bool ok=write(fd,&output,sizeof(output))==sizeof(output);if(close(fd)<0)ok=false;
    if(ok&&rename(temp,empty)==0)return removing?0:1;
    remove(temp);return -1;
}
bool snarty_favorites_match(const char *path,const char *artist,const char *albumartist,const char *album)
{
    struct rule r;const char *canonical=tagged(albumartist)?albumartist:artist;
    if(key(&r,1,path,NULL,NULL)&&access_rule(&r,false)==1)return true;
    if(key(&r,2,NULL,canonical,album)&&access_rule(&r,false)==1)return true;
    if(key(&r,3,NULL,artist,NULL)&&access_rule(&r,false)==1)return true;
    return key(&r,3,NULL,canonical,NULL)&&access_rule(&r,false)==1;
}
int snarty_favorite_toggle(const struct mp3entry *track,int kind)
{
    const char *artist=kind==2&&track->albumartist&&*track->albumartist?track->albumartist:track->artist;
    struct rule r;if(!key(&r,kind,track->path,artist,track->album))return -1;
    return access_rule(&r,true);
}

#if defined(HAVE_TAGCACHE) && !defined(__PCTOOL__)
#include "tagcache.h"
#include "playlist.h"
#include "filetypes.h"
#include "settings.h"
#include "splash.h"
#include "action.h"
#include "kernel.h"
#include "audio.h"
bool snarty_favorites_shuffle(void)
{
    if(global_settings.party_mode){splash(HZ*2,"Leave Party Mode to shuffle Favorites");return false;}
    if(!tagcache_is_usable()){splash(HZ*2,"Music database is not ready");return false;}
    const char *temp=ROCKBOX_DIR "/snarty-favorites-shuffle.tmp.m3u8";
    int fd=open(temp,O_WRONLY|O_CREAT|O_TRUNC,0666);
    if(fd<0){splash(HZ*2,"Cannot prepare Favorites queue");return false;}
    static char path[MAX_PATH],artist[TAG_MAXLEN],albumartist[TAG_MAXLEN],album[TAG_MAXLEN];
    struct tagcache_search search;int count=0,scanned=0;bool ok=tagcache_search(&search,tag_filename);
    if(ok){
        splash(0,"Preparing shuffled Favorites...");
        while(tagcache_get_next(&search,path,sizeof(path))){
            if((scanned++%16)==0&&action_userabort(TIMEOUT_NOBLOCK)){ok=false;break;}
            if(!file_exists(path)||(filetype_get_attr(path)&FILE_ATTR_MASK)!=FILE_ATTR_AUDIO)continue;
            artist[0]=albumartist[0]=album[0]=0;
            tagcache_retrieve(&search,search.idx_id,tag_artist,artist,sizeof(artist));
            tagcache_retrieve(&search,search.idx_id,tag_albumartist,albumartist,sizeof(albumartist));
            tagcache_retrieve(&search,search.idx_id,tag_album,album,sizeof(album));
            if(!snarty_favorites_match(path,artist,albumartist,album))continue;
            if(fdprintf(fd,"%s\n",path)<=0){ok=false;break;}count++;
            yield();
        }
        tagcache_search_finish(&search);
    }
    if(close(fd)<0)ok=false;
    if(!ok||count==0){remove(temp);splash(HZ*2,ok?"No Favorites on the device":"Favorites shuffle cancelled or unavailable");return false;}
    if(count>playlist_get_current()->max_playlist_size){remove(temp);splash(HZ*3,"Increase Max Playlist Size for all Favorites");return false;}
    if(playlist_create(NULL,NULL)<0||playlist_insert_playlist(NULL,temp,PLAYLIST_INSERT_LAST,false)<0||playlist_amount()!=count||playlist_shuffle_all(current_tick)<0){remove(temp);splash(HZ*2,"Cannot build the complete Favorites queue");return false;}
    remove(temp);playlist_sync(NULL);playlist_start(0,0,0);return true;
}
#endif
