/* SNARTY local Wi-Fi/library control bridge. GPLv2 or later. */
#ifndef WIRELESS_ANDROID_H
#define WIRELESS_ANDROID_H
#include <stdbool.h>
bool android_wireless(int command,const char *input,char *output,int size);
#endif
