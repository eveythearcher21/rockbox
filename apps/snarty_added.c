/* Bounded, collision-checked disk hash index; no audio-directory sidecars. GPLv2+. */
#include "config.h"
#include <string.h>
#include <stdio.h>
#include <limits.h>
#include "file.h"
#include "dir.h"
#include "rbpaths.h"
#include "snarty_library.h"
#include "snarty_added.h"
#define INDEX ROCKBOX_DIR "/snarty-device-added-v1.bin"
#define SLOTS 65536U
#define ROW 268
static uint32_t hash_path(const char *p){uint32_t h=2166136261U;while(*p){h^=(unsigned char)*p++;h*=16777619U;}return h;}
static uint32_t le32(const unsigned char*b){return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;}
static uint32_t lookup(const char *path,uint32_t date)
{
    char key[260];if(!snarty_device_path(path,key,sizeof(key)))return date;
    int fd=open(INDEX,date?O_RDWR|O_CREAT:O_RDONLY,0666);if(fd<0)return date;
    uint32_t hash=hash_path(key),result=date;unsigned char row[ROW];
    for(unsigned i=0;i<256;i++){
        off_t at=(off_t)((hash+i)%SLOTS)*ROW;
        if(lseek(fd,at,SEEK_SET)<0)break;
        ssize_t size=read(fd,row,ROW);
        if(size==0||(size==ROW&&row[0]==0)){
            if(date){memset(row,0,ROW);memcpy(row,"ADD1",4);row[4]=date;row[5]=date>>8;row[6]=date>>16;row[7]=date>>24;memcpy(row+8,key,strlen(key)+1);lseek(fd,at,SEEK_SET);write(fd,row,ROW);}
            break;
        }
        if(size!=ROW||memcmp(row,"ADD1",4)||!memchr(row+8,0,260))break;
        if(!strcmp((char*)row+8,key)){result=le32(row+4);break;}
    }
    close(fd);return result;
}
void snarty_added_observe(const char *path,uint32_t date)
{if(date>0&&date<INT_MAX)lookup(path,date);}
long snarty_added_rank(const char *path,uint32_t fallback)
{
    uint32_t date=lookup(path,0);
    if(!date&&fallback){snarty_added_observe(path,fallback);date=fallback;}
    if(!date){
        char parent[260];if(!snarty_device_path(path,parent,sizeof(parent)))return INT_MAX;
        /* Use the original indexed path for virtual-filesystem directory access. */
        if(strlen(path)>=sizeof(parent))return INT_MAX;
        strcpy(parent,path);
        char *name=strrchr(parent,'/');if(!name)return INT_MAX;char base[260];strcpy(base,name+1);if(name==parent)name[1]=0;else *name=0;
        DIR *dir=opendir(parent);if(dir){struct dirent*entry;while((entry=readdir(dir)))if(!strcmp(entry->d_name,base)){struct dirinfo info=dir_get_info(dir,entry);if(info.mtime>0&&info.mtime<INT_MAX)date=info.mtime;break;}closedir(dir);}
        if(date)snarty_added_observe(path,date);
    }
    return date&&date<INT_MAX?1000000000L+(INT_MAX-date)/4:INT_MAX;
}
