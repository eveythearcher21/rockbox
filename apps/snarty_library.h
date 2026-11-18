/* Synced library order. Rockbox GPLv2 or later. */
#ifndef SNARTY_LIBRARY_H
#define SNARTY_LIBRARY_H
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#define SNARTY_LIBRARY_RECORD_SIZE 268
#define SNARTY_LIBRARY_PATH_SIZE 260
#define SNARTY_LIBRARY_HEADER_SIZE 16
bool snarty_device_path(const char *path,char *output,size_t size);
bool snarty_device_paths_equal(const char *a,const char *b);
bool snarty_library_available(void);
long snarty_library_rank(const char *path, bool album);
#endif
