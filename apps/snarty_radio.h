/* Rockbox GPLv2 or later. */
#ifndef SNARTY_RADIO_H
#define SNARTY_RADIO_H
struct mp3entry;
int snarty_play_similar_for(const struct mp3entry *selected);
int snarty_play_similar(void);
#endif
