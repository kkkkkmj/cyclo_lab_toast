"""Explicit bounded Quest episodes on fixed toast layouts; standard diagnostic recorder."""
import argparse
from contextlib import nullcontext
import fcntl
import hashlib
import json
from pathlib import Path
import queue
import secrets
import sys
import threading
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from graceful_shutdown import shutdown, ShutdownRequested
shutdown.install()
from view_make_toast_scenario import resolve_selection, add_group_arguments
from toast_recording_metadata import (DEFAULT_MANIFEST,create_diagnostic,finalize_diagnostic,
    validate_recording_args,applied_reset_poses,manifest_bytes)
from toast_overview import overview_cfg,position_overview
from bridge import read_input
from preview import publish_preview,stop_preview
from preview_encoding import encode_native_preview
from control import BoundedTeleop,norm,sub,qrotate,qinv
from episode_control import EpisodeLifecycle,ButtonEdges,can_start,capture_termination_results
from display_status import display_status,start_blockers
from diagnostic_recorder import DiagnosticRecorder
from practice_options import add_arguments,options,configure
from teleop_gripper_options import configure_right_j3_speed,configure_right_j1_speed
from teleop_slave_gains import configure as configure_slave_gains, readback as gripper_readback, validate_options as validate_gripper_options
from performance_probe import PerformanceProbe
from loop_diagnostics import DiagnosticLog,LoopDiagnostics,control_snapshot
from tracking_monitor import TrackingMonitor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'imitation_learning/isaaclab_recorder'))
from replay_scene_audit import TimelineProbe
from replay_plate_audit import plate_checkpoint,plate_configuration,step_with_first_physics_checkpoint

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bridge-dir',required=True,type=Path)
parser.add_argument('--duration',type=float,default=90)
parser.add_argument('--keep-open',action='store_true',help='Ignore wall duration; wait between episodes until Ctrl+C/q')
parser.add_argument('--preview-only',action='store_true')
parser.add_argument('--enable-grippers',action='store_true')
gripper_speed_options=parser.add_mutually_exclusive_group()
gripper_speed_options.add_argument('--right-gripper-j3-speed-2p2',action='store_true',
                    help='VR comparison B: only right gripper joint3 simulation speed limit becomes 2.2 rad/s; default is unchanged')
gripper_speed_options.add_argument('--right-gripper-j1-speed-6p5',action='store_true',
                    help='Legacy comparison C: keeps right master at 6.5 rad/s; v2 now defaults both masters to 6.5')
parser.add_argument('--gripper-trigger-official-binary',action='store_true',help='VR input only: trigger <0.5 opens to 0rad, otherwise closes to 1rad through existing toast action')
parser.add_argument('--gripper-slave-gains-official',action='store_true',help='Retired soft-gain option: rejected; current v2 slave gains are fixed at 100/4')
parser.add_argument('--operator',choices=('operator_A','operator_B'))
parser.add_argument('--scenario_index',type=int)
parser.add_argument('--scenario_id')
parser.add_argument('--scenario_manifest',default=str(DEFAULT_MANIFEST))
add_group_arguments(parser)
parser.add_argument('--seed',type=int,default=1)
parser.add_argument('--contact-diagnostic',type=Path,help='Opt-in per-physics-step gripper audit JSONL; new file only')
parser.add_argument('--diagnostic-log',type=Path,help='New JSONL trace of decision inputs/states; not demonstration data')
parser.add_argument('--record-dir',type=Path,help='New output directory for raw Isaac Lab demonstrations and simulation camera MP4; never overwrite')
parser.add_argument('--record-seconds',type=float,default=0,help='Auto-save after this many wall seconds; default 0 waits for episode end')
add_arguments(parser)
known,_=parser.parse_known_args()
try:
    validate_gripper_options(known.gripper_slave_gains_official,known.right_gripper_j1_speed_6p5,known.right_gripper_j3_speed_2p2)
    if known.gripper_trigger_official_binary and (not known.enable_grippers or known.gripper_slave_gains_official or known.right_gripper_j1_speed_6p5 or known.right_gripper_j3_speed_2p2):
        raise ValueError('Binary trigger comparison requires --enable-grippers and baseline gains/speeds')
    selected_id=resolve_selection(known)
    validate_recording_args(known)
    control_settings=options(known)
    if (Path(known.scenario_manifest).resolve()==DEFAULT_MANIFEST.resolve()
            and known.operator=='operator_B' and known.scenario_index==1 and selected_id!='toast_v20261108_041'):
        raise ValueError('Operator B first assignment differs from toast_v20261108_041')
except (ValueError,KeyError,OSError) as error:parser.error(str(error))
if not (known.bridge_dir/'input.json').exists():parser.error('Start the input server with this --bridge-dir first')
app=env=recorder=timeline=diagnostic_log=perf=contact_probe=loop_trace=lock=None
record_dir=metadata=None
run_id=secrets.token_hex(12);episode_steps=0;exit_reason='normal_exit'
lifecycle=EpisodeLifecycle()
lock_owned=False
try:
    lock=(known.bridge_dir/'.simulation.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:parser.error('A test already owns this bridge; it was not stopped')
    lock_owned=True
    shutdown.checkpoint()
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(parser)
    args=parser.parse_args()
    # Fresh argparse namespace: also resolve group into parent operator/index for recording.
    selected_id=resolve_selection(args)
    if args.duration<=0:parser.error('--duration must be positive (or use --keep-open)')
    record_dir=metadata=None
    if args.record_dir:
        record_dir,metadata=create_diagnostic(args.record_dir,args.scenario_manifest,args.operator,
                                             selected_id,args.scenario_index,seed=args.seed)
        args.scenario_manifest=str(record_dir/'manifest.json')
    raw,_=manifest_bytes(args.scenario_manifest)
    manifest_hash=hashlib.sha256(raw).hexdigest()
    print(f'SCENARIO_SELECTED operator={args.operator} index={args.scenario_index} id={selected_id or "original"} seed={args.seed} manifest={args.scenario_manifest} manifest_sha256={manifest_hash}',flush=True)
    args.enable_cameras=True
    shutdown.checkpoint()
    app=AppLauncher(args).app
    shutdown.install()
    shutdown.checkpoint()
    import gymnasium as gym
    import torch
    from PIL import Image
    import cyclo_lab  # noqa: F401
    from isaaclab_tasks.utils.parse_cfg import parse_env_cfg

    TASK='Cyclo-Make-Toast-FFW-BG2-Bimanual-IK-Rel-v2'
    env=recorder=timeline=diagnostic_log=perf=contact_probe=loop_trace=None
    episode_steps=0
    run_id=secrets.token_hex(12);frame_id=0;last_capture=None;exit_reason='normal_exit'
    lifecycle=EpisodeLifecycle();edges=ButtonEdges();commands=queue.Queue()

    def console():
        for line in sys.stdin:
            if line.strip().lower() in ('n','s','q'):commands.put(line.strip().lower())
    if args.diagnostic_log:
        args.diagnostic_log.parent.mkdir(parents=True,exist_ok=True)
        diagnostic_log=DiagnosticLog(args.diagnostic_log)
        diagnostic_log.emit(dict(event='begin',run_id=run_id,scenario_id=selected_id,seed=args.seed))
    cfg=parse_env_cfg(TASK,device=args.device,num_envs=1)
    # Native reset renders after state/kinematic reset and before obs_buf compute.
    # Camera.reset marks buffers outdated; observation reads refresh them at time zero.
    cfg.rerender_on_reset=True
    print('RESET_RGB_CONTRACT native_rerender_on_reset=True physics_steps=0',flush=True)
    cfg.scenario_id=selected_id;cfg.scenario_manifest=args.scenario_manifest;cfg.seed=args.seed
    # Observation-only extra camera; original cameras and policy observations untouched.
    cfg.scene.replay_overview=overview_cfg()
    configure_slave_gains(cfg,args.gripper_slave_gains_official)
    configure_right_j3_speed(cfg,args.right_gripper_j3_speed_2p2)
    configure_right_j1_speed(cfg,args.right_gripper_j1_speed_6p5)
    if record_dir:
        from isaaclab.envs.mdp.recorders.recorders_cfg import ActionStateRecorderManagerCfg
        from isaaclab.managers import DatasetExportMode
        cfg.env_name=TASK;cfg.recorders=ActionStateRecorderManagerCfg()
        cfg.recorders.dataset_export_dir_path=str(record_dir);cfg.recorders.dataset_filename='dataset'
        cfg.recorders.dataset_export_mode=DatasetExportMode.EXPORT_ALL
        cfg.recorders.export_in_record_pre_reset=False
        metadata['reset_rgb_contract']={'native_rerender_on_reset':cfg.rerender_on_reset,'extra_physics_steps':0}
        metadata['timing']=dict(physics_dt=cfg.sim.dt,decimation=cfg.decimation,
            render_interval=cfg.sim.render_interval,control_dt=cfg.sim.dt*cfg.decimation)
    # Physics, rewards and 240-second timeout remain; success uses the current task predicate.
    shutdown.checkpoint()
    env=gym.make(TASK,cfg=cfg).unwrapped
    shutdown.checkpoint()
    capture_termination_results(env.termination_manager,lifecycle)
    if record_dir:
        audit_dir=record_dir/'record_audit';audit_dir.mkdir()
        env._replay_audit_dir=str(audit_dir)
        timeline=TimelineProbe(env);timeline.mark('before_startup_reset')
    env.reset(seed=args.seed)
    gripper_reference=None
    def report_gripper_runtime(phase):
        global gripper_reference
        row=gripper_readback(env.scene['robot'],phase,args.gripper_slave_gains_official,
            args.right_gripper_j1_speed_6p5,args.right_gripper_j3_speed_2p2,gripper_reference,
            slave_gains=(cfg.scene.robot.actuators['gripper_slave'].stiffness,
                         cfg.scene.robot.actuators['gripper_slave'].damping))
        if gripper_reference is None:gripper_reference=row
        print('GRIPPER_RUNTIME_OK '+json.dumps(row),flush=True)
        if diagnostic_log:diagnostic_log.emit(row)
    report_gripper_runtime('after_startup_reset')
    if timeline:timeline.mark('after_startup_reset')
    reset_poses=applied_reset_poses(env,args.scenario_manifest,selected_id)
    position_overview(env)
    assert env.action_manager.active_terms==['left_arm','right_arm','left_gripper','right_gripper','lift']
    assert env.action_manager.total_action_dim==15
    for side in ('left','right'):
        term=env.action_manager.get_term(side+'_arm')
        assert term.cfg.controller.use_relative_mode and term.cfg.controller.command_type=='pose'
        assert term.cfg.controller.ik_method=='dls' and term.cfg.scale==.3
    dt=env.step_dt;robot=env.scene['robot']
    assert env.action_manager.get_term('lift').cfg.scale==.25 and env.action_manager.get_term('lift').cfg.offset==-.25
    def poses():
        result={}
        for side in ('left','right'):
            p,q=env.action_manager.get_term(side+'_arm')._compute_frame_pose()
            q=q[0].tolist();result[side]=(p[0].tolist(),q[1:]+q[:1])
        return result
    def new_controller():
        lift=float(robot.data.joint_pos[0,robot.joint_names.index('lift_joint')])
        result=configure(BoundedTeleop(poses(),max(-1.,min(1.,(lift+.25)/.25)),args.enable_grippers),control_settings)
        result.gripper_trigger_official_binary=args.gripper_trigger_official_binary
        root_pos=(robot.data.root_pos_w[0]-env.scene.env_origins[0]).tolist()
        root_q=robot.data.root_quat_w[0].tolist();root_q=root_q[1:]+root_q[:1]
        bread={n:qrotate(qinv(root_q),sub(v['position_m'],root_pos)) for n,v in reset_poses.items() if n.startswith('bread_') and n!='bread_shelf'}
        print('WORKSPACE_RESET '+json.dumps(dict(frame='robot root',wrists=result.home,bread_centers=bread,
            center_distances={s:{n:norm(sub(p,result.home[s][0])) for n,p in bread.items()} for s in result.home})),flush=True)
        return result
    gripper_ids=[robot.joint_names.index(f'gripper_{s}_joint{i}') for s in ('l','r') for i in range(1,5)]
    right_names=[f'gripper_r_joint{i}' for i in range(1,5)]
    right_ids=[robot.joint_names.index(name) for name in right_names]
    right_limits=robot.root_physx_view.get_dof_max_velocities()[0,right_ids].detach().cpu().tolist()
    print('RIGHT_GRIPPER_VELOCITY_LIMIT_RAD_S '+json.dumps(dict(zip(right_names,right_limits))),flush=True)
    if diagnostic_log:
        diagnostic_log.emit(dict(event='joint_configuration',joint_names=list(robot.joint_names),
            soft_position_limits=robot.data.soft_joint_pos_limits[0].detach().cpu().tolist(),
            velocity_limits=robot.data.joint_vel_limits[0].detach().cpu().tolist()))
    gripper_audit_time=0.
    controller=new_controller()
    tracking=TrackingMonitor(control_settings['tracking_stall_seconds'])
    print('CONTROL_SETTINGS '+json.dumps(control_settings),flush=True)
    print('GRIPPER_INPUT '+json.dumps(dict(mode='binary_0_1rad' if args.gripper_trigger_official_binary else 'existing_analog',threshold=.5,closed_action=1.-2./1.1 if args.gripper_trigger_official_binary else -1.)),flush=True)
    if args.gripper_trigger_official_binary:
        for side in ('left','right'):
            term=env.action_manager.get_term(side+'_gripper')
            for trigger in (0.,.49,.5,1.):
                command=controller.gripper_command(trigger)
                term.process_actions(torch.tensor([[command]],device=env.device))
                torch.testing.assert_close(term.processed_actions,torch.full_like(term.processed_actions,0. if trigger<.5 else 1.),rtol=0,atol=2e-7)
            term.process_actions(torch.ones((1,1),device=env.device))
        print('GRIPPER_BINARY_TARGET_CONTRACT_OK: actual processor 0/1rad; no physics step',flush=True)
    for left_grip,right_grip in ((1,1),(-1,1),(1,-1),(.25,-.75)):
        sample=torch.tensor([[.001,-.002,.003,.004,-.005,.006]*2+[left_grip,right_grip,controller.lift_action]],device=env.device)
        targets=env.action_to_target_eef_pose(sample)
        restored=env.target_eef_pose_to_action({k:v[0] for k,v in targets.items()},
            {k:v[0] for k,v in env.actions_to_gripper_actions(sample).items()})
        torch.testing.assert_close(restored,sample[0],atol=3e-5,rtol=5e-4)
    print('ACTION_CONTRACT_OK: unchanged 15D arms + independent analog grippers + lift',flush=True)
    if metadata:
        metadata.update(applied_reset_poses=reset_poses,seed=args.seed,
                        position_scale=controller.position_scale,rotation_scale=controller.rotation_scale,
                        max_translation_m=controller.max_translation,max_rotation_deg=control_settings['max_rotation_deg'],
                        control_settings=control_settings,grippers=('trigger_binary_0_1rad' if args.gripper_trigger_official_binary else 'trigger_analog') if args.enable_grippers else 'open',lift='fixed_at_reset')
        recorder=DiagnosticRecorder(env,metadata,lifecycle)
    def begin_waiting_audit():
        if timeline:
            env._replay_audit_episode=f'demo_{recorder.saved}'
            timeline.mark('before_waiting_renders')
    begin_waiting_audit()
    if not sys.stdin.closed:threading.Thread(target=console,daemon=True).start()
    print(f'RECORD_CONFIG enabled={bool(recorder)} path={record_dir} auto_stop_wall_seconds={args.record_seconds}',flush=True)
    print('READY / WAITING: X(left) or n+Enter = RESET & START; A(right) or s+Enter = SAVE & WAIT; Ctrl+C/q = exit.',flush=True)
    print('PREVIEW ONLY; no controller motion or recording' if args.preview_only else 'Release both squeezes before START, then re-squeeze to move.',flush=True)
    perf=PerformanceProbe(env)
    if recorder:recorder.performance=perf
    loop_trace=LoopDiagnostics(diagnostic_log,env,perf)
    if args.contact_diagnostic:
        from contact_probe import ContactProbe
        contact_probe=ContactProbe(env,args.contact_diagnostic,run_id)
    start=previous=time.monotonic();preview_time=report_time=0.;episode_start=None
    start_blocked=False
    with torch.inference_mode():
        while not shutdown.requested and app.is_running() and (args.keep_open or time.monotonic()-start<args.duration):
            tick=time.monotonic();perf.begin()
            sim_steps_before=env._sim_step_counter
            loop_trace.begin(tick,lifecycle,episode_steps)
            with perf.measure('input_read'):
                snapshot=read_input(args.bridge_dir)
            phase_before=lifecycle.state
            reasons_before={s:v['reason'] for s,v in controller.states.items()}
            current=None;action_values=None;measured_time=None;target_generated_time=None
            record_sample_monotonic=None;control_updated=False;before_control=None
            with perf.measure('episode_commands'):
                requested=edges.commands(snapshot)
                while not commands.empty():requested.append(commands.get_nowait())
                if record_dir:
                    for filename,cmd in (('start_recording','n'),('stop_recording','s')):
                        path=record_dir/filename
                        if path.exists():path.unlink();requested.append(cmd)
                if 'q' in requested:exit_reason='operator_exit';break
                expired=recorder and recorder.active and args.record_seconds>0 and tick-episode_start>=args.record_seconds
                if lifecycle.state=='RUNNING' and ('s' in requested or expired):
                    reason='short_test_duration' if expired else 'manual_stop'
                    if recorder:recorder.finish(reason)
                    if timeline:timeline.mark('after_record_finish')
                    begin_waiting_audit()
                    lifecycle.finish(reason)
                    for side in controller.states:controller.hold(side,'episode_waiting')
                    print('EPISODE_WAITING '+reason,flush=True)
                elif 'n' in requested and lifecycle.state=='WAITING':
                    allowed=args.preview_only or can_start(snapshot)
                    if lifecycle.start(allowed):
                        start_blocked=False
                        if timeline:
                            env._replay_audit_episode=f'demo_{recorder.saved}'
                            timeline.mark('after_waiting_renders');timeline.mark('before_episode_reset')
                        env.reset(seed=args.seed)
                        report_gripper_runtime('after_episode_reset')
                        if timeline:timeline.mark('after_episode_reset')
                        reset_poses=applied_reset_poses(env,args.scenario_manifest,selected_id)
                        position_overview(env);controller=new_controller();episode_steps=0
                        tracking=TrackingMonitor(control_settings['tracking_stall_seconds'])
                        if timeline:
                            plate_configuration(env,metadata['timing'])
                            plate_checkpoint(env,'after_reset_before_physics',env.scene.get_state(is_relative=True))
                        if recorder:
                            with perf.measure('record_start'):
                                recorder.start(lifecycle.number,reset_poses,args.seed)
                        episode_start=time.monotonic()
                        print(f'EPISODE_STARTED {lifecycle.number} seed={args.seed}; release/re-squeeze required',flush=True)
                    else:
                        start_blocked=True
                        print('START_BLOCKED: '+', '.join(start_blockers(snapshot)),flush=True)
            step_start=time.monotonic()
            decision_time=time.monotonic()
            if lifecycle.state=='RUNNING':
                with perf.measure('measured_pose_read'):
                    current=poses()
                measured_time=time.monotonic()
                with perf.measure('input_read'):
                    snapshot=read_input(args.bridge_dir)
                decision_time=time.monotonic()
                perf.received=snapshot.get('received_monotonic')
                if diagnostic_log:
                    with perf.measure('diagnostic_snapshot'):
                        before_control=control_snapshot(snapshot,controller,lifecycle,current,measured_time,tracking,args.preview_only)
                with perf.measure('control_update'):
                    if not args.preview_only:
                        controller.update(snapshot,loop_gap=tick-previous>.25,measured=current)
                        control_updated=True
                target_generated_time=time.monotonic()
                if controller.practice:
                    with perf.measure('tracking_monitor'):
                        fault=tracking.check(controller,current,time.monotonic())
                    if fault:
                        if recorder:recorder.finish(fault[1])
                        lifecycle.finish(fault[1])
                        for side in controller.states:controller.hold(side,fault[1])
                        print('PRACTICE_STOP '+json.dumps(dict(side=fault[0],reason=fault[1],tracking=tracking.stats)),flush=True)
                        if diagnostic_log:diagnostic_log.emit(dict(event='tracking_stop',reason=fault[1],tracking=tracking.stats))
                        loop_trace.observe('tracking_stop',snapshot,controller,lifecycle,current,measured_time,tracking,
                            args.preview_only,control_updated,before_control)
                        loop_trace.finish(lifecycle,episode_steps,recorder,'tracking_stop')
                        continue  # Do not apply the offending target or take another physics step.
                elif any(norm(sub(controller.targets[s][0],current[s][0]))>.08 for s in current):
                    raise RuntimeError('Wrist target error >8 cm')
                loop_trace.observe('control_update',snapshot,controller,lifecycle,current,measured_time,tracking,
                    args.preview_only,control_updated,before_control)
                with perf.measure('control_action'):
                    action_values=controller.action(current,dt)
                    action=torch.tensor([action_values],device=env.device,dtype=torch.float32)
                    if not torch.isfinite(action).all():raise RuntimeError('Nonfinite action')
                with perf.measure('record_timing_prepare'):
                    if recorder and recorder.active:
                        record_sample_monotonic=time.monotonic()
                        env.recorder_manager.add_to_episodes('timing/wall_monotonic',torch.tensor([[record_sample_monotonic]],dtype=torch.float64,device=env.device))
                        env.recorder_manager.add_to_episodes('timing/simulation_time',env.episode_length_buf[:,None]*dt)
                if contact_probe:
                    contact_probe.begin(dict(episode_number=lifecycle.number,control_index=episode_steps,
                        recording=bool(recorder and recorder.active),expected_demo=None if not recorder else f'demo_{recorder.saved}',
                        action=action_values,input_snapshot=snapshot,control_states=controller.states,
                        latest_preview_frame_id=frame_id))
                try:
                    result=step_with_first_physics_checkpoint(env,action) if timeline and episode_steps==0 else env.step(action)
                finally:
                    if contact_probe:contact_probe.end()
                if timeline and episode_steps==0:
                    plate_checkpoint(env,'after_first_control_step');timeline.mark('after_first_control_step')
                episode_steps+=1
                if bool(result[2].any() or result[3].any()):
                    # Standard pre_reset already exported the terminal episode before automatic reset.
                    if timeline:timeline.mark('after_record_finish')
                    begin_waiting_audit()
                    report_gripper_runtime('after_automatic_episode_reset')
                    lifecycle.finish('environment_termination',lifecycle.pending_result)
                    for side in controller.states:controller.hold(side,'episode_waiting')
                    print('EPISODE_RESULT '+json.dumps(lifecycle.result),flush=True)
            else:
                # Render only: no physics, rewards, episode clock or recorder rows in WAITING.
                if tick-preview_time>=1/args.preview_hz:env.sim.render()
            if (phase_before=='RUNNING' or control_updated) and lifecycle.state!='RUNNING':
                loop_trace.observe('episode_end',snapshot,controller,lifecycle,current,measured_time,tracking,
                    args.preview_only,control_updated)
            loop_gap=tick-previous>.25
            previous=tick;step_ms=(time.monotonic()-step_start)*1000
            telemetry=display_status(snapshot,controller,lifecycle,args.preview_only,start_blocked,current)
            telemetry['recording']=bool(recorder and recorder.active)
            telemetry['record_path']=str(record_dir) if record_dir else None
            telemetry['record_episode_id']=recorder.episode_id if recorder else None
            telemetry['video_error']=recorder.video.error if recorder and recorder.video else None
            telemetry['limits_hit']=controller.limits_hit
            if diagnostic_log and current is not None and tick-gripper_audit_time>=.5:
                gripper_audit_time=tick;grip_read_start=time.monotonic()
                # One small transfer at <=2 Hz, never an extra per-frame synchronization.
                joint_values=torch.stack([robot.data.joint_pos[0],robot.data.joint_pos_target[0],
                                         robot.data.joint_vel[0]]).detach().cpu().tolist()
                grip_values=[[row[i] for i in gripper_ids] for row in joint_values]
                diagnostic_log.emit(dict(event='joint_sample',tick_monotonic=tick,
                    sampled_monotonic=time.monotonic(),input_seq=telemetry['input_seq'],
                    position=joint_values[0],target=joint_values[1],velocity=joint_values[2]))
                diagnostic_log.emit(dict(event='gripper_sample',tick_monotonic=tick,input_seq=telemetry['input_seq'],
                    trigger={s:telemetry['hands'][s]['trigger'] for s in ('left','right')},
                    command=dict(controller.grippers),measured_joint_rad=grip_values[0],joint_target_rad=grip_values[1],
                    joint_velocity_rad_s=grip_values[2],sample_read_ms=(time.monotonic()-grip_read_start)*1000))
            telemetry['tracking_monitor']=tracking.stats if controller.practice else None
            stages=perf.report()
            stages['receive_to_target_ms']=None if target_generated_time is None or snapshot.get('received_monotonic') is None else (target_generated_time-snapshot['received_monotonic'])*1000
            stages['simulation_dt']=(env._sim_step_counter-sim_steps_before)*env.physics_dt
            if diagnostic_log and (phase_before=='RUNNING' or lifecycle.state=='RUNNING' or action_values is not None or requested or tick-preview_time>=1/args.preview_hz):
                diagnostic_log.emit(dict(event='decision',tick_monotonic=tick,loop_index=loop_trace.number,
                    episode_number=lifecycle.number,record_sample_monotonic=record_sample_monotonic,
                    phase_before=phase_before,requested=requested,reasons_before=reasons_before,
                    decision_monotonic=decision_time,
                    input_age_at_decision_ms=None if snapshot.get('received_monotonic') is None else (decision_time-snapshot['received_monotonic'])*1000,
                    loop_gap=loop_gap,step_ms=step_ms,frame_id=frame_id,teleop=telemetry,performance=stages,
                    input_snapshot=snapshot,measured_before_step=current,measured_sample_monotonic=measured_time,
                    target_generated_monotonic=target_generated_time,action=action_values,targets=controller.targets,
                    raw_targets=controller.raw_targets if action_values is not None else {},
                    reference_changes=controller.reference_changes if control_updated else [],
                    gripper_commands=dict(controller.grippers),
                    limits=dict(translation_m=controller.max_translation,rotation_rad=controller.max_rotation)))
            if tick-preview_time>=1/args.preview_hz:
                preview_time=tick;captured=time.monotonic();pictures={};stats={}
                camera_start=time.monotonic()
                with perf.measure('preview_camera_readback'):
                    for name in ('head_cam','left_wrist_cam','right_wrist_cam'):
                        camera=env.scene.sensors[name]
                        if lifecycle.state=='WAITING':camera.update(dt,force_recompute=True)
                        rgb=camera.data.output['rgb'][0,:,:,:3].detach().cpu().numpy()
                        if rgb.dtype.name!='uint8' or rgb.ndim!=3 or rgb.shape[-1]!=3:raise RuntimeError(f'Unexpected camera format: {name}')
                        stats[name]=dict(shape=list(rgb.shape),dtype=str(rgb.dtype),minimum=int(rgb.min()),maximum=int(rgb.max()))
                        pictures[name]=Image.fromarray(rgb)
                stages['camera_readback_ms']=(time.monotonic()-camera_start)*1000
                with perf.measure('preview_encode'):
                    encoded,encoding=encode_native_preview([pictures[n] for n in ('head_cam','left_wrist_cam','right_wrist_cam')])
                frame_id+=1
                if contact_probe:contact_probe.preview(frame_id,captured,{n:env.scene.sensors[n] for n in pictures})
                stages.update(perf.report())
                timings=dict(step_ms=step_ms,frame_interval_ms=None if last_capture is None else (captured-last_capture)*1000,
                             episode_state=lifecycle.state,episode_number=lifecycle.number,
                             teleop=telemetry,encoding=encoding,performance=stages,
                             simulation_time_s=float(env.episode_length_buf[0])*dt)
                last_capture=captured
                with perf.measure('preview_publish'):
                    publish_preview(args.bridge_dir,encoded,run_id,frame_id,stats,timings,captured)
                if diagnostic_log:diagnostic_log.emit(dict(event='preview',frame_id=frame_id,timings=timings))
            with perf.measure('terminal_report'):
                if tick-report_time>=1:
                    report_time=tick
                    print(json.dumps(dict(scenario_id=selected_id,seed=args.seed,episode_state=lifecycle.state,
                        episode_number=lifecycle.number,episode_result=lifecycle.result,recording=bool(recorder and recorder.active),
                        record_path=str(record_dir) if record_dir else None,
                        record_episode_id=recorder.episode_id if recorder else None,
                        video_error=recorder.video.error if recorder and recorder.video else None,
                        live=snapshot['live'],states={s:v['reason'] for s,v in controller.states.items()},frame_id=frame_id)),flush=True)
            perf.sleep_requested_ms=max(0.,dt-(time.monotonic()-tick))*1000
            with perf.measure('sleep'):
                time.sleep(perf.sleep_requested_ms/1000)
            loop_trace.finish(lifecycle,episode_steps,recorder)
except ShutdownRequested:
    exit_reason=shutdown.reason
except KeyboardInterrupt:
    exit_reason='KeyboardInterrupt';print('Ctrl+C: saving active diagnostic and closing.',flush=True)
except BaseException as error:
    exit_reason=f'{type(error).__name__}: {error}';print('TEST ERROR: '+exit_reason,flush=True);raise
finally:
    exit_reason=shutdown.reason or exit_reason
    print('SHUTDOWN_REQUEST reason='+exit_reason,flush=True)
    if loop_trace:shutdown.step('loop_trace',lambda:loop_trace.finish(lifecycle,episode_steps,recorder,exit_reason))
    if perf:shutdown.step('finalization_performance_begin',perf.begin)
    if recorder:
        shutdown.step('record_finish',lambda:recorder.finish(exit_reason))
        shutdown.step('record_close',recorder.close)
    elif env is not None:
        handler=getattr(env.recorder_manager,'_dataset_file_handler',None)
        if handler:shutdown.step('initialization_record_close',handler.close)
    if record_dir and metadata:
        def finish_metadata():
            metadata['exit_reason']=exit_reason
            with perf.measure('record_final_inspection') if perf else nullcontext():
                result=finalize_diagnostic(record_dir,metadata)
            print('RECORD_FINALIZED: '+json.dumps(result),flush=True)
        shutdown.step('record_inspection',finish_metadata)
    if diagnostic_log:
        shutdown.step('diagnostic_end',lambda:diagnostic_log.emit(dict(event='end',reason=exit_reason,monotonic=time.monotonic(),
            finalization_performance=perf.report() if perf else None,diagnostic_cost_total_ms=diagnostic_log.cost_ms)))
        shutdown.step('diagnostic_close',diagnostic_log.close)
    if lock_owned:shutdown.step('preview_stop',lambda:stop_preview(known.bridge_dir,run_id,exit_reason))
    for name,resource in [('contact_probe',contact_probe),('performance',perf),('timeline',timeline)]:
        if resource:shutdown.step(name,resource.close)
    # Local camera references can outlive env.close(); detach before destroying Kit.
    if env is not None:
        def detach_cameras():
            for sensor in env.scene.sensors.values():
                registry=getattr(sensor,'_rep_registry',{})
                for annotators in registry.values():
                    while annotators:
                        index=len(annotators)-1
                        annotators[index].detach([sensor._render_product_paths[index]])
                        annotators.pop()  # Camera destructor cannot detach it twice.
        shutdown.step('camera_annotators',detach_cameras)
        shutdown.step('environment',env.close)
    # Closing only our descriptor releases only our flock; never unlink lock paths.
    if lock is not None:shutdown.step('bridge_lock',lock.close)
    # Kit may terminate Python during close, so release the descriptor first.
    if app is not None:shutdown.step('simulation_app',app.close)
    print('SHUTDOWN_COMPLETE reason='+exit_reason,flush=True)
