"""CPU signal/relay tests. Never invoke the real Docker client or active processes."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from graceful_shutdown import Shutdown

ROOT=Path(__file__).resolve().parents[2]

class ShutdownTests(unittest.TestCase):
    def test_latch_and_cleanup(self):
        stop=Shutdown();stop.request(signal.SIGINT);stop.request(signal.SIGTERM)
        self.assertEqual(stop.reason,'signal_SIGINT')
        calls=[]
        stop.step('save',lambda:calls.append('save'));stop.step('save',lambda:calls.append('duplicate'))
        stop.step('failure',lambda:(_ for _ in ()).throw(ValueError('mock close failure')))
        stop.step('app',lambda:calls.append('app'))
        self.assertEqual(calls,['save','app'])

    def test_terminal_interrupt_pipeline_and_initialization(self):
        for phase in ('initializing','WAITING','RUNNING'):
            for tee in (False,True):
                with self.subTest(phase=phase,tee=tee),tempfile.TemporaryDirectory() as tmp:
                    d=Path(tmp)
                    (d/'probe.py').write_text('''import os,signal,time,sys,json
from pathlib import Path
sys.path.insert(0,os.environ['TOOLS'])
from graceful_shutdown import Shutdown
stop=Shutdown();stop.install()
d=Path(os.environ['MOCK_DIR']);(d/'boot').touch()
if os.environ['PHASE']=='initializing':time.sleep(.4)
(d/'pid').write_text(str(os.getpid()))
print('READY '+os.environ['PHASE'],flush=True)
while not stop.requested:time.sleep(.01)
# Simulate work already in progress when the request arrives.
time.sleep(.15)
stop.step('save',lambda:(d/'saved').write_text(stop.reason))
stop.step('app',lambda:print('APP_CLOSED',flush=True))
''')
                    (d/'docker').write_text('''#!/usr/bin/env python3
import os,sys,subprocess,signal
from pathlib import Path
d=Path(os.environ['MOCK_DIR'])
if sys.argv[1]=='exec':
 try:os.kill(int((d/'pid').read_text()),signal.SIGINT)
 except (FileNotFoundError,ProcessLookupError):sys.exit(1)
else:
 assert '-T' in sys.argv and '--name' in sys.argv
 sys.exit(subprocess.call([sys.executable,str(d/'probe.py')]))
''')
                    (d/'docker').chmod(0o755)
                    env=dict(os.environ,PATH=tmp+':'+os.environ['PATH'],MOCK_DIR=tmp,TOOLS=str(ROOT/'scripts/tools'),PHASE=phase)
                    cmd=[sys.executable,str(ROOT/'scripts/tools/mj_signal_relay.py'),'docker','compose','--mj-command','fake-service']
                    import shlex
                    shell=shlex.join(cmd)+(' 2>&1 | tee '+shlex.quote(str(d/'tee.log')) if tee else '')
                    with (d/'stdout.log').open('w') as out:
                        proc=subprocess.Popen(['bash','-c',shell],start_new_session=True,env=env,stdout=out,stderr=out)
                        try:
                            deadline=time.monotonic()+8
                            ready=d/('boot' if phase=='initializing' else 'pid')
                            while not ready.exists() and time.monotonic()<deadline:time.sleep(.02)
                            self.assertTrue(ready.exists())
                            os.killpg(proc.pid,signal.SIGINT)
                            time.sleep(.05);os.killpg(proc.pid,signal.SIGINT)
                            proc.wait(timeout=10)
                            self.assertEqual((d/'saved').read_text(),'signal_SIGINT')
                            pid=int((d/'pid').read_text())
                            with self.assertRaises(ProcessLookupError):os.kill(pid,0)
                        finally:
                            if proc.poll() is None:proc.kill();proc.wait()

if __name__=='__main__':unittest.main()
