"""Cooperative shutdown: handlers only latch a request; cleanup runs in normal code."""
import signal
import threading
import time

class ShutdownRequested(BaseException):
    pass

class Shutdown:
    def __init__(self):
        self.signum=None
        self.completed=set()

    def install(self):
        for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,self.request)

    def request(self,signum,frame=None):
        if self.signum is None:self.signum=signum

    @property
    def requested(self):return self.signum is not None

    @property
    def reason(self):return 'signal_'+signal.Signals(self.signum).name if self.requested else None

    def checkpoint(self):
        if self.requested:raise ShutdownRequested(self.reason)

    def step(self,name,callback):
        if name in self.completed:return
        self.completed.add(name)
        began=time.monotonic();done=threading.Event()
        def report():
            while not done.wait(5):print(f'SHUTDOWN_WAIT stage={name} seconds={time.monotonic()-began:.1f}',flush=True)
        print(f'SHUTDOWN_BEGIN stage={name}',flush=True)
        watcher=threading.Thread(target=report,daemon=True);watcher.start()
        try:callback()
        except BaseException as error:print(f'SHUTDOWN_ERROR stage={name} error={error!r}',flush=True)
        finally:
            done.set();watcher.join()
            print(f'SHUTDOWN_END stage={name} seconds={time.monotonic()-began:.3f}',flush=True)

shutdown=Shutdown()
