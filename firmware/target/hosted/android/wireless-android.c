/* SNARTY local Wi-Fi/library control bridge. GPLv2 or later. */
#define _SYSTEM_WITH_JNI
#include "config.h"
#include "system.h"
#include "wireless-android.h"
#include <string.h>
extern jclass RockboxService_class;
extern jobject RockboxService_instance;
bool android_wireless(int command,const char *input,char *output,int size)
{
    if(size<1)return false;
    output[0]=0;
    JNIEnv *env=getJavaEnvironment();
    if(!env || !RockboxService_class || !RockboxService_instance)return false;
    bool ok=false;jbyteArray in=NULL,out=NULL;
    jmethodID method=(*env)->GetMethodID(env,RockboxService_class,"wirelessCommand","(I[B)[B");
    if(!method || (*env)->ExceptionCheck(env))goto done;
    int length=input?strlen(input):0;
    in=(*env)->NewByteArray(env,length);
    if(!in || (*env)->ExceptionCheck(env))goto done;
    if(length)(*env)->SetByteArrayRegion(env,in,0,length,(const jbyte*)input);
    if((*env)->ExceptionCheck(env))goto done;
    out=(*env)->CallObjectMethod(env,RockboxService_instance,method,command,in);
    if(!out || (*env)->ExceptionCheck(env))goto done;
    length=(*env)->GetArrayLength(env,out);if(length>size-1)length=size-1;
    (*env)->GetByteArrayRegion(env,out,0,length,(jbyte*)output);output[length]=0;
    ok=!(*env)->ExceptionCheck(env);
done:
    if((*env)->ExceptionCheck(env))(*env)->ExceptionClear(env);
    if(in)(*env)->DeleteLocalRef(env,in);
    if(out)(*env)->DeleteLocalRef(env,out);
    return ok;
}
