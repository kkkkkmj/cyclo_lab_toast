"""Separate simulator-only control experiment: no Quest, no input server, no hardware."""
import argparse
from pathlib import Path
import sys
import time

TOOLS=Path(__file__).resolve().parents[1]/'tools'
REPLAY=Path(__file__).resolve().parents[1]/'imitation_learning/isaaclab_recorder'
sys.path[:0]=[str(TOOLS),str(REPLAY)]
from view_make_toast_scenario import resolve_selection
from toast_recording_metadata import DEFAULT_MANIFEST,create_diagnostic,finalize_diagnostic,applied_reset_poses,TASK
from toast_overview import overview_cfg,position_overview
from diagnostic_recorder import DiagnosticRecorder
from control import BoundedTeleop
from replay_scene_audit import TimelineProbe,emit
from replay_plate_audit import plate_checkpoint,plate_configuration,step_with_first_physics_checkpoint

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True,help='New experiment directory, never the original dataset directory')
parser.add_argument('--frames',type=int,default=95)
parser.add_argument('--episodes',type=int,default=2)
parser.add_argument('--wait-renders',type=int,default=30)
parser.add_argument('--reset-rgb-check',action='store_true',help='Synthetic scene teleports for reset validation only; never training data')
parser.add_argument('--seed',type=int,default=1)
parser.add_argument('--operator',default='operator_B',choices=['operator_A','operator_B'])
parser.add_argument('--scenario_index',default=1,type=int)
parser.add_argument('--scenario_id')
parser.add_argument('--scenario_manifest',default=str(DEFAULT_MANIFEST))
from isaaclab.app import AppLauncher
AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args()
if args.frames<1 or args.episodes<1 or args.wait_renders<0:parser.error('frames/episodes must be positive; wait-renders nonnegative')
if args.reset_rgb_check and (args.episodes<2 or args.frames<6):parser.error('reset RGB check requires >=2 episodes and >=6 frames')
if args.output.exists():parser.error('Output exists; choose a NEW directory')
selected=resolve_selection(args)
output,metadata=create_diagnostic(args.output,args.scenario_manifest,args.operator,selected,args.scenario_index,seed=args.seed)
metadata['experiment']=dict(kind='no_quest_held_targets',frames=args.frames,episodes=args.episodes,wait_renders=args.wait_renders,
    note='Reproduces reset/render/hold-target path, not demo_8 historical actions or exact prior episodes')
metadata['experiment']['reset_rgb_check']=args.reset_rgb_check
metadata['experiment']['training_demonstration']=False
if args.reset_rgb_check:metadata['experiment']['synthetic_discontinuity_frame']=args.frames-3
audit=output/'record_audit';audit.mkdir()
from reset_rgb_probe import snapshot,stage_distinct_scene
args.enable_cameras=True
app=AppLauncher(args).app
import gymnasium as gym
import torch
import cyclo_lab
from isaaclab_tasks.utils.parse_cfg import parse_env_cfg
from isaaclab.envs.mdp.recorders.recorders_cfg import ActionStateRecorderManagerCfg
from isaaclab.managers import DatasetExportMode

env=recorder=timeline=None
try:
    cfg=parse_env_cfg(TASK,device=args.device,num_envs=1)
    # Native reset renders after state/kinematic reset and before obs_buf compute.
    # Camera.reset marks buffers outdated; observation reads refresh them at time zero.
    cfg.rerender_on_reset=True
    print('RESET_RGB_CONTRACT native_rerender_on_reset=True physics_steps=0',flush=True)
    cfg.scenario_id=selected;cfg.scenario_manifest=str(output/'manifest.json');cfg.seed=args.seed
    cfg.scene.replay_overview=overview_cfg()
    cfg.env_name=TASK;cfg.recorders=ActionStateRecorderManagerCfg()
    cfg.recorders.dataset_export_dir_path=str(output);cfg.recorders.dataset_filename='dataset'
    cfg.recorders.dataset_export_mode=DatasetExportMode.EXPORT_ALL;cfg.recorders.export_in_record_pre_reset=False
    metadata['reset_rgb_contract']={'native_rerender_on_reset':cfg.rerender_on_reset,'extra_physics_steps':0}
    metadata['timing']=dict(physics_dt=cfg.sim.dt,decimation=cfg.decimation,render_interval=cfg.sim.render_interval,control_dt=cfg.sim.dt*cfg.decimation)
    env=gym.make(TASK,cfg=cfg).unwrapped;env._replay_audit_dir=str(audit)
    if args.reset_rgb_check:
        import inspect,json,hashlib,importlib.metadata
        import isaaclab
        runtime={'isaaclab_module':isaaclab.__file__,'rerender_on_reset':cfg.rerender_on_reset,'sources':{}}
        for label,func in [('env_reset',type(env).reset),('camera_update',type(env.scene['head_cam']).update),('sim_render',type(env.sim).render)]:
            path=Path(inspect.getsourcefile(func));runtime['sources'][label]={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            (audit/(label+'_runtime.py')).write_text(inspect.getsource(func))
        try:runtime['isaacsim_distribution']=importlib.metadata.version('isaacsim')
        except importlib.metadata.PackageNotFoundError:runtime['isaacsim_distribution']='not exposed as installed distribution'
        (audit/'runtime.json').write_text(json.dumps(runtime,indent=2))
    timeline=TimelineProbe(env)
    if args.reset_rgb_check:stage_distinct_scene(env,audit,'startup_before_reset')
    timeline.mark('before_startup_reset');env.reset(seed=args.seed);timeline.mark('after_startup_reset')
    if args.reset_rgb_check:snapshot(env,audit,'startup_after_reset')
    position_overview(env);recorder=DiagnosticRecorder(env,metadata)
    def poses():
        result={}
        for side in ('left','right'):
            p,q=env.action_manager.get_term(side+'_arm')._compute_frame_pose();q=q[0].tolist()
            result[side]=(p[0].tolist(),q[1:]+q[:1])
        return result
    with torch.inference_mode():
        for episode in range(1,args.episodes+1):
            env._replay_audit_episode=f'demo_{episode-1}'
            emit(env,'episode',dict(episode=episode,stage='waiting_before_explicit_reset'))
            timeline.mark('before_waiting_renders');steps_before=timeline.counts['step']
            for _ in range(args.wait_renders):
                env.sim.render()
                for name in ('replay_overview','head_cam','left_wrist_cam','right_wrist_cam'):
                    env.scene[name].update(env.step_dt,force_recompute=True)
                    _=env.scene[name].data.output['rgb']
            timeline.mark('after_waiting_renders')
            if timeline.counts['step']!=steps_before:raise RuntimeError('Unexpected sim.step during WAITING render path')
            timeline.mark('before_episode_reset');env.reset(seed=args.seed);timeline.mark('after_episode_reset')
            if args.reset_rgb_check:snapshot(env,audit,f'episode_{episode:06d}_after_reset')
            reset=applied_reset_poses(env,cfg.scenario_manifest,selected);position_overview(env)
            plate_configuration(env,metadata['timing']);plate_checkpoint(env,'after_reset_before_physics',env.scene.get_state(is_relative=True))
            robot=env.scene['robot'];lift=float(robot.data.joint_pos[0,robot.joint_names.index('lift_joint')])
            controller=BoundedTeleop(poses(),max(-1.,min(1.,(lift+.25)/.25)),False)
            recorder.start(episode,reset,args.seed)
            for frame in range(args.frames):
                if args.reset_rgb_check and frame==args.frames-3:
                    stage_distinct_scene(env,audit,f'episode_{episode:06d}_test_marker')
                action=torch.tensor([controller.action(poses(),env.step_dt)],device=env.device,dtype=torch.float32)
                env.recorder_manager.add_to_episodes('timing/wall_monotonic',torch.tensor([[time.monotonic()]],dtype=torch.float64,device=env.device))
                env.recorder_manager.add_to_episodes('timing/simulation_time',env.episode_length_buf[:,None]*env.step_dt)
                result=step_with_first_physics_checkpoint(env,action) if frame==0 else env.step(action)
                if frame==0:
                    plate_checkpoint(env,'after_first_control_step');timeline.mark('after_first_control_step')
                if bool(result[2].any() or result[3].any()):raise RuntimeError('Original environment termination occurred during experiment')
            recorder.finish('noinput_test_end');timeline.mark('after_record_finish')
    metadata['experiment_completed']=True
    print(f'NOINPUT_RECORD_COMPLETE episodes={args.episodes} frames_each={args.frames} output={output}',flush=True)
finally:
    try:
        if recorder:
            try:recorder.finish('experiment_exit')
            finally:recorder.close()
        finalize_diagnostic(output,metadata)
    finally:
        if timeline:timeline.close()
        if env is not None:env.close()
        app.close()
