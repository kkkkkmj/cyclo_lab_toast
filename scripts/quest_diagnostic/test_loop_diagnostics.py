"""CPU-only timing/transition tests; no simulator, GPU synchronization or live log reads."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from control import BoundedTeleop
from episode_control import EpisodeLifecycle
from loop_diagnostics import DiagnosticLog,LoopDiagnostics,control_snapshot
from performance_probe import PerformanceProbe
from tracking_monitor import TrackingMonitor
from test_control import sample,POSES


def fake_env():
    def no_op(*a,**kw):return 'unchanged'
    return NS(_sim_step_counter=0,physics_dt=.01,step=no_op,reset=no_op,
        sim=NS(step=no_op,render=no_op),scene=NS(update=no_op),observation_manager=NS(compute=no_op),
        action_manager=NS(process_action=no_op,apply_action=no_op))


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'diagnostic.jsonl'
        self.log=DiagnosticLog(self.path);self.addCleanup(self.log.close)
        self.env=fake_env();self.perf=PerformanceProbe(self.env);self.addCleanup(self.perf.close)
        self.trace=LoopDiagnostics(self.log,self.env,self.perf)
        self.life=EpisodeLifecycle();self.life.start(True)
        self.control=BoundedTeleop(POSES,1,True);self.control.practice=True
        self.snapshot=sample();self.tracking=TrackingMonitor()
        self.control.update(self.snapshot,measured=POSES)
        for h in self.snapshot['packet']['controllers'].values():h['buttons'][1]['value']=1.
        self.control.update(self.snapshot,measured=POSES);self.control.update(self.snapshot,measured=POSES)
        self.assertEqual(self.control.states['left']['reason'],'active')
        self.perf.begin();self.trace.begin(10.,self.life,0)
        self.observe()

    def observe(self,before=None):
        self.trace.observe('control_update',self.snapshot,self.control,self.life,POSES,10.,self.tracking,
                           updated=True,before_update=before)

    def rows(self):
        self.log.flush()
        return [json.loads(line) for line in self.path.read_text().splitlines()]

    def test_running_inactive_entry_and_recovery_preserve_evidence(self):
        previous=copy.deepcopy(self.trace.previous)
        self.snapshot['packet']['preview_ok']=False
        before=control_snapshot(self.snapshot,self.control,self.life,POSES,10.1,self.tracking)
        self.control.update(self.snapshot,measured=POSES);self.tracking.check(self.control,POSES,10.1)
        original=copy.deepcopy(self.control.__dict__)
        self.observe(before)
        self.assertEqual(self.control.__dict__,original)
        event=self.rows()[-1]
        self.assertTrue(event['running_inactive']);self.assertEqual(event['after']['episode_state'],'RUNNING')
        self.assertEqual(event['before']['hands']['left']['reason'],'active')
        self.assertEqual(event['after']['hands']['left']['reason'],'preview_not_live')
        self.assertTrue(event['previous_sample']['preview']['valid']);self.assertFalse(event['after']['preview']['valid'])
        self.assertEqual(event['after']['hands']['left']['squeeze']['value'],1.)
        self.assertIsNotNone(event['after']['hands']['left']['trigger'])
        self.assertEqual(event['after']['measured_pose'],json.loads(json.dumps(POSES)))
        self.assertIn('left',event['after']['tracking_monitor'])
        # Current mutations cannot overwrite the saved pre-transition snapshot.
        self.assertEqual(previous['hands']['left']['reason'],'active')
        count=len(self.rows());self.observe();self.assertEqual(len(self.rows()),count)
        self.snapshot['packet']['preview_ok']=True
        for h in self.snapshot['packet']['controllers'].values():h['buttons'][1]['value']=0.
        self.control.update(self.snapshot,measured=POSES);self.observe()
        self.assertEqual(self.rows()[-1]['after']['hands']['left']['reason'],'ready')

    def test_reference_epoch_and_manual_end_are_distinct(self):
        self.snapshot['packet']['safety_epoch']+=1
        self.control.update(self.snapshot,measured=POSES);self.observe()
        event=self.rows()[-1]
        self.assertIn('safety_epoch',event['after']['reference_changes'])
        self.assertTrue(event['running_inactive'])
        self.life.finish('manual_stop')
        for side in self.control.states:self.control.hold(side,'episode_waiting')
        self.trace.observe('episode_end',self.snapshot,self.control,self.life,None,None,self.tracking)
        event=self.rows()[-1]
        self.assertFalse(event['running_inactive']);self.assertEqual(event['after']['episode_state'],'WAITING')
        self.assertIsNone(event['after']['measured_pose'])

    def test_terminal_step_still_advances_simulation_and_waiting_does_not(self):
        with self.perf.measure('input_read'):pass
        self.env._sim_step_counter+=4
        self.life.finish('success')
        with self.perf.measure('sleep'):pass
        self.perf.sleep_requested_ms=0.
        self.trace.finish(self.life,1)
        event=self.rows()[-1]
        self.assertEqual(event['simulation']['advanced_s'],.04)
        self.assertEqual(event['phase_after'],'WAITING')
        self.assertIn('sleep',event['performance']['wall_call_ms'])
        self.perf.begin();self.trace.begin(11.,self.life,1)
        self.trace.finish(self.life,1,reason='tracking_stop')
        event=self.rows()[-1]
        self.assertEqual(event['simulation']['advanced_s'],0.)
        self.assertIsNone(event['performance']['sleep_requested_ms'])
        self.assertEqual(event['performance']['calls']['sleep'],0)
        self.assertEqual(event['completion'],'tracking_stop')
        self.assertIn('serialize',event['diagnostic_cost_ms'])

    def test_probe_times_nested_calls_without_extra_invocations(self):
        self.perf.close();self.env=fake_env();seen=[]
        def step():
            seen.append('step');self.env.sim.step(render=False)
            self.env.sim.render();self.env.observation_manager.compute();return 42
        self.env.step=step;probe=PerformanceProbe(self.env)
        try:
            probe.begin();self.assertEqual(self.env.step(),42)
            report=probe.report();self.assertEqual(seen,['step'])
            for name in ('env_step_total','sim_step_call','render_call','observations'):
                self.assertEqual(report['calls'][name],1)
                self.assertGreaterEqual(report['wall_call_ms'][name],0)
            self.assertNotIn('physics_call',report['wall_call_ms'])
            self.assertIn('NOT pure physics',report['note'])
            with self.assertRaises(ValueError):
                with probe.measure('failing_call'):raise ValueError('test')
            self.assertEqual(probe.report()['calls']['failing_call'],1)
        finally:probe.close()

    def test_disabled_diagnostics_do_not_sample_or_write(self):
        trace=LoopDiagnostics(None,object(),object())
        trace.begin(0.,object(),0)
        trace.observe('none',None,None,None,None,None,None)
        trace.finish(None,0)
        self.assertIsNone(trace.previous)

    def test_buffer_does_not_flush_each_event(self):
        with patch.object(self.log.file,'flush',wraps=self.log.file.flush) as flush:
            self.log.last_flush=__import__('time').monotonic()
            for i in range(10):self.log.emit(dict(event='test',value=i))
            self.assertEqual(flush.call_count,0)
            self.log.last_flush-=2
            self.log.emit(dict(event='test',value=10));self.assertEqual(flush.call_count,1)


class ActualLoopTests(unittest.TestCase):
    def run_loop(self, mode):
        """Execute the real launcher while-loop with fake env I/O, not a copied loop."""
        import ast
        import queue
        import time
        import torch
        from episode_control import ButtonEdges,episode_result
        from display_status import display_status
        path=Path(__file__).with_name('teleop_toast.py')
        tree=ast.parse(path.read_text())
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.While) and 'app.is_running' in ast.unparse(n.test))
        with tempfile.TemporaryDirectory() as tmp:
            log=DiagnosticLog(Path(tmp)/'trace.jsonl')
            env=fake_env();actions=[]
            def step(action):
                actions.append(action.tolist());env._sim_step_counter+=4
                return None,None,torch.tensor([mode=='success']),torch.tensor([False])
            env.step=step;env.device='cpu'
            perf=PerformanceProbe(env);trace=LoopDiagnostics(log,env,perf)
            life=EpisodeLifecycle();life.start(True)
            life.pending_result=episode_result('success') if mode=='success' else None
            control=BoundedTeleop(POSES,1,True);control.practice=True
            snapshot=sample();tracking=TrackingMonitor()
            control.update(snapshot,measured=POSES)
            for hand in snapshot['packet']['controllers'].values():hand['buttons'][1]['value']=1.
            control.update(snapshot,measured=POSES);control.update(snapshot,measured=POSES)
            trace.previous=control_snapshot(snapshot,control,life,POSES,time.monotonic(),tracking)
            if mode=='inactive':snapshot['packet']['preview_ok']=False
            if mode=='stall':tracking.check=lambda *a:('left','tracking_stall')
            commands=queue.Queue()
            if mode=='manual':commands.put('s')
            calls=iter([True,False]);now=time.monotonic()
            ns=dict(shutdown=NS(requested=False),app=NS(is_running=lambda:next(calls)),args=NS(keep_open=True,bridge_dir=Path(tmp),
                record_seconds=0,preview_only=False,preview_hz=10),start=now,previous=now,time=time,
                perf=perf,env=env,loop_trace=trace,read_input=lambda path:snapshot,lifecycle=life,controller=control,
                episode_steps=0,edges=ButtonEdges(),commands=commands,record_dir=None,recorder=None,timeline=None,
                diagnostic_log=log,tracking=tracking,poses=lambda:copy.deepcopy(POSES),torch=torch,dt=.04,
                contact_probe=None,display_status=display_status,start_blocked=False,control_snapshot=control_snapshot,
                preview_time=now+1e6,report_time=now+1e6,gripper_audit_time=now+1e6,frame_id=0,json=json,
                begin_waiting_audit=lambda:None,report_gripper_runtime=lambda phase:None)
            try:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
            finally:perf.close();log.close()
            rows=[json.loads(line) for line in (Path(tmp)/'trace.jsonl').read_text().splitlines()]
            return rows,actions,life

    def test_real_loop_inactive_still_steps_and_records_full_iteration(self):
        rows,actions,life=self.run_loop('inactive')
        self.assertEqual(life.state,'RUNNING');self.assertEqual(len(actions),1)
        self.assertEqual(actions[0][0][:12],[0.]*12)
        transition=next(x for x in rows if x['event']=='control_transition')
        self.assertTrue(transition['running_inactive'])
        decision=next(x for x in rows if x['event']=='decision')
        self.assertEqual(decision['teleop']['hands']['left']['control_reason'],'preview_not_live')
        timing=rows[-1];self.assertEqual(timing['event'],'loop_timing')
        self.assertEqual(timing['simulation']['advanced_s'],.04)
        self.assertEqual(timing['performance']['calls']['input_read'],2)
        self.assertEqual(timing['performance']['calls']['env_step_total'],1)
        self.assertEqual(timing['performance']['calls']['sleep'],1)

    def test_real_loop_stall_skips_physics_and_sleep_but_not_transition_or_timing(self):
        rows,actions,life=self.run_loop('stall')
        self.assertEqual(actions,[]);self.assertEqual(life.state,'WAITING')
        transition=next(x for x in rows if x['event']=='control_transition')
        self.assertEqual(transition['after']['hands']['left']['reason'],'tracking_stall')
        self.assertIsNotNone(transition['after']['measured_pose'])
        self.assertEqual(rows[-1]['completion'],'tracking_stop')
        self.assertEqual(rows[-1]['simulation']['advanced_s'],0.)
        self.assertNotIn('sleep',rows[-1]['performance']['calls'])

    def test_real_loop_terminal_action_and_manual_stop(self):
        rows,actions,life=self.run_loop('success')
        decision=next(x for x in rows if x['event']=='decision')
        self.assertEqual(len(actions),1);self.assertEqual(life.state,'WAITING')
        self.assertIsNotNone(decision['action'])
        self.assertEqual(decision['performance']['simulation_dt'],.04)
        self.assertEqual(rows[-1]['simulation']['advanced_s'],.04)
        rows,actions,life=self.run_loop('manual')
        self.assertEqual(actions,[]);self.assertEqual(life.reason,'manual_stop')
        self.assertEqual(rows[-1]['simulation']['advanced_s'],0.)


if __name__=='__main__':unittest.main()
