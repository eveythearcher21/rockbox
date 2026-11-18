/* Album card/cover transition renderer. GPLv2 or later. */
#include "config.h"
#include "snarty_albums.h"
#ifdef HAVE_SNARTY_NAVIGATION
#include <string.h>
#include <stdio.h>
#include "string-extra.h"
#include <strings.h>
#include "tree.h"
#include "filetypes.h"
#include "tagtree.h"
#include "gui/list.h"
#include "gui/line.h"
#include "viewport.h"
#include "screen_access.h"
#include "font.h"
#include "icons.h"
#include "file.h"
#include "dir.h"
#include "kernel.h"
#include "metadata.h"
#include "misc.h"
#include "pathfuncs.h"
#include "recorder/albumart.h"
#include "recorder/bmp.h"
#include "recorder/jpeg_load.h"
#include "rbpaths.h"
#define BG LCD_RGBPACK(35,34,52)
#define MINT LCD_RGBPACK(165,230,186)
#define LAVENDER LCD_RGBPACK(162,172,205)
#define THUMB 80
#define LARGE 200
#define CACHE 6
static int px(int n){return (n*LCD_WIDTH+240)/480;}
struct cover {bool valid,art;struct snarty_album_info info;fb_data pixels[THUMB*THUMB];};
static struct cover covers[CACHE];static unsigned replace_slot;
static struct snarty_album_info detail_info;
static fb_data detail_pixels[LARGE*LARGE],scaled[LARGE*LARGE];
static unsigned char decode_buffer[512*1024];
static struct mp3entry metadata;
static bool detail_valid,detail_art,theme_disabled,file_cards;
static int selected_x,selected_y,selected_size;
static struct viewport tracks_vp,normal_vp;
static int big_font=-1,small_font=-1,normal_font=-1;
static fb_data pixel(const fb_data *data,int w,int h,int x,int y)
{
#if LCD_STRIDEFORMAT == VERTICAL_STRIDE
    (void)w;return data[x*h+y];
#else
    (void)h;return data[y*w+x];
#endif
}
static void store(fb_data*data,int w,int h,int x,int y,fb_data color)
{
#if LCD_STRIDEFORMAT == VERTICAL_STRIDE
    (void)w;data[x*h+y]=color;
#else
    (void)h;data[y*w+x]=color;
#endif
}
static bool load_cover(const struct snarty_album_info *info,fb_data *out,int side);
static bool named_image(const char *directory,const char *name,char *out,size_t size,bool converted)
{
    const char *extensions[]={".jpg",".jpeg",".bmp",".png",".webp"};
    char filename[TAG_MAXLEN+8];
    for(int i=converted?3:0;i<(converted?5:3);i++){
        if(snprintf(filename,sizeof(filename),"%s%s",name,extensions[i])>=(int)sizeof(filename))continue;
        if(path_append(out,directory,filename,size)<size&&file_exists(out))return true;
    }
    DIR *dir=opendir(directory);if(!dir)return false;struct dirent *entry;bool found=false;
    while((entry=readdir(dir))){
        const char *dot=strrchr(entry->d_name,'.');if(!dot||(size_t)(dot-entry->d_name)!=strlen(name)||strncasecmp(entry->d_name,name,strlen(name)))continue;
        bool native=!strcasecmp(dot,".jpg")||!strcasecmp(dot,".jpeg")||!strcasecmp(dot,".bmp");
        bool other=!strcasecmp(dot,".png")||!strcasecmp(dot,".webp");
        if((converted?other:native)&&path_append(out,directory,entry->d_name,size)<size){found=true;break;}
    }
    closedir(dir);return found;
}
static bool artist_image(const char *artist,char *out,size_t size)
{
    char name[TAG_MAXLEN];strlcpy(name,artist,sizeof(name));
    for(char *p=name;*p;p++)if(strchr("/\\:*?\"<>|",*p))*p='_';
#ifdef INNIOASIS_Y1
    const char *directory="/sdcard/Artist_Images";
#else
    const char *directory="/Artist_Images";
#endif
    if(named_image(directory,name,out,size,false))return true;
    char original[MAX_PATH];
    return named_image(directory,name,original,sizeof(original),true)&&named_image(ROCKBOX_DIR "/snarty/artist-images",name,out,size,false);
}
static bool playlist_cover(const char *playlist,fb_data *out,int side)
{
    int fd=open(playlist,O_RDONLY);if(fd<0)return false;
    static struct mp3entry entry;
    static fb_data tile[LARGE*LARGE];
    static char keys[4][TAG_MAXLEN*2+2];
    struct snarty_album_info info;char line[MAX_PATH+4],base[MAX_PATH],path[MAX_PATH];
    strlcpy(base,playlist,sizeof(base));char *slash=strrchr(base,'/');if(slash==base)base[1]=0;else if(slash)*slash=0;else strlcpy(base,"/",sizeof(base));
    int count=0,scanned=0,half=side/2;
    for(int y=0;y<side;y++)for(int x=0;x<side;x++)store(out,side,side,x,y,BG);
    while(count<4&&scanned++<2048&&read_line(fd,line,sizeof(line))>0){
        char *name=line;if(!strncmp(name,"\xef\xbb\xbf",3))name+=3;
        if(!*name||name[0]=='#'||strstr(name,"://"))continue;
        if(name[0]=='/'){if(strlcpy(path,name,sizeof(path))>=sizeof(path))continue;}
        else if(path_append(path,base,name,sizeof(path))>=sizeof(path))continue;
        path_remove_dot_segments(path,path);
        if((filetype_get_attr(path)&FILE_ATTR_MASK)!=FILE_ATTR_AUDIO||!file_exists(path)||!get_metadata(&entry,-1,path))continue;
        char key[TAG_MAXLEN*2+2];snprintf(key,sizeof(key),"%s\t%s",entry.albumartist&&*entry.albumartist?entry.albumartist:entry.artist?entry.artist:"",entry.album&&*entry.album?entry.album:path);
        bool duplicate=false;for(int i=0;i<count;i++)if(!strcasecmp(key,keys[i]))duplicate=true;
        if(duplicate)continue;
        memset(&info,0,sizeof(info));strlcpy(info.path,path,sizeof(info.path));strlcpy(info.title,entry.album?entry.album:"",sizeof(info.title));strlcpy(info.artist,entry.albumartist?entry.albumartist:entry.artist?entry.artist:"",sizeof(info.artist));
        if(!load_cover(&info,tile,half))continue;
        strlcpy(keys[count],key,sizeof(keys[0]));int left=(count%2)*half,top=(count/2)*half;
        for(int y=0;y<half;y++)for(int x=0;x<half;x++)store(out,side,side,left+x,top+y,pixel(tile,half,half,x,y));
        count++;yield();
    }
    close(fd);return count>0;
}
static bool load_cover(const struct snarty_album_info *info,fb_data *out,int side)
{
    if(info->kind==4)return playlist_cover(info->path,out,side);
    memset(&metadata,0,sizeof(metadata));strlcpy(metadata.path,info->path,sizeof(metadata.path));
    metadata.album=(char*)info->title;metadata.artist=metadata.albumartist=(char*)info->artist;
    char cover[MAX_PATH];struct dim dim={LARGE,LARGE};
    struct bitmap bitmap;memset(&bitmap,0,sizeof(bitmap));bitmap.width=bitmap.height=side;bitmap.data=decode_buffer;
    const int format=FORMAT_NATIVE|FORMAT_RESIZE|FORMAT_KEEP_ASPECT;int result=-1;
    if(info->kind==2)
    {
        if(!artist_image(info->title,cover,sizeof(cover)))snprintf(cover,sizeof(cover),"%s.artist.jpg",info->path);
        if(!file_exists(cover)){
            strlcpy(cover,info->path,sizeof(cover));char *slash=strrchr(cover,'/');
            if(slash)strlcpy(slash+1,"artist.jpg",sizeof(cover)-(slash+1-cover));
        }
        if(file_exists(cover)){const char *ext=strrchr(cover,'.');result=ext&&!strcasecmp(ext,".bmp")?read_bmp_file(cover,&bitmap,sizeof(decode_buffer),format,NULL):read_jpeg_file(cover,&bitmap,sizeof(decode_buffer),format,NULL);}
    }
    else if(find_albumart(&metadata,cover,sizeof(cover),&dim))
    {
        const char *ext=strrchr(cover,'.');
        result=ext&&!strcasecmp(ext,".bmp")?read_bmp_file(cover,&bitmap,sizeof(decode_buffer),format,NULL):
            read_jpeg_file(cover,&bitmap,sizeof(decode_buffer),format,NULL);
    }
    else if(get_metadata(&metadata,-1,info->path)&&metadata.has_embedded_albumart&&
            (metadata.albumart.type&AA_CLEAR_FLAGS_MASK)==AA_TYPE_JPG)
    {
        int fd=open(info->path,O_RDONLY);
        if(fd>=0){lseek(fd,metadata.albumart.pos,SEEK_SET);result=clip_jpeg_fd(fd,metadata.albumart.type,metadata.albumart.size,&bitmap,sizeof(decode_buffer),format,NULL);close(fd);}
    }
    for(int y=0;y<side;y++)for(int x=0;x<side;x++)store(out,side,side,x,y,BG);
    if(result<=0||bitmap.width<=0||bitmap.height<=0||bitmap.width>side||bitmap.height>side)return false;
    int left=(side-bitmap.width)/2,top=(side-bitmap.height)/2;
    for(int y=0;y<bitmap.height;y++)for(int x=0;x<bitmap.width;x++)store(out,side,side,left+x,top+y,pixel((fb_data*)bitmap.data,bitmap.width,bitmap.height,x,y));
    return true;
}
static void paint_cover(const fb_data*data,int original,int x,int y,int side,bool art)
{
    if(side<=0||side>LARGE)return;
    if(!art)
    {
        lcd_set_foreground(LAVENDER);lcd_drawrect(x,y,side,side);
        lcd_putsxy(x+side/4,y+side/2,"?");return;
    }
    for(int dy=0;dy<side;dy++)for(int dx=0;dx<side;dx++)store(scaled,side,side,dx,dy,pixel(data,original,original,dx*original/side,dy*original/side));
    lcd_bitmap(scaled,x,y,side,side);
}
static struct cover*card(struct tree_context *tree,int item)
{
    static struct snarty_album_info info;
    if(file_cards)
    {
        memset(&info,0,sizeof(info));tree_lock_cache(tree);
        struct entry *entry=tree_get_entry_at(tree,item);
        if(!entry){tree_unlock_cache(tree);return NULL;}
        strlcpy(info.title,entry->name,sizeof(info.title));
        snprintf(info.path,sizeof(info.path),"%s/%s",tree->currdir,entry->name);
        bool directory=entry->attr&ATTR_DIRECTORY;bool playlist=(entry->attr&FILE_ATTR_MASK)==FILE_ATTR_M3U;tree_unlock_cache(tree);
        if(playlist)info.kind=4;
        if(directory){strlcat(info.path,"/episode.mp3",sizeof(info.path));strlcpy(info.artist,"Open collection",sizeof(info.artist));}
        else {strlcpy(info.artist,playlist?"Playlist":"Media",sizeof(info.artist));
            if(!playlist&&get_metadata(&metadata,-1,info.path)){
                if(metadata.title)strlcpy(info.title,metadata.title,sizeof(info.title));
                if(metadata.artist)strlcpy(info.artist,metadata.artist,sizeof(info.artist));
            }
        }
    }
    else if(!tagtree_album_info(tree,item,&info))return NULL;
    for(int i=0;i<CACHE;i++)if(covers[i].valid&&covers[i].info.kind==info.kind&&!strcmp(covers[i].info.title,info.title)&&!strcmp(covers[i].info.path,info.path))return &covers[i];
    struct cover *c=&covers[replace_slot++%CACHE];c->info=info;
    c->art=load_cover(&info,c->pixels,THUMB);c->valid=true;return c;
}
static void prepare_detail(struct tree_context*tree)
{
    static struct snarty_album_info info;
    if(!tagtree_album_info(tree,tree->special_entry_count,&info))return;
    if(detail_valid&&!strcmp(detail_info.title,info.title)&&!strcmp(detail_info.artist,info.artist))return;
    detail_info=info;detail_art=load_cover(&detail_info,detail_pixels,LARGE);detail_valid=true;
}
static void detail_background(void)
{
    struct viewport *old=lcd_set_viewport(NULL);lcd_set_background(BG);lcd_clear_display();
    lcd_set_foreground(MINT);lcd_setfont(screens[SCREEN_MAIN].getuifont());lcd_putsxy(px(20),px(12),"Album");
    paint_cover(detail_pixels,LARGE,px(20),px(40),px(64),detail_valid&&detail_art);
    struct viewport info;viewport_set_defaults(&info,SCREEN_MAIN);
    info.x=px(104);info.y=px(40);info.width=LCD_WIDTH-px(124);info.height=px(64);lcd_set_viewport(&info);
    lcd_set_foreground(MINT);lcd_setfont(big_font>=0?big_font:screens[SCREEN_MAIN].getuifont());
    lcd_putsxy(0,0,detail_valid?detail_info.title:"Album");
    lcd_setfont(screens[SCREEN_MAIN].getuifont());lcd_set_foreground(LAVENDER);
    lcd_putsxy(0,px(36),detail_valid?detail_info.artist:"");
    lcd_set_viewport(old);
}
static void album_draw(struct list_putlineinfo_t *info)
{
    struct screen *display=info->display;struct tree_context *tree=info->list->data;
    if(display->screen_type!=SCREEN_MAIN||info->is_title)
    {display->put_line(info->x,info->y,info->linedes,"$t",info->dsp_text);return;}
    if(!file_cards&&tagtree_is_album_tracks(tree))
    {
        if(info->line==info->list->start_item[SCREEN_MAIN])detail_background();
        snarty_draw_list_item(info);return;
    }
    // Copy movable list text before metadata/cover reads can yield.
    char title[TAG_MAXLEN];strlcpy(title,info->dsp_text,sizeof(title));
    if(!file_cards&&info->line<tree->special_entry_count)
    {snarty_draw_list_item(info);return;}
    struct cover *c=card(tree,info->line);
    int height=info->linedes->height,side=MAX(px(16),height-px(info->is_selected?4:12));
    if(info->is_selected){lcd_set_foreground(LCD_RGBPACK(48,46,67));lcd_fillrect(0,info->y,info->vp->width,height);lcd_set_foreground(MINT);lcd_fillrect(0,info->y,px(3),height);}
    paint_cover(c?c->pixels:NULL,THUMB,px(4),info->y+(height-side)/2,side,c&&c->art);
    if(info->is_selected){selected_x=info->vp->x+px(4);selected_y=info->vp->y+info->y+(height-side)/2;selected_size=side;}
    int ui=screens[SCREEN_MAIN].getuifont();
    int chosen=info->is_selected?ui:(normal_font>=0?normal_font:ui),small=small_font>=0?small_font:ui;
    int title_h=font_get(chosen)->height,artist_h=font_get(small)->height;
    int top=info->y+MAX(0,(height-title_h-artist_h-px(3))/2),left=height+px(8);
    lcd_set_foreground(info->is_selected?MINT:LAVENDER);lcd_setfont(chosen);
    if(info->is_selected){
        struct line_desc line=LINE_DESC_DEFINIT;line.height=title_h;line.style=STYLE_COLORBAR|STYLE_COLORED;line.line_color=LCD_RGBPACK(48,46,67);line.text_color=MINT;line.scroll=true;
        font_lock(ui,true);display->put_line(left,top,&line,"$t",title);font_lock(ui,false);
    }else lcd_putsxy(left,top,title);
    lcd_set_foreground(LAVENDER);lcd_setfont(small);
    lcd_putsxy(left,top+title_h+px(3),c?(c->info.kind==2?"Artist":c->info.artist):"Unknown Artist");
    lcd_setfont(ui);
}
void snarty_cards_prepare_draw(struct gui_synclist *list)
{
    if(list->callback_draw_item!=album_draw||file_cards)return;
    struct tree_context *tree=list->data;
    if(list->selected_item==tree->special_entry_count&&list->selected_item<list->nb_items){
        list->start_item[SCREEN_MAIN]=list->selected_item;
#ifdef HAVE_TOUCHSCREEN
        list->y_pos=list->selected_item*list->line_height[SCREEN_MAIN];
#endif
    }
}
extern bool list_display_title(struct gui_synclist *list,enum screen_type screen);
int snarty_card_row_height(struct gui_synclist *list)
{
    if(list->callback_draw_item!=album_draw)return 0;
    int rows=!file_cards&&tagtree_is_album_tracks((struct tree_context*)list->data)?8:(list_display_title(list,SCREEN_MAIN)?6:5);
    return MAX(1,list->parent[SCREEN_MAIN]->height/rows);
}
void snarty_albums_leave(void)
{
    if(theme_disabled){viewportmanager_theme_undo(SCREEN_MAIN,false);theme_disabled=false;}
}
void snarty_albums_configure(struct gui_synclist *list,struct tree_context *tree)
{
    file_cards=false;
    for(int i=0;i<CACHE;i++)if(covers[i].info.kind==2||covers[i].info.kind==4)covers[i].valid=false;
    bool albums=tagtree_card_kind(tree)>0,tracks=tagtree_is_album_tracks(tree);
    if(!tracks&&theme_disabled)
    {
        snarty_albums_leave();viewport_set_defaults(&normal_vp,SCREEN_MAIN);list->parent[SCREEN_MAIN]=&normal_vp;
    }
    if(!albums&&!tracks)return;
    if(small_font<0)small_font=font_load(ROCKBOX_DIR "/fonts/12-KodeMono-SemiBold.fnt");
    if(normal_font<0)normal_font=font_load(LCD_WIDTH>=480?ROCKBOX_DIR "/fonts/15-KodeMono-SemiBold.fnt":ROCKBOX_DIR "/fonts/12-KodeMono-SemiBold.fnt");
    if(big_font<0)big_font=font_load(LCD_WIDTH>=480?ROCKBOX_DIR "/fonts/29-KodeMono-SemiBold.fnt":ROCKBOX_DIR "/fonts/22-KodeMono-SemiBold.fnt");
    list->callback_draw_item=album_draw;
    if(albums&&!tracks){list->line_height[SCREEN_MAIN]=MAX(1,list->parent[SCREEN_MAIN]->height/(list_display_title(list,SCREEN_MAIN)?6:5));}
    else
    {
        prepare_detail(tree);
        if(!theme_disabled){viewportmanager_theme_enable(SCREEN_MAIN,false,NULL);theme_disabled=true;}
        viewport_set_defaults(&tracks_vp,SCREEN_MAIN);
        tracks_vp.x=px(20);tracks_vp.y=px(114);tracks_vp.width=LCD_WIDTH-px(40);tracks_vp.height=LCD_HEIGHT-px(124);
        list->parent[SCREEN_MAIN]=&tracks_vp;gui_synclist_set_title(list,NULL,Icon_NOICON);
        list->line_height[SCREEN_MAIN]=MAX(1,tracks_vp.height/8);
        detail_background();
    }
}
void snarty_media_configure(struct gui_synclist *list,struct tree_context *tree)
{
    file_cards=*tree->dirfilter==SHOW_M3U||strstr(tree->currdir,"/Videos")||strstr(tree->currdir,"/Podcasts")||strstr(tree->currdir,"/Playlists");
    if(!file_cards)return;
    for(int i=0;i<CACHE;i++)if(covers[i].info.kind==4)covers[i].valid=false;
    if(small_font<0)small_font=font_load(ROCKBOX_DIR "/fonts/12-KodeMono-SemiBold.fnt");
    if(normal_font<0)normal_font=font_load(LCD_WIDTH>=480?ROCKBOX_DIR "/fonts/15-KodeMono-SemiBold.fnt":ROCKBOX_DIR "/fonts/12-KodeMono-SemiBold.fnt");
    list->callback_draw_item=album_draw;list->line_height[SCREEN_MAIN]=MAX(1,list->parent[SCREEN_MAIN]->height/(list_display_title(list,SCREEN_MAIN)?6:5));
}
void snarty_album_open(struct tree_context *tree)
{
    if(!tagtree_card_kind(tree)||tree->selected_item<tree->special_entry_count)return;
    struct cover *c=card(tree,tree->selected_item);if(!c)return;
    detail_info=c->info;detail_art=load_cover(&detail_info,detail_pixels,LARGE);detail_valid=true;
    struct viewport *old=lcd_set_viewport(NULL);snarty_snapshot_current();
    int from_size=selected_size>0?selected_size:px(72);
    for(int frame=0;frame<=8;frame++)
    {
        int t=frame*256/8;t=t*t*(768-2*t)/65536;
        bool album=tagtree_is_album_view(tree);
        int x=selected_x+(px(20)-selected_x)*t/256,y=selected_y+(px(album?40:70)-selected_y)*t/256;
        int side=from_size+(px(album?64:200)-from_size)*t/256;
        snarty_snapshot_restore();paint_cover(detail_pixels,LARGE,x,y,side,detail_art);lcd_update();sleep(MAX(1,HZ/50));
    }
    lcd_set_viewport(old);
}
#endif
