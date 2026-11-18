#!/usr/bin/env python3
"""Actual persisted favorites and first-seen index with POSIX filesystem stubs."""
from pathlib import Path
import tempfile,subprocess,json
repo=Path(__file__).resolve().parents[3];root=Path(tempfile.mkdtemp(prefix='snarty-rules-'));h=root/'headers';h.mkdir()
headers={'config.h':'#define MAX_PATH 1024\n','file.h':'#include <unistd.h>\n#include <fcntl.h>\n#include <stdio.h>\n',
'rbpaths.h':'#define ROCKBOX_DIR '+json.dumps(str(root))+'\n',
'dir.h':'#include <sys/stat.h>\n#include <dirent.h>\n#include <time.h>\n#define mkdir(p) mkdir(p,0700)\nstatic inline int dir_exists(const char*p){struct stat s;return stat(p,&s)==0&&S_ISDIR(s.st_mode); }\nstruct dirinfo{time_t mtime;};\nstatic inline struct dirinfo dir_get_info(DIR*d,struct dirent*e){(void)d;(void)e;return (struct dirinfo){0};}\n',
'string-extra.h':'#include <string.h>\nstatic inline size_t strlcpy(char*d,const char*s,size_t n){size_t l=strlen(s);if(n){size_t k=l<n-1?l:n-1;memcpy(d,s,k);d[k]=0;}return l;}\n',
'metadata.h':'struct mp3entry{char path[260];char*artist;char*albumartist;char*album;};\n'}
for n,s in headers.items():(h/n).write_text(s)
(root/'test.c').write_text('''#include <assert.h>
#include <stdio.h>
#include <limits.h>
#include "metadata.h"
#include "snarty_favorites.h"
#include "snarty_added.h"
int main(void){
 struct mp3entry a={"/sdcard/Music/a.mp3","Artist A","Artist A","Album A"};
 assert(!snarty_favorites_match(a.path,a.artist,a.albumartist,a.album));
 assert(snarty_favorite_toggle(&a,1)==1);
 assert(snarty_favorites_match("/storage/sdcard0/Music/a.mp3",a.artist,a.albumartist,a.album));
 assert(!snarty_favorites_match("/sdcard/Music/b.mp3",a.artist,a.albumartist,a.album));
 assert(snarty_favorite_toggle(&a,2)==1);
 assert(snarty_favorites_match("/sdcard/Music/untagged-albumartist.mp3",a.artist,"<Untagged>",a.album));
 assert(snarty_favorites_match("/sdcard/Music/b.mp3",a.artist,a.albumartist,a.album));
 assert(!snarty_favorites_match("/sdcard/other.mp3","Other","Other",a.album));
 assert(snarty_favorite_toggle(&a,2)==0);
 assert(!snarty_favorites_match("/sdcard/Music/b.mp3",a.artist,a.albumartist,a.album));
 assert(snarty_favorites_match(a.path,a.artist,a.albumartist,a.album));
 assert(snarty_favorite_toggle(&a,3)==1);
 assert(snarty_favorites_match("/sdcard/FUTURE.mp3",a.artist,a.albumartist,"Future Album"));
 assert(snarty_favorite_toggle(&a,3)==0);
 assert(!snarty_favorites_match("/sdcard/FUTURE.mp3",a.artist,a.albumartist,"Future Album"));
 assert(snarty_favorite_toggle(&a,3)==1); /* tombstone can reactivate */
 snarty_added_observe(a.path,1700000000);long old=snarty_added_rank(a.path,0);
 snarty_added_observe(a.path,1800000000);assert(snarty_added_rank(a.path,0)==old);
 assert(snarty_added_rank("/storage/sdcard0/Music/a.mp3",0)==old);
 long newer=snarty_added_rank("/sdcard/Music/new.mp3",1800000000);assert(newer<old&&newer>=1000000000);
 assert(snarty_added_rank("/sdcard/Music/new.mp3",1900000000)==newer);
 assert(snarty_added_rank("/missing.mp3",0)==INT_MAX);
 puts("PASS: persisted song/album/artist favorites, future artist matches, independent removal/reactivation, alias paths, stable first-seen dates and descending fallback chronology");
}''')
subprocess.run(['cc','-D__PCTOOL__','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g','-I',str(h),'-I',str(repo/'apps'),*[str(repo/'apps'/f) for f in ('snarty_library.c','snarty_added.c','snarty_favorites.c')],str(root/'test.c'),'-o',str(root/'test')],check=True)
subprocess.run([str(root/'test')],check=True)
