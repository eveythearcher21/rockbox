#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
s=(Path(__file__).resolve().parents[3]/'apps/root_menu.c').read_text();a=s.index('static int get_selection(');b=s.index('\nstatic inline int load_screen',a)
code='''#include <assert.h>
#include <stdio.h>
#define ARRAYLEN(a) (sizeof(a)/sizeof((a)[0]))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MENU_TYPE_MASK 15
#define MT_RETURN_VALUE 6
#define MENU_GET_COUNT(flags) ((flags)>>4)
struct menu {int flags,value;};
static struct menu values[6],root_menu_;
static struct menu*root_menu__[15];
'''+s[a:b]+'''
int main(void){
 for(int i=0;i<6;i++){values[i].flags=6;values[i].value=i;root_menu__[i]=&values[i];}
 root_menu_.flags=6<<4;assert(get_selection(4)==4);assert(get_selection(26)==0);
 root_menu_.flags=1<<4;assert(get_selection(4)==0);
 root_menu_.flags=100<<4;assert(get_selection(26)==0);
 root_menu__[4]=0;assert(get_selection(4)==0);
 puts("PASS: actual root selection lookup bounds configured entries, handles sparse/null slots and safely returns from routes absent from the legacy menu");
}
'''
r=Path(tempfile.mkdtemp(prefix='snarty-root-selection-'));(r/'test.c').write_text(code)
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g',str(r/'test.c'),'-o',str(r/'test')],check=True);subprocess.run([str(r/'test')],check=True)
