#!/usr/bin/env python3
"""Exercise actual font renderer against recording/pinning font-cache stubs."""
from pathlib import Path
import subprocess,tempfile
repo=Path(__file__).resolve().parents[3];s=(repo/'apps/snarty_navigation.c').read_text()
a=s.index('static void label_font(');brace=s.index('{',a);end=brace+1;depth=1
while depth:depth+=(s[end]=='{')-(s[end]=='}');end+=1
code='''#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#define FONT_UI 12
typedef unsigned int ucschar_t;
static const unsigned char* utf8decode(const unsigned char*s,ucschar_t*c){*c=*s;return s+1;}
#define FONT_SYSFIXED -1
#define SCREEN_MAIN 0
#define MAX(a,b) ((a)>(b)?(a):(b))
struct font {int height,depth;};static struct font cached={5,0};
static int pinned,pins,unpins,lines;static bool system_font;
static int ui_font(void){return 2;} static struct {int(*getuifont)(void);} screens[]={{ui_font}};
static void font_lock(int id,bool lock){assert(id==2||id==-1);system_font=id==-1;if(id<0)return;if(lock){assert(!pinned);pinned=1;pins++;}else{assert(pinned);pinned=0;unpins++;}}
static struct font*font_get(int id){assert(id==2||id==-1);return &cached;}
static int font_get_width(struct font*f,unsigned char c){(void)f;(void)c;assert(pinned||system_font);return 3;}
static const unsigned char*font_get_bits(struct font*f,unsigned char c){(void)c;assert(pinned||system_font);static unsigned char mono[]={31,17,31};static unsigned char alpha[]={0,0,0,0,0,0,0,0};return f->depth?alpha:mono;}
static void lcd_hline(int a,int b,int y){assert(a>=0&&b>=a&&b<480&&y>=0&&y<360);lines++;}
'''+s[a:end]+'''
int main(void){
 for(int depth=0;depth<2;depth++)for(int height=5;height<33;height++){
  cached.depth=depth;int before=lines;label_font("Music",5,5,height,300,FONT_UI);assert(lines>before&&!pinned&&pins==unpins);
  before=lines;label_font("Clipped",5,5,height,0,FONT_UI);assert(lines==before&&!pinned&&pins==unpins);
 }
 label_font("Back",5,5,12,80,FONT_SYSFIXED);assert(!pinned&&pins==unpins);
 puts("PASS: real renderer resolves FONT_UI, pins across cache I/O, balances all exit paths and clips mono/alpha glyphs across scale sizes");
}
'''
r=Path(tempfile.mkdtemp(prefix='snarty-font-'));(r/'test.c').write_text(code)
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g',str(r/'test.c'),'-o',str(r/'test')],check=True)
subprocess.run([str(r/'test')],check=True)
