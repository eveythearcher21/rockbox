/* SNARTY navigation. Rockbox GPLv2 or later. */
#ifndef SNARTY_NAVIGATION_H
#define SNARTY_NAVIGATION_H
#include "config.h"
/* Shared-code iPod simulator is the test harness; physical iPods are unchanged. */
#if defined(INNIOASIS_Y1) || (defined(SIMULATOR) && defined(IPOD_6G))
#define HAVE_SNARTY_NAVIGATION
#include <stdint.h>
#include "snarty_icons.h"
struct snarty_nav_item { const char *label; enum snarty_icon icon; int route; };
/* Returns an index or a navigation/event sentinel. */
#define SN_NAV_BACK (-1)
#define SN_NAV_HOME (-2)
#define SN_NAV_USB (-3)
#define SN_NAV_WPS (-4)
int snarty_nav_choose(const char *title, const struct snarty_nav_item *items,
                     int count, int *selected);
void snarty_navigation_home(void);
#endif
#endif
