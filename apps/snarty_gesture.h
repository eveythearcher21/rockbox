/* Raw, replayable Right/Left gesture. GPLv2+. */
#ifndef SNARTY_GESTURE_H
#define SNARTY_GESTURE_H
#include <stdbool.h>
#include <stdint.h>
#define SNARTY_GESTURE_MATCH (-77)
#define ACTION_SNARTY_FAVORITES 0x7f14
int snarty_gesture_read(bool enabled,int timeout);
intptr_t snarty_gesture_data(void);
void snarty_gesture_reset(void);
#endif
