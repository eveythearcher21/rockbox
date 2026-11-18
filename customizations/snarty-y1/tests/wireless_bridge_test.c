/* Actual native JNI wireless bridge against recording JNI operations. GPLv2+. */
#include <jni.h>
#include <assert.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "wireless-android.h"
jclass RockboxService_class=(jclass)(uintptr_t)1;
jobject RockboxService_instance=(jobject)(uintptr_t)2;
static bool attached=true,exception,fail_method,fail_alloc,fail_call;
static unsigned char input[256],result[512];
static int length,allocated,deleted,cleared,code;
static const char *expected;
static jboolean check_exception(JNIEnv *env){(void)env;return exception;}
static void clear(JNIEnv *env){(void)env;exception=false;cleared++;}
static jmethodID method(JNIEnv *env,jclass cls,const char *name,const char *sig){
    (void)env;assert(cls==RockboxService_class);assert(!strcmp(name,"wirelessCommand")&&!strcmp(sig,"(I[B)[B"));
    if(fail_method){exception=true;return NULL;}return(jmethodID)(uintptr_t)3;
}
static jbyteArray allocate(JNIEnv *env,jsize n){
    (void)env;assert(n>=0&&n<(int)sizeof(input));
    if(fail_alloc){exception=true;return NULL;}
    allocated++;length=n;return(jbyteArray)input;
}
static void set(JNIEnv *env,jbyteArray bytes,jsize start,jsize n,const jbyte *p){
    (void)env;assert(bytes==(jbyteArray)input&&start==0&&n==length);memcpy(input,p,n);
}
static jobject call(JNIEnv *env,jobject instance,jmethodID m,...){
    (void)env;assert(instance==RockboxService_instance&&m==(jmethodID)(uintptr_t)3);
    va_list args;va_start(args,m);assert(va_arg(args,int)==code);assert(va_arg(args,jbyteArray)==(jbyteArray)input);va_end(args);
    assert((int)strlen(expected)==length&&!memcmp(input,expected,length));
    if(fail_call){exception=true;return NULL;}return(jobject)result;
}
static jsize size(JNIEnv *env,jarray a){(void)env;assert(a==(jarray)result);return strlen((char*)result);}
static void get(JNIEnv *env,jbyteArray a,jsize start,jsize n,jbyte *p){(void)env;assert(a==(jbyteArray)result&&start==0);memcpy(p,result,n);}
static void release(JNIEnv *env,jobject a){(void)env;assert(a==(jobject)input||a==(jobject)result);deleted++;}
static const struct JNINativeInterface_ functions={
    .GetMethodID=method,.NewByteArray=allocate,.SetByteArrayRegion=set,
    .CallObjectMethod=call,.GetArrayLength=size,.GetByteArrayRegion=get,
    .ExceptionCheck=check_exception,.ExceptionClear=clear,.DeleteLocalRef=release,
};
static JNIEnv environment=&functions;
JNIEnv *getJavaEnvironment(void){return attached?&environment:NULL;}
int main(void){
    char output[128];code=6;expected="A quote's \xf0\x9f\x8f\xb9\tpa\\ss\"word";
    strcpy((char*)result,"Connecting \xf0\x9f\x8f\xb9");assert(android_wireless(code,expected,output,sizeof(output)));
    assert(!strcmp(output,(char*)result)&&allocated==1&&deleted==2);
    assert(android_wireless(code,expected,output,5)&&output[4]==0);
    assert(!android_wireless(code,expected,output,0));
    expected="";code=0;assert(android_wireless(code,NULL,output,sizeof(output)));
    fail_method=true;assert(!android_wireless(code,NULL,output,sizeof(output)));fail_method=false;
    fail_alloc=true;assert(!android_wireless(code,NULL,output,sizeof(output)));fail_alloc=false;
    fail_call=true;assert(!android_wireless(code,NULL,output,sizeof(output)));fail_call=false;
    assert(cleared==3&&!exception&&deleted==7);
    attached=false;assert(!android_wireless(code,NULL,output,sizeof(output)));attached=true;
    RockboxService_instance=NULL;assert(!android_wireless(code,NULL,output,sizeof(output)));
    puts("PASS: actual native wireless bridge command dispatch, exact UTF8/password byte transport, output bounds, exception/reference cleanup and missing-service errors");
}
