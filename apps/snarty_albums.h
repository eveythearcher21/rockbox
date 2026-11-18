/* Album cards and detail panel. Rockbox GPLv2 or later. */
#ifndef SNARTY_ALBUMS_H
#define SNARTY_ALBUMS_H
#include "snarty_navigation.h"
#ifdef HAVE_SNARTY_NAVIGATION
struct gui_synclist;struct tree_context;
void snarty_albums_configure(struct gui_synclist *list,struct tree_context *tree);
void snarty_album_open(struct tree_context *tree);
void snarty_albums_leave(void);
#endif
#endif
