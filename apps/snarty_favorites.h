#ifndef SNARTY_FAVORITES_H
#define SNARTY_FAVORITES_H
#include <stdbool.h>
struct mp3entry;
bool snarty_favorites_match(const char *path,const char *artist,const char *albumartist,const char *album);
bool snarty_favorites_shuffle(void);
int snarty_favorite_toggle(const struct mp3entry *track,int kind);
#endif
