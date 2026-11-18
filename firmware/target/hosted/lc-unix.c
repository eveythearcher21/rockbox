/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 *
 * Copyright (C) 2010 by Thomas Martitz
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY
 * KIND, either express or implied.
 *
 ****************************************************************************/

#ifdef INNIOASIS_Y1
#define _SYSTEM_WITH_JNI
#include "system.h"
#include <android/log.h>
extern jclass RockboxService_class;
extern jobject RockboxService_instance;
#endif
#include <string.h> /* size_t */
#include <dlfcn.h>
#include "file.h"
#include "debug.h"
#include "load_code.h"

void *lc_open(const char *filename, unsigned char *buf, size_t buf_size)
{
    (void)buf;
    (void)buf_size;
    char path[MAX_PATH];

    const char *fpath = handle_special_dirs(filename, 0, path, sizeof(path));
    if(!fpath)return NULL;

#ifdef INNIOASIS_Y1
    char executable[MAX_PATH];
    if(fpath && ((strlen(fpath)>5 && !strcmp(fpath+strlen(fpath)-5,".rock")) || (strlen(fpath)>4 && !strcmp(fpath+strlen(fpath)-4,".ovl")))) {
    JNIEnv *env=getJavaEnvironment();
    if(!env || !fpath)return NULL;
    jbyteArray in=NULL,out=NULL;bool copied=false;
    jmethodID method=(*env)->GetMethodID(env,RockboxService_class,"cachePlugin","([B)[B");
    if(method && !(*env)->ExceptionCheck(env)) {
        int n=strlen(fpath);in=(*env)->NewByteArray(env,n);
        if(in && !(*env)->ExceptionCheck(env)) {
            (*env)->SetByteArrayRegion(env,in,0,n,(const jbyte*)fpath);
            if(!(*env)->ExceptionCheck(env))out=(*env)->CallObjectMethod(env,RockboxService_instance,method,in);
            if(out && !(*env)->ExceptionCheck(env)) {
                n=(*env)->GetArrayLength(env,out);
                if(n>0 && n<(int)sizeof(executable)) {
                    (*env)->GetByteArrayRegion(env,out,0,n,(jbyte*)executable);
                    executable[n]=0;copied=!(*env)->ExceptionCheck(env);
                }
            }
        }
    }
    if((*env)->ExceptionCheck(env))(*env)->ExceptionClear(env);
    if(in)(*env)->DeleteLocalRef(env,in);
    if(out)(*env)->DeleteLocalRef(env,out);
    if(!copied)return NULL;
    fpath=executable;
    }
#endif
    void *handle = dlopen(fpath, RTLD_NOW);
    if (handle == NULL)
    {
#ifdef INNIOASIS_Y1
        __android_log_print(ANDROID_LOG_ERROR,"RockboxPlugin","dlopen failed for %s: %s",filename,dlerror());
#endif
        DEBUGF("failed to load %s\n", filename);
        DEBUGF("lc_open(%s): %s\n", filename, dlerror());
    }
    return handle;
}

void *lc_get_header(void *handle)
{
    char *ret = dlsym(handle, "__header");
    if (ret == NULL)
        ret = dlsym(handle, "___header");

    return ret;
}

void lc_close(void *handle)
{
    dlclose(handle);
}
