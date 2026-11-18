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
static bool key(struct rule *r,int kind,const char *path,const char *artist,const char *album)
{
    memset(r,0,sizeof(*r));memcpy(r->magic,"FAV1",4);r->kind=kind;
    if(kind==1)return snarty_device_path(path,r->path,sizeof(r->path));
    if(!artist||!*artist||strlen(artist)>=sizeof(r->artist))return false;
    strcpy(r->artist,artist);
    if(kind==2){if(!album||!*album||strlen(album)>=sizeof(r->album))return false;strcpy(r->album,album);}
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
    struct rule r;const char *canonical=albumartist&&*albumartist?albumartist:artist;
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
