/* Stable device first-seen dates. GPLv2+. */
#ifndef SNARTY_ADDED_H
#define SNARTY_ADDED_H
#include <stdint.h>
void snarty_added_observe(const char *path,uint32_t date);
long snarty_added_rank(const char *path,uint32_t fallback);
#endif
