/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 * $Id$
 *
 * Copyright (C) 2010 Thomas Martitz
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

package org.rockbox;

import org.rockbox.Helper.MediaButtonReceiver;
import android.app.Activity;
import android.app.ProgressDialog;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.ResultReceiver;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Toast;
import android.content.Context;
import android.os.PowerManager;
import android.util.Log;
import android.app.ActivityManager;
import java.util.List;

public class RockboxActivity extends Activity
{
    private android.widget.TextView storageStatus;
    private void showStorageWait(String detail) {
        if (storageStatus == null) {
            android.widget.LinearLayout panel = new android.widget.LinearLayout(this);
            panel.setOrientation(android.widget.LinearLayout.VERTICAL);
            panel.setGravity(android.view.Gravity.CENTER);
            panel.setPadding(16, 12, 16, 12);
            panel.setBackgroundColor(android.graphics.Color.rgb(35, 34, 52));
            storageStatus = new android.widget.TextView(this);
            storageStatus.setTextColor(android.graphics.Color.rgb(162, 172, 205));
            storageStatus.setGravity(android.view.Gravity.CENTER);
            storageStatus.setTextSize(15);
            panel.addView(storageStatus, new android.widget.LinearLayout.LayoutParams(-1, 0, 1));
            android.widget.Button retry = new android.widget.Button(this);
            retry.setText("Retry storage");
            retry.setOnClickListener(new android.view.View.OnClickListener() {
                public void onClick(android.view.View view) {
                    Intent intent = new Intent(RockboxActivity.this, RockboxService.class);
                    intent.setAction(Intent.ACTION_MAIN);startService(intent);
                }
            });
            panel.addView(retry);
            android.widget.Button stock = new android.widget.Button(this);
            stock.setText("Switch to stock (restart)");
            stock.setOnClickListener(new android.view.View.OnClickListener() {
                public void onClick(android.view.View view) {
                    RockboxService service = RockboxService.getInstance();
                    if (service != null) {
                        service.setActivity(RockboxActivity.this);service.switchFirmware();
                    }
                }
            });
            panel.addView(stock);setContentView(panel);retry.requestFocus();
        }
        storageStatus.setText(detail);
    }
    private void showFramebuffer() {
        if (RockboxService.getInstance() != null) MediaButtonReceiver.setDpadMode(0);
        storageStatus = null;
        RockboxFramebuffer fb = new RockboxFramebuffer(this);
        setContentView(fb);fb.requestFocus();
    }
    private String storageMessage() {
        String state = android.os.Environment.getExternalStorageState();
        if (android.os.Environment.MEDIA_MOUNTED.equals(state))
            return "Starting Rockbox...";
        if (android.os.Environment.MEDIA_SHARED.equals(state))
            return "USB file transfer is active. Safely eject the card in Windows, then unplug the USB cable. Rockbox will retry automatically.";
        return "Waiting for a writable microSD card (" + state + "). Insert or mount the card; Rockbox will retry automatically.";
    }

    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState) 
    {
        /* Native loading is handled by the service, with a visible error path. */
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                             WindowManager.LayoutParams.FLAG_FULLSCREEN);
        Intent intent = new Intent(this, RockboxService.class);
        intent.setAction(Intent.ACTION_MAIN);
        intent.putExtra("callback", new ResultReceiver(new Handler(getMainLooper())) {
            private boolean unzip = false;
            private ProgressDialog loadingdialog;
            private void createProgressDialog()
            {
                loadingdialog = new ProgressDialog(RockboxActivity.this);
                loadingdialog.setMessage(getString(R.string.rockbox_extracting));
                loadingdialog.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL);
                loadingdialog.setIndeterminate(true);
                loadingdialog.setCancelable(false);
                loadingdialog.show();
            }

            @Override
            protected void onReceiveResult(final int resultCode, final Bundle resultData)
            {
                RockboxFramebuffer fb;
                switch (resultCode) {
                    case RockboxService.RESULT_INVOKING_MAIN:
                        if (loadingdialog != null)
                            loadingdialog.dismiss();
                        showFramebuffer();
                        break;
                    case RockboxService.RESULT_LIB_LOAD_PROGRESS:
                        if (loadingdialog == null)
                            createProgressDialog();
                        loadingdialog.setIndeterminate(false);
                        loadingdialog.setMax(resultData.getInt("max", 100));
                        loadingdialog.setProgress(resultData.getInt("value", 0));
                        break;
                    case RockboxService.RESULT_LIB_LOADED:
                        unzip = resultData.getBoolean("unzip");
                        break;
                    case RockboxService.RESULT_SERVICE_RUNNING:
                        if (!unzip) /* defer to RESULT_INVOKING_MAIN */
                        {
                            showFramebuffer();
                        }
                        setServiceActivity(true);
                        break;
                    case RockboxService.RESULT_STORAGE_WAIT:
                        if (loadingdialog != null) { loadingdialog.dismiss();loadingdialog = null; }
                        showStorageWait(storageMessage());
                        break;
                    case RockboxService.RESULT_ERROR_OCCURED:
                        if (loadingdialog != null) { loadingdialog.dismiss();loadingdialog = null; }
                        String error = resultData.getString("error");
                        Toast.makeText(RockboxActivity.this, error, Toast.LENGTH_LONG).show();
                        showStorageWait(error);
                        break;
                    case RockboxService.RESULT_ROCKBOX_EXIT:
                        finish();
                        break;
                }
            }
        });
        startService(intent);
    }

    private void setServiceActivity(boolean set)
    {
        RockboxService s = RockboxService.getInstance();
        if (s != null)
            s.setActivity(set ? this : null);
    }

    public void onResume()
    {
        super.onResume();
        RockboxService service = RockboxService.getInstance();
        if (service != null && service.isRockboxRunning()) {
            showFramebuffer();keyLock(false);
        } else {
            showStorageWait(storageMessage());
        }
        setVisible(true);setServiceActivity(true);
    }
    
    /* this is also called when the backlight goes off,
     * which is nice 
     */
    @Override
    protected void onPause() 
    {
        super.onPause();
        /* this will cause the framebuffer's Surface to be destroyed, enabling
         * us to disable drawing */
        setVisible(false);
        /* enable key lock */
        RockboxService service = RockboxService.getInstance();
        if (service != null && service.isRockboxRunning()) keyLock(true);
    }
    
    @Override
    protected void onStop() 
    {
        super.onStop();
        setServiceActivity(false);
    }
    
    @Override
    protected void onDestroy() 
    {
        super.onDestroy();
        setServiceActivity(false);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);

        PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
        boolean screenOn = pm.isScreenOn();
        if (hasFocus) {
            RockboxService service = RockboxService.getInstance();
            if (service != null)
                MediaButtonReceiver.setDpadMode(service.isRockboxRunning() ? 0 : 2);
        }
        /* also check if the screen is on since the activity also loose focus if screen is off while in Rockbox */
        else if (!hasFocus && screenOn && RockboxService.getInstance() != null) {
            String foregroundPackage = getForegroundPackageName(this);
            if (foregroundPackage.equals("com.mediatek.FMRadio")){
                MediaButtonReceiver.setDpadMode(1); // fm specific remapping
            } else {
                MediaButtonReceiver.setDpadMode(2); // other menus
            }
        }
    }

    private String getForegroundPackageName(Context context) {
        ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);

        try {
            List<ActivityManager.RunningTaskInfo> tasks = am.getRunningTasks(1);
            if (tasks != null && !tasks.isEmpty()) {
                return tasks.get(0).baseActivity.getPackageName();
            }
        } catch (Exception e) {
            Log.e("RockboxActivity", "Error getting foreground package", e);
        }

        return "unknown";
    }

    /* call native method to trigger key lock */
    public native static void keyLock(boolean keyLock);

}
