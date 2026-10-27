/* Local listening journal and Wrapped views. Rockbox GPLv2 or later. */
#ifndef LISTENING_HISTORY_H
#define LISTENING_HISTORY_H
struct mp3entry;
void listening_history_record(const struct mp3entry *id3);
void listening_history_show(void);
#endif
