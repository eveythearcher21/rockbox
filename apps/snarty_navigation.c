/* SNARTY menu renderer and nonblocking selection animation. GPLv2 or later. */
#include "config.h"
#include "snarty_navigation.h"
#ifdef HAVE_SNARTY_NAVIGATION
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "lcd.h"
#include "scroll_engine.h"
#include "screen_access.h"
#include "font.h"
#include "rbunicode.h"
#include "kernel.h"
#include "action.h"
#include "misc.h"
#include "settings.h"
#include "viewport.h"
#include "powermgmt.h"
#include "talk.h"
#include "gui/list.h"
#include "gui/line.h"
#include "icons.h"
#include "snarty_gesture.h"
#include "snarty_favorites.h"

#define BG LCD_RGBPACK(35,34,52)
#define CARD LCD_RGBPACK(48,46,67)
#define MINT LCD_RGBPACK(165,230,186)
#define LAVENDER LCD_RGBPACK(162,172,205)
static int px(int value) { return (value * LCD_WIDTH + 240) / 480; }
static int eased(int elapsed, int ticks)
{
    int t = MIN(256, MAX(0, elapsed * 256 / ticks));
    return t*t*(768-2*t)/65536;
}
/* Font bitmaps are bounded by font_get_width/height. Theme fonts may be mono
 * or 4-bit alpha; thresholding matches SNARTY's crisp bitmap icon style. */
static void label_font(const char *text, int x, int y, int height, int maxwidth, int font_id)
{
    // FONT_UI is a lookup sentinel, not a pinnable allocation ID. Resolve it
    // before cache I/O; audio buffering may compact the core allocator.
    if (font_id == FONT_UI) font_id = screens[SCREEN_MAIN].getuifont();
    font_lock(font_id,true);
    struct font *font = font_get(font_id);
    for (; *text && maxwidth > 0;)
    {
        ucschar_t ch;
        text=(const char*)utf8decode((const unsigned char*)text,&ch);
        int source_w = font_get_width(font, ch);
        int width = MAX(1, source_w * height / font->height);
        if (width > maxwidth) break;
        const unsigned char *bits = font_get_bits(font, ch);
        for (int dy=0; dy<height; dy++)
        {
            int sy=dy*font->height/height, run=-1;
            for (int dx=0; dx<=width; dx++)
            {
                int sx=dx*source_w/width;
                bool ink=false;
                if (dx<width)
                {
                    if (font->depth == 0) ink=(bits[(sy/8)*source_w+sx]>>(sy%8))&1;
                    else { int n=sy*source_w+sx;ink=((bits[n/2]>>((n%2)*4))&15)<8; }
                }
                if (ink && run<0) run=dx;
                if (!ink && run>=0) { lcd_hline(x+run,x+dx-1,y+dy);run=-1; }
            }
        }
        x+=width;maxwidth-=width;
    }
    font_lock(font_id,false);
}
static void label(const char *text,int x,int y,int height,int maxwidth)
{
    label_font(text,x,y,height,maxwidth,FONT_UI);
}
static void fixed_label(const char *text,int x,int y,int height,int maxwidth)
{
    label_font(text,x,y,height,maxwidth,FONT_SYSFIXED);
}
void snarty_draw_label(const char *text,int x,int y,int height,int maxwidth)
{ label(text,x,y,height,maxwidth); }
/* Shared list treatment covers settings, filters, playlist/catalog and media
 * browsers without changing their actions or stealing their callback data. */
void snarty_draw_list_item(struct list_putlineinfo_t *info)
{
    if(info->display->screen_type!=SCREEN_MAIN)return;
    int y=info->y,h=info->linedes->height,w=info->vp->width;
    lcd_set_foreground(BG);lcd_fillrect(0,y,w,h);
    if(info->is_title)
    {
        lcd_set_foreground(MINT);label(info->dsp_text,px(8),y+px(4),px(22),w-px(16));
        lcd_set_foreground(CARD);lcd_hline(0,w-1,y+h-1);return;
    }
    bool selected=info->is_selected;
    if(selected){lcd_set_foreground(CARD);lcd_fillrect(px(2),y+1,w-px(4),h-2);lcd_set_foreground(MINT);lcd_fillrect(px(2),y+1,px(3),h-2);}
    lcd_set_foreground(selected?MINT:LAVENDER);
    int size=px(selected?27:23),left=px(16);
    if(w>=px(260)&&info->have_icons&&info->icon>=0){screen_put_iconxy(info->display,left,y+(h-get_icon_height(SCREEN_MAIN))/2,info->icon);left+=px(32);}
    int available=w-left-px(12),text_width,text_height;
    font_getstringsize(info->dsp_text,&text_width,&text_height,screens[SCREEN_MAIN].getuifont());
    if(selected&&text_width*size/MAX(1,text_height)>available){
        struct line_desc line=*info->linedes;line.style=STYLE_COLORBAR|STYLE_COLORED;line.line_color=CARD;line.text_color=MINT;line.scroll=true;
        info->display->put_line(left,y,&line,"$t",info->dsp_text);
    }else label(info->dsp_text,left,y+(h-size)/2,size,available);
}
static fb_data playing_frame[LCD_WIDTH*LCD_HEIGHT];
static fb_data work_frame[LCD_WIDTH*LCD_HEIGHT];
static bool have_playing_frame, sheet_mode;
static void capture_frame(fb_data *destination)
{
    struct viewport *old=lcd_set_viewport(NULL);
#if LCD_STRIDEFORMAT == VERTICAL_STRIDE
    for(int x=0;x<LCD_WIDTH;x++) memcpy(destination+x*LCD_HEIGHT,FBADDR(x,0),LCD_HEIGHT*sizeof(fb_data));
#else
    for(int y=0;y<LCD_HEIGHT;y++) memcpy(destination+y*LCD_WIDTH,FBADDR(0,y),LCD_WIDTH*sizeof(fb_data));
#endif
    lcd_set_viewport(old);
}
void snarty_capture_playing_screen(void) { capture_frame(playing_frame);have_playing_frame=true; }
void snarty_snapshot_current(void) { capture_frame(work_frame); }
void snarty_snapshot_restore(void) { lcd_bitmap(work_frame,0,0,LCD_WIDTH,LCD_HEIGHT); }
static void sheet_transition(bool opening)
{
    if(!have_playing_frame)return;
    struct viewport *old=lcd_set_viewport(NULL);capture_frame(work_frame);
    for(int frame=0;frame<=8;frame++)
    {
        int offset=LCD_HEIGHT*eased(opening?frame:8-frame,8)/256;
        if(offset<LCD_HEIGHT)lcd_bitmap_part(playing_frame,0,offset,STRIDE_MAIN(LCD_WIDTH,LCD_HEIGHT),0,0,LCD_WIDTH,LCD_HEIGHT-offset);
        if(offset>0)lcd_bitmap_part(work_frame,0,0,STRIDE_MAIN(LCD_WIDTH,LCD_HEIGHT),0,LCD_HEIGHT-offset,LCD_WIDTH,offset);
        lcd_update();sleep(MAX(1,HZ/50));
    }
    lcd_set_viewport(old);
}
int snarty_nav_choose_sheet(const char *title,const struct snarty_nav_item *items,int count,int *selected)
{
    sheet_mode=true;int result=snarty_nav_choose(title,items,count,selected);sheet_mode=false;return result;
}
static void icon(enum snarty_icon id, int x, int y, int size)
{
    if(id<0 || id>=SN_ICON_COUNT || size<=0)return;
    for (int dy=0;dy<size;dy++)
    {
        uint32_t row=snarty_icons[id][dy*32/size];int run=-1;
        for (int dx=0;dx<=size;dx++)
        {
            bool ink=dx<size && ((row>>(dx*32/size))&1);
            if (ink && run<0) run=dx;
            if (!ink && run>=0) {lcd_hline(x+run,x+dx-1,y+dy);run=-1;}
        }
    }
}
static void draw(const char *title,const struct snarty_nav_item *items,int count,
                 int selected,int previous,int level)
{
    int top=px(52), footer=px(28);
    int rows=MIN(count,MAX(1,(LCD_HEIGHT-top-footer)/px(52)));
    int start=MAX(0,MIN(selected-rows/2,count-rows));
    int row_h=(LCD_HEIGHT-top-footer)/rows;
    lcd_set_background(BG);lcd_clear_display();lcd_set_foreground(MINT);
    label(title,px(16),px(10),MIN((int)font_get(screens[SCREEN_MAIN].getuifont())->height,px(28)),LCD_WIDTH-px(90));
    char number[24];snprintf(number,sizeof(number),"%d/%d",selected+1,count);
    fixed_label(number,LCD_WIDTH-px(72),px(18),MAX(12,px(16)),px(64));
    lcd_set_foreground(CARD);lcd_hline(px(12),LCD_WIDTH-px(12),px(44));
    for (int row=0;row<rows;row++)
    {
        int index=start+row, y=top+row*row_h;
        int growth=index==selected?level:index==previous?256-level:0;
        if (growth)
        {
            lcd_set_foreground(LCD_RGBPACK(35+13*growth/256,34+12*growth/256,52+15*growth/256));
            int inset=px(16)-px(7)*growth/256;
            int height=row_h-px(16)+px(10)*growth/256;
            lcd_fillrect(inset,y+(row_h-height)/2,LCD_WIDTH-2*inset,height);
            lcd_set_foreground(MINT);
            lcd_fillrect(inset,y+(row_h-height)/2,MAX(1,px(3)*growth/256),height);
        }
        lcd_set_foreground(growth?MINT:LAVENDER);
        int size=px(30)+px(9)*growth/256, h=MIN((int)font_get(screens[SCREEN_MAIN].getuifont())->height,row_h-px(14))+px(6)*growth/256;
        icon(items[index].icon,px(20)+(px(40)-size)/2,y+(row_h-size)/2,size);
        label(items[index].label,px(76),y+(row_h-h)/2,h,LCD_WIDTH-px(92));
        if (index==selected) label(">",LCD_WIDTH-px(28),y+(row_h-px(18))/2,px(18),px(20));
    }
    lcd_set_foreground(LAVENDER);
    fixed_label("Back",px(16),LCD_HEIGHT-px(24),MAX(12,px(16)),px(80));
    fixed_label("Open",LCD_WIDTH-px(66),LCD_HEIGHT-px(24),MAX(12,px(16)),px(60));
    lcd_update();
}
int snarty_nav_choose(const char *title,const struct snarty_nav_item *items,
                     int count,int *selected)
{
    if (count<=0) return SN_NAV_BACK;
    *selected=MAX(0,MIN(*selected,count-1));
    unsigned fg=lcd_get_foreground(),bg=lcd_get_background();
    fb_data *backdrop=lcd_get_backdrop();
    viewportmanager_theme_enable(SCREEN_MAIN,false,NULL);
    lcd_set_viewport(NULL);lcd_set_backdrop(NULL);lcd_scroll_stop();
    int previous=-1, result=SN_NAV_BACK, duration=MAX(1,HZ/6);
    long began=current_tick-duration;
    bool dirty=true,first_frame=true;
    while (true)
    {
        int elapsed=current_tick-began;
        if (dirty || elapsed<duration)
        {
            draw(title,items,count,*selected,previous,eased(elapsed,duration));
            dirty=elapsed<duration;
            if(first_frame && sheet_mode)sheet_transition(true);
            first_frame=false;
        }
        int action=get_action(CONTEXT_MAINMENU,dirty?MAX(1,HZ/60):HZ/2);
        if (action==ACTION_STD_NEXT || action==ACTION_STD_NEXTREPEAT ||
            action==ACTION_STD_PREV || action==ACTION_STD_PREVREPEAT)
        {
            previous=*selected;
            int step=(action==ACTION_STD_NEXT || action==ACTION_STD_NEXTREPEAT)?1:-1;
            *selected=(*selected+step+count)%count;began=current_tick;dirty=true;
            if (global_settings.talk_menu) talk_spell(items[*selected].label,false);
        }
        else if (action==ACTION_STD_OK) {result=*selected;break;}
        else if (action==ACTION_STD_CANCEL) {result=SN_NAV_BACK;break;}
        else if (action==ACTION_STD_MENU) {result=SN_NAV_BACK;break;}
        else if(action==ACTION_SNARTY_FAVORITES){if(snarty_favorites_shuffle()){result=SN_NAV_WPS;break;}dirty=true;}
        else if (action==ACTION_TREE_WPS) {result=SN_NAV_WPS;break;}
        else if (action==ACTION_REDRAW || action==ACTION_NONE) dirty=true;
        else if (default_event_handler(action)==SYS_USB_CONNECTED) {result=SN_NAV_USB;break;}
    }
    if(sheet_mode && (result==SN_NAV_BACK || result==SN_NAV_HOME))sheet_transition(false);
    lcd_set_backdrop(backdrop);lcd_set_foreground(fg);lcd_set_background(bg);
    viewportmanager_theme_undo(SCREEN_MAIN,false);
    return result;
}
#endif
