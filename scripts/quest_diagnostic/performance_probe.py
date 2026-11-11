"""Wall-call timing only; no GPU synchronizations or additional physics/render calls."""
import time
from contextlib import contextmanager

class PerformanceProbe:
    def __init__(self,env):
        self.original=[];self.totals={};self.counts={};self.received=None;self.first_apply=True;self.first_physics=True;self.latency={};self.render_times={};self.sleep_requested_ms=None
        targets=[(env.sim,'step','sim_step_call'),(env.sim,'render','render_call'),
            (env.scene,'update','scene_update'),(env.observation_manager,'compute','observations'),
            (env.action_manager,'process_action','process_action'),(env.action_manager,'apply_action','apply_action')]
        for name,label in (('step','env_step_total'),('reset','env_reset_total')):
            if callable(getattr(env,name,None)):targets.append((env,name,label))
        manager=getattr(env,'recorder_manager',None)
        for name in ('record_pre_step','record_post_step','record_pre_reset'):
            if callable(getattr(manager,name,None)):targets.append((manager,name,name))
        for obj,name,label in targets:
            original=getattr(obj,name);self.original.append((obj,name,original));self.totals[label]=0.;self.counts[label]=0
            def wrapped(*args,_fn=original,_label=label,**kwargs):
                start=time.monotonic()
                if self.received is not None:
                    if _label=='process_action':self.latency['receive_to_process_ms']=(start-self.received)*1000
                    if _label=='sim_step_call' and self.first_physics:
                        self.latency['receive_to_first_sim_step_ms']=(start-self.received)*1000;self.first_physics=False
                    if _label=='apply_action' and self.first_apply:
                        self.latency['receive_to_first_apply_ms']=(start-self.received)*1000;self.first_apply=False
                if _label=='render_call':self.render_times['render_begin_monotonic']=start
                try:return _fn(*args,**kwargs)
                finally:
                    end=time.monotonic();self.totals[_label]+=(end-start)*1000;self.counts[_label]+=1
                    if _label=='render_call':self.render_times['render_end_monotonic']=end
            setattr(obj,name,wrapped)
    def begin(self,received=None):
        self.received=received;self.first_apply=True;self.first_physics=True;self.latency={};self.render_times={};self.sleep_requested_ms=None
        for k in self.totals:self.totals[k]=0.;self.counts[k]=0
    @contextmanager
    def measure(self,label):
        start=time.monotonic()
        try:yield
        finally:
            self.totals[label]=self.totals.get(label,0.)+(time.monotonic()-start)*1000
            self.counts[label]=self.counts.get(label,0)+1

    def report(self):
        return dict(sleep_requested_ms=self.sleep_requested_ms,wall_call_ms=dict(self.totals),calls=dict(self.counts),**self.latency,**self.render_times,
                    note='Inclusive CPU wall timings, NOT additive GPU profiling. env_step_total includes physics/render/observations/recording/reset; sim_step_call is a host sim.step call, NOT pure physics GPU time. Asynchronous work may complete in later calls.')
    def close(self):
        for obj,name,original in reversed(self.original):setattr(obj,name,original)
