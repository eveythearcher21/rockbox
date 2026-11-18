/* Constant-memory binary search of desktop-synced YouTube Music ranks. GPLv2+. */
#include "config.h"
#include <string.h>
#include <strings.h>
#include <limits.h>
#include "file.h"
#include "rbpaths.h"
#include "snarty_library.h"
#define LIBRARY_FILE ROCKBOX_DIR "/snarty/library-v1.bin"
bool snarty_device_path(const char *path,char *out,size_t size)
{
    if(!path || path[0]!='/')return false;
    const char *suffix=NULL;
    const char *aliases[]={"/storage/sdcard0/","/mnt/sdcard/","/sdcard/"};
    for(unsigned i=0;i<sizeof(aliases)/sizeof(aliases[0]);i++)
        if(!strncmp(path,aliases[i],strlen(aliases[i]))){suffix=path+strlen(aliases[i]);break;}
    size_t prefix=suffix?8:0,length=strlen(suffix?suffix:path);
    if(prefix+length>=size)return false;
    if(suffix){memcpy(out,"/sdcard/",8);memcpy(out+8,suffix,length+1);}
    else memcpy(out,path,length+1);
    return true;
}
bool snarty_device_paths_equal(const char *a,const char *b)
{
    char x[SNARTY_LIBRARY_PATH_SIZE],y[SNARTY_LIBRARY_PATH_SIZE];
    return snarty_device_path(a,x,sizeof(x))&&snarty_device_path(b,y,sizeof(y))&&!strcasecmp(x,y);
}
static uint32_t le32(const unsigned char *b)
{ return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24; }
static int open_library(uint32_t *count)
{
    int fd=open(LIBRARY_FILE,O_RDONLY);unsigned char header[16];
    if (fd<0) return -1;
    if (read(fd,header,16)!=16 || memcmp(header,"SNRTLIB1",8) ||
        le32(header+12)!=SNARTY_LIBRARY_RECORD_SIZE ||
        (*count=le32(header+8))>1000000 ||
        lseek(fd,0,SEEK_END)!=(off_t)(16+(uint64_t)*count*SNARTY_LIBRARY_RECORD_SIZE))
    {close(fd);return -1;}
    return fd;
}
bool snarty_library_available(void)
{ uint32_t count;int fd=open_library(&count);if(fd<0)return false;close(fd);return count>0; }
long snarty_library_rank(const char *path,bool album)
{
    char key[SNARTY_LIBRARY_PATH_SIZE];
    if(!snarty_device_path(path,key,sizeof(key)))return INT_MAX;
    uint32_t count;int fd=open_library(&count);long rank=INT_MAX;
    if (fd<0 || !path) {if(fd>=0)close(fd);return rank;}
    uint32_t lo=0,hi=count;unsigned char row[SNARTY_LIBRARY_RECORD_SIZE];
    while(lo<hi)
    {
        uint32_t mid=lo+(hi-lo)/2;
        if(lseek(fd,16+(off_t)mid*sizeof(row),SEEK_SET)<0 || read(fd,row,sizeof(row))!=(ssize_t)sizeof(row) ||
           !memchr(row,0,SNARTY_LIBRARY_PATH_SIZE)) break;
        int cmp=strcmp(key,(const char*)row);
        if(cmp<0)hi=mid;
        else if(cmp>0)lo=mid+1;
        else {uint32_t value=le32(row+260+(album?4:0));if(value>0&&value<INT_MAX)rank=value;break;}
    }
    close(fd);return rank;
}
