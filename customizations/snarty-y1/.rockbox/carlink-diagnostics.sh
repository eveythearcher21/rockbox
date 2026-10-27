#!/system/bin/sh
# Read-only connection diagnostics. No USB, network or system configuration changes.
set -e
out=/sdcard/.rockbox/carlink-diagnostics.txt
tmp=/sdcard/.rockbox/carlink-diagnostics.txt.tmp
{
    echo 'Rockbox Y1 car-connection capability report v1'
    date
    echo 'This report contains no serial number, accounts, Wi-Fi credentials or tokens.'
    echo
    echo '=== Platform ==='
    uname -srm || true
    for property in ro.product.model ro.product.board ro.hardware ro.product.cpu.abi ro.build.version.release ro.build.version.sdk; do
        printf '%s: ' "$property"
        getprop "$property" || true
    done
    echo
    echo '=== USB mode (read only) ==='
    for property in sys.usb.config sys.usb.state persist.sys.usb.config; do
        printf '%s: ' "$property"
        getprop "$property" || true
    done
    for file in /sys/class/android_usb/android0/functions /sys/class/android_usb/android0/enable /sys/class/android_usb/android0/idVendor /sys/class/android_usb/android0/idProduct; do
        printf '%s: ' "$file"
        if [ -r "$file" ]; then cat "$file"; else echo 'unavailable'; fi
    done
    echo
    echo '=== Gadget function names ==='
    ls /sys/class/android_usb/android0/ 2>/dev/null || echo 'android_usb sysfs interface unavailable'
    echo
    echo '=== USB controllers ==='
    ls /sys/class/udc/ 2>/dev/null || echo 'UDC sysfs interface unavailable'
    echo
    echo '=== Network interface names (no addresses) ==='
    ls /sys/class/net/ 2>/dev/null || true
    echo
    echo '=== Relevant kernel feature flags, when exposed ==='
    if [ -r /proc/config.gz ] && [ -x /system/xbin/busybox ]; then
        /system/xbin/busybox zcat /proc/config.gz 2>/dev/null | /system/xbin/busybox grep -E '^(CONFIG_USB_(GADGET|ANDROID|CONFIGFS|F_NCM|F_RNDIS|ETH|G_NCM|G_MULTI|NET)|# CONFIG_USB_(GADGET|ANDROID|CONFIGFS|F_NCM|F_RNDIS|ETH|G_NCM|G_MULTI|NET))' || true
    else
        echo 'Kernel configuration is not exposed; this does not establish lack of USB support.'
    fi
    echo
    echo 'No projection server is installed by this check.'
} > "$tmp"
mv "$tmp" "$out"
