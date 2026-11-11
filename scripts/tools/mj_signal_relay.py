"""Own one Compose run; relay terminal interrupts to its registered Python PID.

Compose runs without a TTY in an isolated session. A closed tee pipe does not kill
Compose or the simulation: keep draining output to a unique local recovery log.
"""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid


def main(command):
    name='cyclo-mj-run-'+uuid.uuid4().hex
    requested=[]
    def request(sig,frame):
        if not requested:requested.append(sig)
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,request)
    # command ends with compose options; append the owned run and original arguments.
    split=command.index('--mj-command')
    cmd=command[:split]+['run','--rm','--no-deps','-T','--name',name,'--env','MJ_SIGNAL_RELAY=1']+command[split+1:]
    log=tempfile.NamedTemporaryFile(prefix=name+'-',suffix='.log',delete=False)
    print(f'MJ_RUN container={name} recovery_log={log.name}',flush=True)
    child=subprocess.Popen(cmd,start_new_session=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    def drain():
        broken=False
        while True:
            chunk=os.read(child.stdout.fileno(),65536)
            if not chunk:break
            log.write(chunk);log.flush()
            if not broken:
                try:sys.stdout.buffer.write(chunk);sys.stdout.buffer.flush()
                except BrokenPipeError:
                    broken=True
                    os.dup2(os.open(os.devnull,os.O_WRONLY),sys.stdout.fileno())
        log.close()
    reader=threading.Thread(target=drain);reader.start()
    sent=False;last=0
    while child.poll() is None:
        if requested and not sent and time.monotonic()-last>.5:
            last=time.monotonic()
            # Exact PID in this uniquely named container; no process-name matching.
            code='read -r pid < /tmp/cyclo-mj-python.pid; case "$pid" in ""|*[!0-9]*) exit 2;; esac; kill -s '+signal.Signals(requested[0]).name.removeprefix('SIG')+' "$pid"'
            try:
                result=subprocess.run(['docker','exec',name,'/bin/sh','-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
                sent=result.returncode==0
            except subprocess.TimeoutExpired:pass
            if sent:
                message=f'MJ_SIGNAL sent={signal.Signals(requested[0]).name} container={name}\n'
                with open(log.name,'ab') as f:f.write(message.encode())
                try:
                    with open('/dev/tty','w') as tty:tty.write(message+'Shutdown progress: '+log.name+'\n')
                except OSError:pass
        time.sleep(.1)
    reader.join()
    with open(log.name,'ab') as f:f.write(f'MJ_RUN_EXIT code={child.returncode} signal_forwarded={sent}\n'.encode())
    return child.returncode

if __name__=='__main__':sys.exit(main(sys.argv[1:]))
