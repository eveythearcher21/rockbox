#include "config.h"
#include "snarty_navigation.h"
#ifdef HAVE_SNARTY_NAVIGATION
#include "button.h"
#include "kernel.h"
#include "system.h"
#include "snarty_gesture.h"
#define CAPACITY 16
#define SNARTY_REACHED(a,b) (!TIME_BEFORE((a),(b)))
static struct {int button;intptr_t data;} saved[CAPACITY];
static unsigned count,replay,step;
static bool pending,flushing,held;
static long deadline,started;
static intptr_t data;
void snarty_gesture_reset(void){count=replay=step=0;pending=flushing=held=false;}
intptr_t snarty_gesture_data(void){return data;}
static int output(void){int b=saved[replay].button;data=saved[replay++].data;if(replay==count)snarty_gesture_reset();return b;}
int snarty_gesture_read(bool enabled,int timeout)
{
    if(flushing)return output();
    if(pending&&(!enabled||SNARTY_REACHED(current_tick,deadline)||SNARTY_REACHED(current_tick,started+HZ*12/10))){flushing=true;return output();}
    for(;;){
        int wait=timeout;
        if(pending){int remaining=(int)(deadline-current_tick);if(remaining<0)remaining=0;if(wait<0||wait>remaining)wait=remaining;}
        int button=button_get_w_tmo(wait);data=button_get_data();
        if(button&SYS_EVENT){snarty_gesture_reset();return button;}
        if(button==BUTTON_NONE){
            if(pending&&(SNARTY_REACHED(current_tick,deadline)||SNARTY_REACHED(current_tick,started+HZ*12/10))){flushing=true;return output();}
            return button;
        }
        if(pending&&(SNARTY_REACHED(current_tick,deadline)||SNARTY_REACHED(current_tick,started+HZ*12/10))){
            saved[count].button=button;saved[count++].data=data;flushing=true;return output();
        }
        if(!pending){
            if(!enabled||button!=BUTTON_RIGHT)return button;
            pending=true;started=current_tick;deadline=current_tick+MAX(1,HZ*35/100);step=1;held=true;
            saved[0].button=button;saved[0].data=data;count=1;
        }else{
            if(count==CAPACITY){flushing=true;return output();} /* Real patterns use eight events. */
            saved[count].button=button;saved[count++].data=data;
            int previous=step%2?BUTTON_RIGHT:BUTTON_LEFT;
            if(held&&button==(previous|BUTTON_REL)){
                held=false;if(step==4){snarty_gesture_reset();return SNARTY_GESTURE_MATCH;}
            }else if(!held&&button==(step%2?BUTTON_LEFT:BUTTON_RIGHT)&&step<4){
                step++;held=true;deadline=current_tick+MAX(1,HZ*35/100);
            }else{flushing=true;return output();}
        }
        if(timeout==TIMEOUT_NOBLOCK)return BUTTON_NONE;
    }
}
#endif
