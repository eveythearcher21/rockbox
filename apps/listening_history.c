/* Local listening journal and Wrapped views. Rockbox GPLv2 or later. */
#include "config.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include "file.h"
#include "string-extra.h"
#include "kernel.h"
#include "metadata.h"
#include "timefuncs.h"
#include "rbpaths.h"
#include "misc.h"
#include "splash.h"
#include "action.h"
#include "core_alloc.h"
#include "gui/list.h"
#include "icons.h"
#include "lcd.h"
#include "settings.h"
#include "listening_history.h"
#include "listening_stats.h"

#define HISTORY_PATH ROCKBOX_DIR "/listening-history-v1.tsv"
#define PERIOD_LIMIT 2400
#define TABLE_LIMIT 65536
static const char * const month_names[]={"January","February","March","April","May","June",
    "July","August","September","October","November","December"};

static bool history_write_failed;

/* Only the serialized playback-finish callback writes this buffer. */
void listening_history_record(const struct mp3entry *id3)
{
#if CONFIG_RTC
    static char line[LISTENING_LINE_SIZE];
    struct tm now=*get_time();
    if (!valid_time(&now)) { history_write_failed=true;return; }
    struct listening_record record={
        .year=now.tm_year+1900,.month=now.tm_mon+1,.day=now.tm_mday,
        .hour=now.tm_hour,.minute=now.tm_min,.second=now.tm_sec,
        .elapsed_ms=id3->elapsed,.length_ms=id3->length,
        .path=id3->path,.title=id3->title,.artist=id3->artist,.album=id3->album,
    };
    int length=listening_record_format(line,sizeof(line),&record);
    if (length<0) { history_write_failed=true;return; }
    int fd=open(HISTORY_PATH,O_RDWR|O_CREAT|O_APPEND,0666);
    if (fd<0) { history_write_failed=true;return; }
    off_t start=lseek(fd,0,SEEK_END);
    const char *header=LISTENING_HISTORY_HEADER;
    const size_t header_length=sizeof(LISTENING_HISTORY_HEADER)-1;
    if (start==0) {
        if (write(fd,header,header_length)!=(ssize_t)header_length) {
            history_write_failed=true;ftruncate(fd,0);close(fd);return;
        }
        start=header_length;
    } else {
        char check[sizeof(LISTENING_HISTORY_HEADER)];
        lseek(fd,0,SEEK_SET);
        if (read(fd,check,header_length)!=(ssize_t)header_length || memcmp(check,header,header_length)) {
            history_write_failed=true;
            close(fd);return; /* Never rewrite an unknown file format. */
        }
        /* Repair only an interrupted final append, bounded by one valid row. */
        char c=0;off_t end=start;
        for (int n=0;end>(off_t)header_length && n<LISTENING_LINE_SIZE;n++) {
            lseek(fd,end-1,SEEK_SET);
            if (read(fd,&c,1)!=1) { history_write_failed=true;close(fd);return; }
            if (c=='\n') break;
            end--;
        }
        if (c!='\n' && end>(off_t)header_length) { history_write_failed=true;close(fd);return; }
        if (end!=start && ftruncate(fd,end)<0) { history_write_failed=true;close(fd);return; }
        start=end;
    }
    int done=0;
    while (done<length) {
        ssize_t n=write(fd,line+done,length-done);
        if (n<=0) break;
        done+=n;
    }
    if (done!=length) { history_write_failed=true;ftruncate(fd,start); }
    if (fsync(fd)<0) history_write_failed=true;
    close(fd);
#else
    (void)id3;
#endif
}

static struct {
    int periods[PERIOD_LIMIT],picker_periods[PERIOD_LIMIT],period_count;
    uint32_t plays;
    char line[LISTENING_LINE_SIZE],compare_line[LISTENING_LINE_SIZE];
    char title[LISTENING_TOP_COUNT][LISTENING_TEXT_SIZE];
    char artist[LISTENING_TOP_COUNT][LISTENING_TEXT_SIZE];
    char album[LISTENING_TOP_COUNT][LISTENING_TEXT_SIZE];
    uint32_t counts[LISTENING_TOP_COUNT];
    int top_count,selected;
} wrapped;

#ifdef HAVE_LCD_COLOR
static struct list_selection_color wrapped_colors = {
    .text_color=LCD_RGBPACK(35,34,52),
    .line_color=LCD_RGBPACK(165,230,186),
    .line_end_color=LCD_RGBPACK(162,172,205),
    .fg_color=LCD_RGBPACK(162,172,205),
    .bg_color=LCD_RGBPACK(35,34,52),
};
#endif
static void wrapped_list_init(struct simplelist_info *info,char *title,int count,void *data)
{
    simplelist_info_init(info,title,count,data);
#ifdef HAVE_LCD_COLOR
    info->selection_color=&wrapped_colors;
#endif
}

static int open_history(off_t *end)
{
    int fd=open(HISTORY_PATH,O_RDONLY);
    if (fd<0) return -1;
    char header[sizeof(LISTENING_HISTORY_HEADER)];
    size_t size=sizeof(LISTENING_HISTORY_HEADER)-1;
    if (read(fd,header,size)!=(ssize_t)size || memcmp(header,LISTENING_HISTORY_HEADER,size)) {
        close(fd);return -1;
    }
    *end=lseek(fd,0,SEEK_END);
    /* A reader never includes a partially appended row. */
    char c=0;
    for (int n=0;*end>(off_t)size && n<LISTENING_LINE_SIZE;n++) {
        lseek(fd,*end-1,SEEK_SET);
        if (read(fd,&c,1)!=1) { close(fd);return -1; }
        if (c=='\n') break;
        (*end)--;
    }
    if (c!='\n' && *end>(off_t)size) { close(fd);return -1; }
    lseek(fd,size,SEEK_SET);
    return fd;
}

static bool next_record(int fd,off_t end,off_t *offset,struct listening_record *r)
{
    while ((*offset=lseek(fd,0,SEEK_CUR))<end) {
        int length=read_line(fd,wrapped.line,sizeof(wrapped.line));
        off_t position=lseek(fd,0,SEEK_CUR);
        if (length<0 || position<=*offset || position>end) return false;
        if (!length) continue;
        if (listening_record_parse(wrapped.line,r)) return true;
    }
    return false;
}
static bool same_path(void *context,uint64_t offset,const char *path)
{
    int fd=*(int*)context;
    off_t position=lseek(fd,0,SEEK_CUR);
    lseek(fd,(off_t)offset,SEEK_SET);
    struct listening_record r;
    bool same=read_line(fd,wrapped.compare_line,sizeof(wrapped.compare_line))>0 &&
              listening_record_parse(wrapped.compare_line,&r) && !strcmp(r.path,path);
    lseek(fd,position,SEEK_SET);
    return same;
}
static int descending_period(const void *a,const void *b)
{
    int x=*(const int*)a,y=*(const int*)b;
    return x<y?1:x>y?-1:0;
}
static bool collect_periods(void)
{
    wrapped.period_count=0;wrapped.plays=0;
    off_t end,offset;
    int fd=open_history(&end);
    if (fd<0) return false;
    struct listening_record r;
    long next_yield=current_tick+HZ/2;
    while (next_record(fd,end,&offset,&r)) {
        if (wrapped.plays<UINT32_MAX) wrapped.plays++;
        int period=r.year*100+r.month,i;
        for (i=0;i<wrapped.period_count;i++) if (wrapped.periods[i]==period) break;
        if (i==wrapped.period_count) {
            if (i==PERIOD_LIMIT) { close(fd);splash(HZ*2,"Too many months; use the export file");return false; }
            wrapped.periods[wrapped.period_count++]=period;
        }
        if (TIME_AFTER(current_tick,next_yield)) {
            yield();next_yield=current_tick+HZ/2;
            if (action_userabort(TIMEOUT_NOBLOCK)) { close(fd);return false; }
        }
    }
    close(fd);
    qsort(wrapped.periods,wrapped.period_count,sizeof(wrapped.periods[0]),descending_period);
    return wrapped.period_count>0;
}

static bool load_ranking(int year,int month)
{
    off_t end,offset;
    int fd=open_history(&end);
    if (fd<0) return false;
    struct listening_record r;
    uint32_t rows=0;
    long next_update=current_tick+HZ/2;
    while (next_record(fd,end,&offset,&r)) {
        if (listening_record_matches(&r,year,month) && rows<UINT32_MAX) rows++;
        if (TIME_AFTER(current_tick,next_update)) {
            yield();next_update=current_tick+HZ/2;
            if (action_userabort(TIMEOUT_NOBLOCK)) { close(fd);return false; }
        }
    }
    if (!rows) { close(fd);return false; }
    size_t capacity=32;
    while (capacity<TABLE_LIMIT && capacity<(uint64_t)rows*2) capacity*=2;
    int handle=core_alloc(capacity*sizeof(struct listening_stat));
    if (handle<=0) { close(fd);splash(HZ*2,"Not enough memory; use the export file");return false; }
    core_pin(handle);
    struct listening_stat *table=core_get_data(handle);
    memset(table,0,capacity*sizeof(*table));
    lseek(fd,sizeof(LISTENING_HISTORY_HEADER)-1,SEEK_SET);
    bool ok=true;
    while (next_record(fd,end,&offset,&r)) {
        if (listening_record_matches(&r,year,month) &&
            !listening_stats_add(table,capacity,&r,offset,same_path,&fd)) {
            splash(HZ*2,"Too many distinct songs; use the export file");ok=false;break;
        }
        if (TIME_AFTER(current_tick,next_update)) {
            splash_progress((int)(offset/1024),(int)(end/1024+1),"Building your Wrapped");
            next_update=current_tick+HZ/2;
            if (action_userabort(TIMEOUT_NOBLOCK)) { ok=false;break; }
            yield();
        }
    }
    if (ok) {
        size_t top[LISTENING_TOP_COUNT];
        wrapped.top_count=listening_stats_top(table,capacity,top);
        for (int i=0;i<wrapped.top_count;i++) {
            lseek(fd,(off_t)table[top[i]].offset,SEEK_SET);
            if (read_line(fd,wrapped.line,sizeof(wrapped.line))<=0 ||
                !listening_record_parse(wrapped.line,&r)) { ok=false;break; }
            const char *title=r.title;
            if (!*title) { title=strrchr(r.path,'/');title=title?title+1:r.path; }
            strlcpy(wrapped.title[i],title,sizeof(wrapped.title[i]));
            strlcpy(wrapped.artist[i],*r.artist?r.artist:"Unknown Artist",sizeof(wrapped.artist[i]));
            strlcpy(wrapped.album[i],*r.album?r.album:"Unknown Album",sizeof(wrapped.album[i]));
            wrapped.counts[i]=table[top[i]].count;
        }
    }
    core_unpin(handle);core_free(handle);close(fd);
    return ok;
}

static const char *rank_name(int item,void *data,char *buffer,size_t size)
{
    (void)data;
    int rank=item/2;
    if (item%2==0) snprintf(buffer,size,"#%02d  %s",rank+1,wrapped.title[rank]);
    else snprintf(buffer,size,"%lu plays  -  %s",(unsigned long)wrapped.counts[rank],wrapped.artist[rank]);
    return buffer;
}
static int rank_action(int action,struct gui_synclist *list)
{
    if (action!=ACTION_REDRAW) wrapped.selected=gui_synclist_get_sel_pos(list)/2;
    return action;
}
#ifdef HAVE_LCD_COLOR
static int rank_color(int item,void *data)
{
    (void)data;
    if (item/2==wrapped.selected) return -1;
    return item/2==0?LCD_RGBPACK(165,230,186):LCD_RGBPACK(162,172,205);
}
#endif
static const char *detail_name(int item,void *data,char *buffer,size_t size)
{
    int rank=*(int*)data;
    if (item==0) snprintf(buffer,size,"%s",wrapped.title[rank]);
    else if (item==1) snprintf(buffer,size,"%s",wrapped.artist[rank]);
    else if (item==2) snprintf(buffer,size,"%s",wrapped.album[rank]);
    else snprintf(buffer,size,"%lu recorded plays",(unsigned long)wrapped.counts[rank]);
    return buffer;
}
static void show_ranking(int year,int month)
{
    if (!load_ranking(year,month)) return;
    char title[64];
    if (month) snprintf(title,sizeof(title),"%s %d - TOP 10",month_names[month-1],year);
    else snprintf(title,sizeof(title),"Your %d song of the year",year);
    int count=month?wrapped.top_count:1;
    int selected=0;
    for (;;) {
        struct simplelist_info info;
        wrapped_list_init(&info,title,count,NULL);
        info.selection=selected;
        wrapped.selected=selected/2;
        info.selection_size=2;info.get_name=rank_name;info.scroll_all=true;
        info.title_icon=Icon_Audio;info.action_callback=rank_action;
#ifdef HAVE_LCD_COLOR
        info.get_color=rank_color;
#endif
        if (simplelist_show_list(&info) || info.selection<0) return;
        selected=info.selection;
        int rank=info.selection/2;
        struct simplelist_info detail;
        wrapped_list_init(&detail,"Your listening",4,&rank);
        detail.get_name=detail_name;detail.scroll_all=true;
        if (simplelist_show_list(&detail)) return;
    }
}
static const char *period_name(int item,void *data,char *buffer,size_t size)
{
    int *periods=data,period=periods[item];
    if (period%100) snprintf(buffer,size,"%s %d",month_names[period%100-1],period/100);
    else snprintf(buffer,size,"%d - Song of the year",period/100);
    return buffer;
}
static void pick_period(bool yearly)
{
    int *periods=wrapped.picker_periods,count=0,last_year=-1;
    for (int i=0;i<wrapped.period_count;i++) {
        int year=wrapped.periods[i]/100;
        if (!yearly) periods[count++]=wrapped.periods[i];
        else if (year!=last_year) { periods[count++]=year*100;last_year=year; }
    }
    int selected=0;
    for (;;) {
        struct simplelist_info info;
        wrapped_list_init(&info,yearly?"Your years":"Your months",count,periods);
        info.selection=selected;
        info.get_name=period_name;info.title_icon=Icon_Audio;
        if (simplelist_show_list(&info) || info.selection<0) return;
        selected=info.selection;
        show_ranking(periods[info.selection]/100,periods[info.selection]%100);
    }
}
static const char *home_name(int item,void *data,char *buffer,size_t size)
{
    (void)data;
    if (item==0) snprintf(buffer,size,"Monthly Top 10 - %d months",wrapped.period_count);
    else if (item==1) snprintf(buffer,size,"Song of the Year");
    else snprintf(buffer,size,"Sync / export data");
    return buffer;
}
static const char *export_name(int item,void *data,char *buffer,size_t size)
{
    (void)data;
    const char *lines[]={"Local listening history (TSV v1)",".rockbox/listening-history-v1.tsv",
        "Copy this file to your sync app","Device-local timestamps; no cloud upload",
        "History starts with this update","Gather Runtime Data must be enabled",
        "Keep the player's date and time correct",
        "Plays appear when a track ends or changes"};
    strlcpy(buffer,lines[item],size);return buffer;
}
void listening_history_show(void)
{
    bool has_history=collect_periods();
    if (history_write_failed)
        splash(HZ*3,"Some plays were not recorded. Check the clock and free storage.");
    if (!has_history) splash(HZ*3,"No recorded plays yet. Enable Gather Runtime Data and check the clock.");
    for (;;) {
        struct simplelist_info info;
        wrapped_list_init(&info,"spotify wrapped - on this player",3,NULL);
        info.get_name=home_name;info.title_icon=Icon_Audio;
        if (simplelist_show_list(&info) || info.selection<0) return;
        if (info.selection<2) {
            has_history=collect_periods(); /* Include plays completed since opening this screen. */
            if (has_history) pick_period(info.selection==1);
            else splash(HZ*2,"Play indexed songs with Gather Runtime Data enabled");
        } else {
            struct simplelist_info help;
            wrapped_list_init(&help,"Sync / export",8,NULL);
            help.get_name=export_name;help.scroll_all=true;
            if (simplelist_show_list(&help)) return;
        }
    }
}
