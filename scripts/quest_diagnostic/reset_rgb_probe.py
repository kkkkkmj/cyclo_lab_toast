"""Opt-in synthetic reset probe, never used by normal VR collection."""
import json
from pathlib import Path

CAMERAS = ('head_cam', 'left_wrist_cam', 'right_wrist_cam')


def snapshot(env, directory, name):
    from PIL import Image
    directory = Path(directory)
    directory.mkdir(exist_ok=True)
    for camera in CAMERAS:
        # Capture obs_buf, the exact pre-action input used by the recorder.
        Image.fromarray(env.obs_buf['policy'][camera][0].cpu().numpy()).save(directory/f'{name}_{camera}.png')
    robot = env.scene['robot']
    info = dict(physics_counter=env._sim_step_counter,
                simulation_time=float(env.sim.current_time),
                episode_length=int(env.episode_length_buf[0]),
                joint_names=robot.joint_names,
                default_joint_pos=robot.data.default_joint_pos[0].tolist(),
                robot_joint_pos=robot.data.joint_pos[0].tolist(),
                bread_0=env.scene['bread_0'].data.root_state_w[0].tolist())
    info['cameras'] = {key: dict(position=env.scene[key].data.pos_w[0].tolist(),
                                 quaternion_wxyz_ros=env.scene[key].data.quat_w_ros[0].tolist(),
                                 intrinsic_matrix=env.scene[key].data.intrinsic_matrices[0].tolist())
                       for key in CAMERAS}
    (directory/f'{name}_state.json').write_text(json.dumps(info, indent=2))


def stage_distinct_scene(env, directory, name):
    """Test-only teleport: make preceding scene visibly different without a physics step.

    This deliberately creates a discontinuity inside the synthetic test episode.
    It must never be treated as a training demonstration.
    """
    import torch
    before = env._sim_step_counter
    bread = env.scene['bread_0']
    pose = bread.data.root_state_w[:, :7].clone()
    pose[:, :3] = env.scene.env_origins + torch.tensor([.36, .02, 1.09], device=env.device)
    bread.write_root_pose_to_sim(pose)
    bread.write_root_velocity_to_sim(torch.zeros_like(bread.data.root_state_w[:, 7:]))
    robot = env.scene['robot']
    q = robot.data.joint_pos.clone()
    for side in ('l', 'r'):
        q[:, robot.joint_names.index(f'arm_{side}_joint2')] += .25
    robot.write_joint_state_to_sim(q, torch.zeros_like(q))
    env.scene.write_data_to_sim()
    env.sim.forward()
    # A test-only refresh after teleport. Normal collection uses native env.reset.
    for camera in CAMERAS:
        env.scene[camera].reset()
    env.sim.render()
    for camera in CAMERAS:
        env.scene[camera].update(0.0, force_recompute=True)
    env.obs_buf = env.observation_manager.compute(update_history=False)
    assert env._sim_step_counter == before
    snapshot(env, directory, name)
