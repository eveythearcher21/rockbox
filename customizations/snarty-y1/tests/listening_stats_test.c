/* Exercises the actual journal codec, calendar filters and ranking code. */
#include "listening_stats.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>

static const char *paths[100];
static bool same(void *context,uint64_t offset,const char *path)
{
    (void)context;return !strcmp(paths[offset],path);
}
static struct listening_record record(const char *path,int year,int month)
{
    struct listening_record r={.year=year,.month=month,.day=1,.hour=12,.minute=30,.second=45,
        .elapsed_ms=180000,.length_ms=180000,.path=path,.title="Song",.artist="Artist",.album="Album"};
    return r;
}
static void round_trip(void)
{
    char line[LISTENING_LINE_SIZE];
    struct listening_record r=record("/Music/é\\song\t.flac",2024,2),parsed;
    r.day=29;r.title="Line 1\nLine 2\twith\\slashes";r.artist="Björk";r.album="";
    int n=listening_record_format(line,sizeof(line),&r);
    assert(n>0 && line[n-1]=='\n');
    assert(listening_record_parse(line,&parsed));
    assert(parsed.year==2024 && parsed.month==2 && parsed.day==29);
    assert(!strcmp(parsed.path,r.path) && !strcmp(parsed.title,r.title));
    assert(!strcmp(parsed.artist,r.artist) && !strcmp(parsed.album,""));
    assert(parsed.elapsed_ms==180000 && parsed.length_ms==180000);
    r.year=2023;assert(listening_record_format(line,sizeof(line),&r)<0);
    r.year=2024;r.month=13;assert(listening_record_format(line,sizeof(line),&r)<0);
    r.month=2;r.day=29;assert(listening_record_format(line,10,&r)<0);
    char utf8[1200];for (int i=0;i<599;i++){utf8[i*2]=(char)0xc3;utf8[i*2+1]=(char)0xa9;}utf8[1198]=0;
    r.title=utf8;assert(listening_record_format(line,sizeof(line),&r)>0);
    assert(listening_record_parse(line,&parsed));assert(strlen(parsed.title)==512);
    assert((unsigned char)parsed.title[511]==0xa9);
    char bad[]="2024-02-30T12:30:45\t10\t20\t/a\tx\ty\tz";
    assert(!listening_record_parse(bad,&parsed));
    char broken_escape[]="2024-02-29T12:30:45\t10\t20\t/a\tx\ty\tz\\q";
    assert(!listening_record_parse(broken_escape,&parsed));
    char bad_number[]="2024-02-29T12:30:45\t-1\t20\t/a\tx\ty\tz";
    assert(!listening_record_parse(bad_number,&parsed));
    char partial[]="2024-02-29T12:30:45\t10\t20\t/a\tx\ty";
    assert(!listening_record_parse(partial,&parsed));
}
static void months_and_years(void)
{
    struct listening_stat january[32]={0},february[32]={0},year[32]={0};
    const char *event_paths[]={"/a","/b","/a","/b","/b","/c","/a"};
    int years[]={2025,2025,2025,2025,2025,2025,2024};
    int months[]={1,1,1,2,2,2,1};
    for (int i=0;i<7;i++) {
        paths[i]=event_paths[i];struct listening_record r=record(paths[i],years[i],months[i]);
        if (listening_record_matches(&r,2025,1)) assert(listening_stats_add(january,32,&r,i,same,NULL));
        if (listening_record_matches(&r,2025,2)) assert(listening_stats_add(february,32,&r,i,same,NULL));
        if (listening_record_matches(&r,2025,0)) assert(listening_stats_add(year,32,&r,i,same,NULL));
    }
    size_t top[10];
    assert(listening_stats_top(january,32,top)==2);
    assert(january[top[0]].count==2 && !strcmp(paths[january[top[0]].offset],"/a"));
    assert(listening_stats_top(february,32,top)==2);
    assert(february[top[0]].count==2 && !strcmp(paths[february[top[0]].offset],"/b"));
    assert(listening_stats_top(year,32,top)==3);
    assert(year[top[0]].count==3 && !strcmp(paths[year[top[0]].offset],"/b"));
    assert(year[top[1]].count==2 && !strcmp(paths[year[top[1]].offset],"/a"));
}
static void top_ten_and_collisions(void)
{
    struct listening_stat table[64]={0};char names[15][20];
    for (int i=0;i<15;i++) {
        snprintf(names[i],sizeof(names[i]),"/song-%d",i);paths[i]=names[i];
        struct listening_record r=record(paths[i],2025,3);
        for (int j=0;j<=i;j++) assert(listening_stats_add(table,64,&r,i,same,NULL));
    }
    size_t top[10];assert(listening_stats_top(table,64,top)==10);
    for (int i=0;i<10;i++) assert(table[top[i]].count==(uint32_t)(15-i));
    struct listening_stat collision[2]={0};paths[20]="/not-the-same-song";paths[21]="/actual-song";
    struct listening_record r=record(paths[21],2025,3);
    size_t slot=listening_path_hash(r.path)&1;
    collision[slot].hash=listening_path_hash(r.path);collision[slot].count=4;collision[slot].offset=20;
    assert(listening_stats_add(collision,2,&r,21,same,NULL));
    assert(collision[slot].count==4 && collision[slot^1].count==1);
    paths[22]="/third-song";r.path=paths[22];assert(!listening_stats_add(collision,2,&r,22,same,NULL));
    collision[slot].count=UINT32_MAX;r.path=paths[20];collision[slot].hash=listening_path_hash(r.path);
    assert(listening_stats_add(collision,2,&r,20,same,NULL));assert(collision[slot].count==UINT32_MAX);
    struct listening_stat empty[2]={0};assert(listening_stats_top(empty,2,top)==0);
}
int main(void)
{
    round_trip();months_and_years();top_ten_and_collisions();
    puts("PASS: journal round-trip/UTF-8, invalid records, month/year boundaries, top ten, collisions, full table and saturation");
    return 0;
}
