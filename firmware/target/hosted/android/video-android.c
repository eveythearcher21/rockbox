/* Internal Y1 video activity bridge. Rockbox GPLv2 or later. */
#define _SYSTEM_WITH_JNI
#include "config.h"
#include "system.h"
#include "video-android.h"
#include <string.h>

extern jclass RockboxService_class;
extern jobject RockboxService_instance;

bool android_play_video(const char *path)
{
    JNIEnv *env = getJavaEnvironment();
    if (!env || !RockboxService_class || !RockboxService_instance)
        return false;
    jmethodID method = (*env)->GetMethodID(env, RockboxService_class,
                                          "openVideo", "([B)Z");
    jbyteArray bytes = NULL;
    bool opened = false;
    if (!method || (*env)->ExceptionCheck(env))
        goto done;
    /* Byte transport preserves UTF-8 filenames, including four-byte Unicode. */
    size_t length = strlen(path);
    bytes = (*env)->NewByteArray(env, length);
    if (!bytes || (*env)->ExceptionCheck(env))
        goto done;
    (*env)->SetByteArrayRegion(env, bytes, 0, length, (const jbyte *)path);
    if (!(*env)->ExceptionCheck(env))
        opened = (*env)->CallBooleanMethod(env, RockboxService_instance,
                                           method, bytes) == JNI_TRUE;
done:
    if ((*env)->ExceptionCheck(env))
    {
        (*env)->ExceptionClear(env);
        opened = false;
    }
    if (bytes)
        (*env)->DeleteLocalRef(env, bytes);
    return opened;
}
