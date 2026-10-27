/* Compile the real JNI bridge against a recording JNI table. GPLv2 or later. */
#include <jni.h>
#include <assert.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "video-android.h"

jclass RockboxService_class = (jclass)(uintptr_t)1;
jobject RockboxService_instance = (jobject)(uintptr_t)2;
static bool attached = true, exception, allocation_fail, method_fail, call_fail;
static int allocated, deleted, invoked, cleared;
static jsize byte_count;
static unsigned char buffer[512];
static const char *expected;
static jboolean check_exception(JNIEnv *env) { (void)env;return exception; }
static void clear_exception(JNIEnv *env) { (void)env;exception=false;cleared++; }
static jmethodID find_method(JNIEnv *env,jclass cls,const char *name,const char *signature) {
    (void)env;assert(cls==RockboxService_class);
    assert(!strcmp(name,"openVideo") && !strcmp(signature,"([B)Z"));
    if (method_fail) { exception=true;return NULL; }
    return (jmethodID)(uintptr_t)3;
}
static jbyteArray allocate(JNIEnv *env,jsize size) {
    (void)env;assert(size>=0 && size<(jsize)sizeof(buffer));
    if (allocation_fail) { exception=true;return NULL; }
    allocated++;byte_count=size;return (jbyteArray)buffer;
}
static void write_bytes(JNIEnv *env,jbyteArray bytes,jsize start,jsize size,const jbyte *data) {
    (void)env;assert(bytes==(jbyteArray)buffer && start==0 && size==byte_count);
    memcpy(buffer,data,size);
}
static jboolean invoke(JNIEnv *env,jobject service,jmethodID method,...) {
    (void)env;assert(service==RockboxService_instance && method==(jmethodID)(uintptr_t)3);
    va_list args;va_start(args,method);assert(va_arg(args,jbyteArray)==(jbyteArray)buffer);va_end(args);
    assert((size_t)byte_count==strlen(expected) && !memcmp(buffer,expected,byte_count));
    invoked++;
    if (call_fail) { exception=true;return JNI_FALSE; }
    return JNI_TRUE;
}
static void release(JNIEnv *env,jobject object) {
    (void)env;assert(object==(jobject)buffer);deleted++;
}
static const struct JNINativeInterface_ functions = {
    .GetMethodID=find_method,.NewByteArray=allocate,.SetByteArrayRegion=write_bytes,
    .CallBooleanMethod=invoke,.DeleteLocalRef=release,
    .ExceptionCheck=check_exception,.ExceptionClear=clear_exception,
};
static JNIEnv environment=&functions;
JNIEnv *getJavaEnvironment(void) { return attached?&environment:NULL; }
int main(void) {
    expected="/sdcard/Videos/A quote's & arrow \xf0\x9f\x8f\xb9.mp4";
    assert(android_play_video(expected));
    assert(allocated==1 && deleted==1 && invoked==1 && cleared==0);
    method_fail=true;assert(!android_play_video(expected));method_fail=false;
    assert(cleared==1 && !exception && deleted==1);
    allocation_fail=true;assert(!android_play_video(expected));allocation_fail=false;
    assert(cleared==2 && !exception && deleted==1);
    call_fail=true;assert(!android_play_video(expected));call_fail=false;
    assert(cleared==3 && !exception && deleted==2 && invoked==2);
    attached=false;assert(!android_play_video(expected));attached=true;
    RockboxService_instance=NULL;assert(!android_play_video(expected));
    puts("PASS: actual JNI bridge preserves UTF-8 bytes, launches explicitly, releases references and clears failure exceptions");
}
