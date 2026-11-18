/* Exercises the actual asynchronous gate without Android or real delays. */
package org.rockbox;
public final class StorageStartGateTest {
    static final class Host implements StorageStartGate.Host {
        boolean mounted, startSucceeds = true;
        int starts, waits, scheduled;
        Runnable pending;
        StorageStartGate gate;
        public boolean mounted() { return mounted; }
        public void waiting() { waits++; }
        public boolean start() {
            starts++;gate.request(); // Reentrant requests cannot start twice.
            return startSucceeds;
        }
        public void schedule(Runnable retry, long delay) {
            check(delay == 1000 || delay == 5000);check(pending == null);scheduled++;pending = retry;
        }
        public void remove(Runnable retry) { if (pending == retry) pending = null; }
        void tick() { Runnable run = pending;check(run != null);pending = null;run.run(); }
        void init() { gate = new StorageStartGate(this); }
    }
    static void check(boolean condition) { if (!condition) throw new AssertionError(); }
    public static void main(String[] args) {
        Host host = new Host();host.init();host.gate.request();
        check(host.starts == 0 && host.waits == 1 && host.pending != null);
        // Missing/shared/unmounted card: repeated requests never enter the core.
        for (int i=0;i<20;i++) { host.gate.request();host.tick(); }
        check(host.starts == 0 && host.pending != null);
        host.mounted = true;host.tick();
        check(host.starts == 1 && host.pending == null);
        host.gate.request();check(host.starts == 1);
        Host cancelled = new Host();cancelled.init();cancelled.gate.request();
        Runnable old = cancelled.pending;cancelled.gate.cancel();
        cancelled.mounted = true;old.run();cancelled.gate.request();
        check(cancelled.starts == 0 && cancelled.pending == null);
        Host ready = new Host();ready.mounted = true;ready.init();ready.gate.request();
        check(ready.starts == 1 && ready.scheduled == 0);
        ready.gate.failed();ready.gate.request();
        check(ready.starts == 2 && ready.scheduled == 1 && ready.pending == null);
        Host failure = new Host();failure.mounted = true;failure.startSucceeds = false;
        failure.init();failure.gate.request();
        check(failure.starts == 1 && failure.pending != null);
        failure.startSucceeds = true;failure.tick();
        check(failure.starts == 2 && failure.pending == null);
        System.out.println("PASS: storage unavailable polling, nonblocking deferred start, mounted transition, single/reentrant start, cancelled callbacks and automatic retry after load failure");
    }
}
