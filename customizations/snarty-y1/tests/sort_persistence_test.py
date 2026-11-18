#!/usr/bin/env python3
"""Compile real sort preference read/write functions and emulate process restart."""
from pathlib import Path
import tempfile,subprocess,json
repo=Path(__file__).resolve().parents[3];root=Path(tempfile.mkdtemp(prefix='snarty-sorts-'));source=(repo/'apps/tagtree.c').read_text()
def extract(name):
 a=source.index('static void '+name+'(');b=source.index('{',a);depth=1;i=b+1
 while depth:
  depth+=(source[i]=='{')-(source[i]=='}');i+=1
 return source[a:i]
text='''#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
'''+ '#define ROCKBOX_DIR '+json.dumps(str(root))+'\nstatic unsigned char library_sort[3];static bool sorts_loaded;\n'+extract('load_sorts')+'\n'+extract('save_sorts')+'''
int main(void){load_sorts();assert(!library_sort[0]&&!library_sort[1]&&!library_sort[2]);library_sort[0]=1;library_sort[1]=2;save_sorts();memset(library_sort,0,3);sorts_loaded=false;load_sorts();assert(library_sort[0]==1&&library_sort[1]==2&&library_sort[2]==0);int fd=open(ROCKBOX_DIR "/snarty-sorts-v1.bin",O_WRONLY|O_TRUNC);write(fd,"x",1);close(fd);memset(library_sort,0,3);sorts_loaded=false;load_sorts();assert(!library_sort[0]&&!library_sort[1]&&!library_sort[2]);puts("PASS: actual atomic sort preference roundtrip across restart, independent categories, missing/truncated input defaults");}
'''
(root/'test.c').write_text(text)
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(root/'test.c'),'-o',str(root/'test')],check=True)
subprocess.run([str(root/'test')],check=True)
