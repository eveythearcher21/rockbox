/* Local listening-history format and ranking. Rockbox GPLv2 or later. */
#include "listening_stats.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <limits.h>

static bool valid_date(const struct listening_record *r)
{
    static const int days[]={31,28,31,30,31,30,31,31,30,31,30,31};
    if (r->year<1900 || r->year>9999 || r->month<1 || r->month>12 ||
        r->hour<0 || r->hour>23 || r->minute<0 || r->minute>59 ||
        r->second<0 || r->second>59)
        return false;
    int limit=days[r->month-1];
    if (r->month==2 && r->year%4==0 && (r->year%100!=0 || r->year%400==0))
        limit++;
    return r->day>=1 && r->day<=limit;
}

static int escaped(char *buffer, size_t size, size_t *used, const char *value, size_t limit)
{
    if (!value) value="";
    size_t take=strlen(value);
    if (take>limit) {
        take=limit;
        while (take && ((unsigned char)value[take]&0xc0)==0x80) take--;
    }
    for (size_t i=0;i<take;i++) {
        char c=value[i], replacement=0;
        if (c=='\\') replacement='\\';
        else if (c=='\t') replacement='t';
        else if (c=='\n') replacement='n';
        else if (c=='\r') replacement='r';
        size_t need=replacement?2:1;
        if (*used+need>=size) return -1;
        if (replacement) { buffer[(*used)++]='\\';buffer[(*used)++]=replacement; }
        else buffer[(*used)++]=c;
    }
    return 0;
}

int listening_record_format(char *buffer, size_t size, const struct listening_record *r)
{
    if (!valid_date(r) || !r->path || !r->path[0] ||
        strlen(r->path)>=LISTENING_PATH_SIZE || !size) return -1;
    int prefix=snprintf(buffer,size,"%04d-%02d-%02dT%02d:%02d:%02d\t%lu\t%lu",
                        r->year,r->month,r->day,r->hour,r->minute,r->second,
                        r->elapsed_ms,r->length_ms);
    if (prefix<0 || (size_t)prefix>=size) return -1;
    size_t used=prefix;
    const char *fields[]={r->path,r->title,r->artist,r->album};
    for (int i=0;i<4;i++) {
        if (used+1>=size) return -1;
        buffer[used++]='\t';
        if (escaped(buffer,size,&used,fields[i],i==0?LISTENING_PATH_SIZE-1:LISTENING_LOG_TEXT_LIMIT)<0)
            return -1;
    }
    if (used+1>=size) return -1;
    buffer[used++]='\n';buffer[used]='\0';
    return (int)used;
}

static int digits(const char *s, int count)
{
    int n=0;
    for (int i=0;i<count;i++) {
        if (s[i]<'0' || s[i]>'9') return -1;
        n=n*10+s[i]-'0';
    }
    return n;
}
static bool number(const char *s, unsigned long *value)
{
    if (!*s) return false;
    unsigned long result=0;
    for (;*s;s++) {
        if (*s<'0' || *s>'9' || result>(ULONG_MAX-(unsigned)(*s-'0'))/10) return false;
        result=result*10+*s-'0';
    }
    *value=result;return true;
}
static bool unescape(char *s)
{
    char *out=s;
    while (*s) {
        if (*s=='\\') {
            s++;
            if (*s=='t') *out++='\t';
            else if (*s=='n') *out++='\n';
            else if (*s=='r') *out++='\r';
            else if (*s=='\\') *out++='\\';
            else return false;
            s++;
        } else *out++=*s++;
    }
    *out=0;return true;
}
bool listening_record_parse(char *line, struct listening_record *r)
{
    char *field[7];field[0]=line;int count=1;
    for (char *p=line;*p;p++) {
        if (*p=='\t') {
            if (count==7) return false;
            *p=0;field[count++]=p+1;
        } else if (*p=='\n' || *p=='\r') { *p=0;break; }
    }
    if (count!=7 || strlen(field[0])!=19 || field[0][4]!='-' || field[0][7]!='-' ||
        field[0][10]!='T' || field[0][13]!=':' || field[0][16]!=':') return false;
    r->year=digits(field[0],4);r->month=digits(field[0]+5,2);r->day=digits(field[0]+8,2);
    r->hour=digits(field[0]+11,2);r->minute=digits(field[0]+14,2);r->second=digits(field[0]+17,2);
    if (!valid_date(r) || !number(field[1],&r->elapsed_ms) || !number(field[2],&r->length_ms))
        return false;
    for (int i=3;i<7;i++) if (!unescape(field[i])) return false;
    r->path=field[3];r->title=field[4];r->artist=field[5];r->album=field[6];
    return *r->path && strlen(r->path)<LISTENING_PATH_SIZE;
}
bool listening_record_matches(const struct listening_record *r, int year, int month)
{
    return r->year==year && (month==0 || r->month==month);
}
uint64_t listening_path_hash(const char *path)
{
    uint64_t hash=UINT64_C(14695981039346656037);
    while (*path) { hash^=(unsigned char)*path++;hash*=UINT64_C(1099511628211); }
    return hash;
}
bool listening_stats_add(struct listening_stat *table,size_t capacity,
                         const struct listening_record *r,uint64_t offset,
                         listening_same_path same_path,void *context)
{
    if (!capacity || (capacity&(capacity-1))) return false;
    uint64_t hash=listening_path_hash(r->path);
    size_t slot=(size_t)hash&(capacity-1);
    for (size_t i=0;i<capacity;i++,slot=(slot+1)&(capacity-1)) {
        struct listening_stat *entry=&table[slot];
        if (!entry->count) {
            entry->hash=hash;entry->offset=offset;entry->count=1;return true;
        }
        if (entry->hash==hash && same_path(context,entry->offset,r->path)) {
            if (entry->count<UINT32_MAX) entry->count++;
            return true;
        }
    }
    return false;
}
size_t listening_stats_top(const struct listening_stat *table,size_t capacity,
                          size_t result[LISTENING_TOP_COUNT])
{
    size_t count=0;
    for (size_t i=0;i<capacity;i++) {
        if (!table[i].count) continue;
        size_t position=0;
        while (position<count && (table[result[position]].count>table[i].count ||
               (table[result[position]].count==table[i].count && table[result[position]].offset<table[i].offset)))
            position++;
        if (position>=LISTENING_TOP_COUNT) continue;
        size_t end=count<LISTENING_TOP_COUNT?count:LISTENING_TOP_COUNT-1;
        for (size_t j=end;j>position;j--) result[j]=result[j-1];
        result[position]=i;
        if (count<LISTENING_TOP_COUNT) count++;
    }
    return count;
}
