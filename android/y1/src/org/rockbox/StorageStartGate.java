/* Non-blocking, single-start storage gate. Rockbox GPLv2 or later. */
package org.rockbox;
public final class StorageStartGate {
    public interface Host {
        boolean mounted();
        void waiting();
        boolean start();
        void schedule(Runnable retry, long delayMs);
        void remove(Runnable retry);
    }
    private final Host host;
    private boolean started, cancelled;
    private final Runnable retry = new Runnable() { public void run() { request(); } };
    public StorageStartGate(Host host) { this.host = host; }
    /** Called on the Android main thread; waiting never sleeps or blocks it. */
    public void request() {
        if (cancelled || started) return;
        host.remove(retry);
        if (!host.mounted()) {
            host.waiting();host.schedule(retry, 1000);return;
        }
        started = true;
        if (!host.start()) started = false; // Manual retry after a load error only.
    }
    /** Initialization failed after library loading; permit explicit retry. */
    public void failed() { started = false;host.remove(retry); }
    public void cancel() { cancelled = true;host.remove(retry); }
}
