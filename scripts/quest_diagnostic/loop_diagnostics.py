"""Bounded-buffer diagnostic events; CPU snapshots only, never control decisions."""
import copy
import json
import time


class DiagnosticLog:
    """Compact JSONL, 64 KiB buffer, periodic flush; no per-row fsync or worker queue."""
    def __init__(self, path):
        self.file=path.open('x',buffering=65536)
        self.last_flush=time.monotonic()
        self.cost_ms=dict(serialize=0.,write=0.,flush=0.)
        self.rows=0

    def emit(self, event):
        start=time.monotonic()
        line=json.dumps(event,separators=(',',':'))+'\n'
        encoded=time.monotonic()
        self.file.write(line)
        written=time.monotonic()
        self.cost_ms['serialize']+=(encoded-start)*1000
        self.cost_ms['write']+=(written-encoded)*1000
        self.rows+=1
        if written-self.last_flush>=1.:self.flush()

    def flush(self):
        start=time.monotonic();self.file.flush();self.last_flush=time.monotonic()
        self.cost_ms['flush']+=(self.last_flush-start)*1000

    def close(self):
        self.flush();self.file.close()


def control_snapshot(snapshot, controller, lifecycle, measured, measured_at, tracking, preview_only=False, updated=False):
    packet=snapshot.get('packet') or {};hands={}
    for side,state in controller.states.items():
        hand=packet.get('controllers',{}).get(side,{})
        buttons=hand.get('buttons',[])
        hands[side]=dict(reason=state['reason'],ready=state['ready'],anchored=state['anchor'] is not None,
            active=not preview_only and lifecycle.state=='RUNNING' and state['reason']=='active',
            target_enabled=not preview_only and lifecycle.state=='RUNNING' and state['reason'] in ('active','anchored'),
            valid=hand.get('valid'),input_reason=hand.get('reason'),source_id=hand.get('source_id'),
            squeeze=buttons[1] if len(buttons)>1 else None,trigger=buttons[0] if buttons else None,
            rebase_button=buttons[5] if len(buttons)>5 else None,anchor=state['anchor'],
            controller_pose=[hand.get('position'),hand.get('quaternion_xyzw')])
    return copy.deepcopy(dict(observed_monotonic=time.monotonic(),episode_state=lifecycle.state,
        episode_number=lifecycle.number,hands=hands,
        input=dict(live=snapshot.get('live'),age_ms=snapshot.get('age_ms'),seq=packet.get('seq'),
                   received_monotonic=snapshot.get('received_monotonic'),visibility=packet.get('visibility'),
                   server_id=snapshot.get('server_id'),session=packet.get('session'),
                   safety_epoch=packet.get('safety_epoch'),reference_generation=packet.get('reference_generation')),
        preview=dict(valid=packet.get('preview_ok'),guard_reason=packet.get('preview_guard_reason'),
                     status=packet.get('preview_status')),
        reference_changes=controller.reference_changes if updated else [],basis=controller.basis,
        measured_pose=measured,measured_monotonic=measured_at,target_pose=controller.targets,
        raw_target_pose=controller.raw_targets if updated else {},gripper_commands=controller.grippers,
        tracking_monitor=tracking.stats if controller.practice else None))


class LoopDiagnostics:
    """One compact completion row per loop plus detailed rows only on control transitions."""
    def __init__(self, log, env, performance):
        self.log=log;self.env=env;self.performance=performance
        self.number=0;self.previous=None;self.pending=None;self.last_tick=None;self.last_summary_ms=0.

    def begin(self, tick, lifecycle, control_steps):
        if self.log is None:return
        self.number+=1
        self.pending=dict(loop_index=self.number,tick_monotonic=tick,
            previous_tick_interval_ms=None if self.last_tick is None else (tick-self.last_tick)*1000,
            phase_before=lifecycle.state,episode_before=lifecycle.number,control_steps_before=control_steps,
            sim_steps_before=self.env._sim_step_counter,log_cost_before=dict(self.log.cost_ms),
            previous_summary_emit_ms=self.last_summary_ms)
        self.last_tick=tick

    def observe(self, stage, snapshot, controller, lifecycle, measured, measured_at, tracking,
                preview_only=False, updated=False, before_update=None):
        if self.log is None:return
        with self.performance.measure('diagnostic_transition'):
            self._observe(stage,snapshot,controller,lifecycle,measured,measured_at,tracking,preview_only,updated,before_update)

    def _observe(self,stage,snapshot,controller,lifecycle,measured,measured_at,tracking,preview_only,updated,before_update):
        current=control_snapshot(snapshot,controller,lifecycle,measured,measured_at,tracking,preview_only,updated)
        before=before_update or self.previous
        changes={side:dict(before=before['hands'][side]['reason'],after=hand['reason'],
                           was_active=before['hands'][side]['active'],active=hand['active'])
                 for side,hand in current['hands'].items() if before is not None and
                 (before['hands'][side]['reason']!=hand['reason'] or before['hands'][side]['active']!=hand['active'])}
        reference_events=[]
        if updated and any((hand['rebase_button'] or {}).get('value',0)>.8 for hand in current['hands'].values()):
            reference_events.append('rebase_requested')
        if before is not None:
            if before['basis']!=current['basis']:reference_events.append('basis_changed')
            for side,hand in current['hands'].items():
                if before['hands'][side]['anchor']!=hand['anchor']:
                    reference_events.append(side+':anchor_changed:'+hand['reason'])
        if changes or current['reference_changes'] or reference_events:
            self.log.emit(dict(event='control_transition',loop_index=self.number,
                tick_monotonic=self.last_tick,stage=stage,changes=changes,before=before,after=current,
                previous_sample=self.previous,reference_events=reference_events,
                running_inactive=lifecycle.state=='RUNNING' and any(v['was_active'] and not v['active'] for v in changes.values()),
                note='Measured poses are existing pre-step samples, not additional post-step/GPU reads; pose quaternions are xyzw in the controller target frame.'))
        self.previous=current

    def finish(self, lifecycle, control_steps, recorder=None, reason='normal'):
        if self.pending is None:return
        row=self.pending;self.pending=None
        sim_steps=self.env._sim_step_counter
        before=row.pop('sim_steps_before');cost_before=row.pop('log_cost_before')
        row.update(event='loop_timing',completion=reason,phase_after=lifecycle.state,
            episode_after=lifecycle.number,control_steps_after=control_steps,
            simulation=dict(physics_steps_before=before,physics_steps_after=sim_steps,
                time_before_s=before*self.env.physics_dt,time_after_s=sim_steps*self.env.physics_dt,
                advanced_s=(sim_steps-before)*self.env.physics_dt,
                source='Python env._sim_step_counter * physics_dt; excludes any uncounted reset/warmup work'),
            performance=self.performance.report(),
            diagnostic_cost_ms={k:self.log.cost_ms[k]-v for k,v in cost_before.items()},
            async_video=recorder.video.status() if recorder and recorder.video else None)
        end=time.monotonic()
        row.update(end_monotonic=end,loop_wall_ms=(end-row['tick_monotonic'])*1000,
                   note='Includes measured sleep; excludes this summary emit, reported as previous_summary_emit_ms in the next row. Inclusive nested wall calls are not additive or GPU kernel timings.')
        self.log.emit(row);self.last_summary_ms=(time.monotonic()-end)*1000
