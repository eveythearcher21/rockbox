/* Local listening-history format and ranking. Rockbox GPLv2 or later. */
#ifndef LISTENING_STATS_H
#define LISTENING_STATS_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define LISTENING_LINE_SIZE 4096
#define LISTENING_LOG_TEXT_LIMIT 512
#define LISTENING_TEXT_SIZE 161
#define LISTENING_PATH_SIZE 260
#define LISTENING_TOP_COUNT 10
#define LISTENING_HISTORY_HEADER "# rockbox-listening-history\t1\n"
struct listening_record {
    int year, month, day, hour, minute, second;
    unsigned long elapsed_ms, length_ms;
    const char *path, *title, *artist, *album;
};
struct listening_stat {
    uint64_t hash, offset;
    uint32_t count;
};
typedef bool (*listening_same_path)(void *context, uint64_t offset, const char *path);
int listening_record_format(char *buffer, size_t size, const struct listening_record *record);
bool listening_record_parse(char *line, struct listening_record *record);
bool listening_record_matches(const struct listening_record *record, int year, int month);
uint64_t listening_path_hash(const char *path);
bool listening_stats_add(struct listening_stat *table, size_t capacity,
                         const struct listening_record *record, uint64_t offset,
                         listening_same_path same_path, void *context);
size_t listening_stats_top(const struct listening_stat *table, size_t capacity,
                          size_t result[LISTENING_TOP_COUNT]);
#endif
