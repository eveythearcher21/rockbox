#!/usr/bin/env python3
"""Actual raw gesture filter with a timed queue, including replay data."""
from pathlib import Path
import tempfile,subprocess
repo=Path(__file__).resolve().parents[3];r=Path(tempfile.mkdtemp(prefix='snarty-gesture-'));h=r/'h';h.mkdir()
(h/'config.h').write_text('#define SNARTY_NAVIGATION_H\n#define HAVE_SNARTY_NAVIGATION\n')
(h/'button.h').write_text('#include <stdint.h>\n#define BUTTON_NONE 0\n#define BUTTON_RIGHT 1\n#define BUTTON_LEFT 2\n#define BUTTON_REL 0x02000000\n#define BUTTON_REPEAT 0x04000000\n#define SYS_EVENT 0x40000000\nint button_get_w_tmo(int timeout);intptr_t button_get_data(void);\n')
(h/'kernel.h').write_text('#define HZ 100\n#define TIMEOUT_NOBLOCK 0\n#define MAX(a,b) ((a)>(b)?(a):(b))\n#define TIME_BEFORE(a,b) ((long)(a)-(long)(b)<0)\nextern long test_tick;\n#define current_tick test_tick\n')
(h/'system.h').write_text('')
(r/'test.c').write_text('''#include <assert.h>
#include <stdio.h>
#include "button.h"
#include "snarty_gesture.h"
long test_tick;static intptr_t datum;static int at,count;static struct {long tick;int button;intptr_t data;}q[64];
int button_get_w_tmo(int t){if(at<count&&(t<0||q[at].tick<=test_tick+t)){test_tick=q[at].tick;datum=q[at].data;return q[at++].button;}if(t>0)test_tick+=t;return 0;}
intptr_t button_get_data(void){return datum;}
static void reset(void){snarty_gesture_reset();at=count=0;test_tick=0;}
static void event(int tick,int b,int d){q[count].tick=tick;q[count].button=b;q[count++].data=d;}
static int read_button(void){return snarty_gesture_read(true,-1);}
int main(void){
 reset();for(int i=0;i<4;i++){int b=i%2?BUTTON_LEFT:BUTTON_RIGHT;event(i*15,b,0);event(i*15+5,b|BUTTON_REL,0);}assert(read_button()==SNARTY_GESTURE_MATCH);assert(at==8);
 reset();event(0,BUTTON_RIGHT,11);event(8,BUTTON_RIGHT|BUTTON_REL,12);assert(read_button()==BUTTON_RIGHT);assert(snarty_gesture_data()==11);assert(read_button()==(BUTTON_RIGHT|BUTTON_REL));assert(snarty_gesture_data()==12);
 reset();event(0,BUTTON_RIGHT,0);event(5,BUTTON_RIGHT|BUTTON_REL,0);event(10,7,99);assert(read_button()==BUTTON_RIGHT);assert(read_button()==(BUTTON_RIGHT|BUTTON_REL));assert(read_button()==7);assert(snarty_gesture_data()==99);
 reset();event(0,BUTTON_RIGHT,0);event(31,BUTTON_RIGHT|BUTTON_REPEAT,0);assert(read_button()==BUTTON_RIGHT);assert(read_button()==(BUTTON_RIGHT|BUTTON_REPEAT));
 reset();event(0,BUTTON_RIGHT,0);event(5,SYS_EVENT|1,123);assert(read_button()==(SYS_EVENT|1));assert(snarty_gesture_data()==123);
 reset();event(0,BUTTON_RIGHT,0);assert(snarty_gesture_read(false,-1)==BUTTON_RIGHT);
 reset();event(0,BUTTON_RIGHT,0);assert(snarty_gesture_read(true,0)==0);assert(snarty_gesture_read(false,0)==BUTTON_RIGHT);
 reset();for(int i=0;i<4;i++){int b=i%2?BUTTON_LEFT:BUTTON_RIGHT;event(i*34,b,0);event(i*34+5,b|BUTTON_REL,0);}assert(read_button()==SNARTY_GESTURE_MATCH);
 reset();event(0,BUTTON_RIGHT,0);event(5,BUTTON_RIGHT|BUTTON_REL,0);event(40,BUTTON_LEFT,0);assert(read_button()==BUTTON_RIGHT);assert(read_button()==(BUTTON_RIGHT|BUTTON_REL));assert(read_button()==BUTTON_LEFT);
 reset();for(int i=0;i<4;i++){int b=i%2?BUTTON_LEFT:BUTTON_RIGHT;event(i*34,b,0);event(i==3?130:i*34+5,b|BUTTON_REL,0);}assert(read_button()==BUTTON_RIGHT);
 puts("PASS: exact RLRL recognition, complete event consumption, ordinary/wrong/held/slow input replay, original event data, context cancellation, USB priority and nonblocking polling");}
''')
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g','-I',str(h),'-I',str(repo/'apps'),str(repo/'apps/snarty_gesture.c'),str(r/'test.c'),'-o',str(r/'test')],check=True)
subprocess.run([str(r/'test')],check=True)
