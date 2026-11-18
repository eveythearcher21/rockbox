#!/usr/bin/env python3
"""Compile actual playlist shuffle functions with recording host dependencies."""
from pathlib import Path
import subprocess,tempfile
repo=Path(__file__).resolve().parents[3]
source=(repo/'apps/playlist.c').read_text()
def function(signature):
 start=source.index(signature);brace=source.index('{',start);depth=1;end=brace+1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
code='''#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
struct playlist_info {unsigned long indices[26];int index,first_index,amount,last_insert_pos;unsigned int seed;};
static struct playlist_info current_playlist;
static struct {bool play_selected;} global_settings;
static int locks, stops, writes, saved_first;
static void dc_thread_stop(struct playlist_info*p){(void)p;stops++;}
static void dc_thread_start(struct playlist_info*p,bool b){(void)p;(void)b;stops--;}
static void playlist_write_lock(struct playlist_info*p){(void)p;locks++;}
static void playlist_write_unlock(struct playlist_info*p){(void)p;locks--;}
static unsigned int prng_newseed(void){return 12345;}
static void iap_on_track_playback_index(int i,bool b){(void)i;(void)b;}
static int rotate_index(struct playlist_info*p,int i){return (i-p->first_index+p->amount)%p->amount;}
#define PLAYLIST_COMMAND_SHUFFLE 1
static void update_control_unlocked(struct playlist_info*p,int c,unsigned int seed,int first,void*a,void*b,void*d){(void)p;(void)c;(void)seed;(void)a;(void)b;(void)d;writes++;saved_first=first;}
'''
for name in ['static void find_and_set_playlist_index_unlocked(', 'static int randomise_playlist_unlocked(', 'int playlist_shuffle(', 'int playlist_shuffle_all(']:code+=function(name)+'\n'
code+='''
static void init(int amount,int first){current_playlist.amount=amount;current_playlist.first_index=first;current_playlist.index=first;for(int i=0;i<26;i++)current_playlist.indices[i]=(unsigned long)i;}
int main(void){
 bool reproduced=false;global_settings.play_selected=true;
 for(int seed=1;seed<50;seed++){init(26,0);playlist_shuffle(seed,0);if(current_playlist.first_index!=0)reproduced=true;}
 assert(reproduced); // Old API relocates the queue origin when preserving track 1.
 for(int selected=0;selected<2;selected++)for(int amount=1;amount<=26;amount++)for(int first=0;first<amount;first++)for(int seed=1;seed<=20;seed++){
  global_settings.play_selected=selected;init(amount,first);int before=writes;
  assert(playlist_shuffle_all(seed)==0);assert(current_playlist.index==0&&current_playlist.first_index==0);
  assert(saved_first==0&&writes==before+1);assert(global_settings.play_selected==(bool)selected);
  unsigned int seen=0;for(int i=0;i<amount;i++){unsigned long track=current_playlist.indices[i];assert(track<(unsigned long)amount);assert(!(seen&(1u<<track)));seen|=1u<<track;}
  assert(seen==((1u<<amount)-1));assert(locks==0&&stops==0);
 }
 init(0,0);int before=writes;assert(playlist_shuffle_all(1)==-1);assert(writes==before&&locks==0&&stops==0);
 puts("PASS: reproduced rotated-origin regression; complete unique shuffle for 1..26 tracks, all previous origins, both Play Selected First settings, 20 seeds, persisted origin zero and empty queue");
}
'''
work=Path(tempfile.mkdtemp(prefix='snarty-shuffle-'));(work/'test.c').write_text(code)
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g',str(work/'test.c'),'-o',str(work/'test')],check=True)
subprocess.run([str(work/'test')],check=True)
