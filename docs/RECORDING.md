# Scenarios, recording and playback

Run the [Quest setup](../README.md#optional-vr-teleoperation-and-demonstration-recording) first. Run the commands below in a **host terminal**, with the repository root as the current directory.

| Directory | Robot left → right (+Y → −Y) | Count |
|---|---|---:|
| [scenarios/mixed](../scenarios/mixed/README.md) | Six permutations of toaster, plate and rack | 100 |
| [scenarios/fixed_tpb](../scenarios/fixed_tpb/README.md) | Toaster → Plate → Bread Rack | 100 |
| [scenarios/fixed_ptb](../scenarios/fixed_ptb/README.md) | Plate → Toaster → Bread Rack | 100 |

Each has `operator_A_1`, `operator_A_2`, `operator_B_1`, `operator_B_2`, **25 scenarios each**. Each manifest specifies scenario IDs, assignments, poses and seeds. Coordinates are +X forward, +Y robot left, +Z up; quaternions are wxyz. The set READMEs retain design, distributions, rejection criteria and reproduction information.

Choose `GROUP` and `INDEX=1..25`. `record_quest_base.py` always selects the base set. For the other sets, use the full teleop command printed by dry-run, change `--scenario_manifest` to that set's `manifest.json`, and supply fresh `--record-dir`/`--diagnostic-log` paths. Selection flags are `--scenario_group` and `--group_index`; do not mix an ID from another set.

## Demonstration Recording and Playback

Every launcher execution creates a new timestamp/UUID run directory and refuses collisions, preserving earlier attempts:

```text
recordings/quest_base_B1/episode_001/run_DATE_TIME_UUID/
  launch.json                  # scenario, manifest hash, command and paths
  run.log, diagnostic.jsonl    # terminal and input/control diagnostics
  exit_code, launcher_result.json, run.lock
  recording/
    dataset.hdf5               # data/demo_* actions, observations, states, timing
    manifest.json, metadata.json
    record_audit/              # reset/timing evidence
    episode_000001/            # demonstration attempt, possibly _success suffix
      episode.json, video.mp4, video.json, frames.jsonl
```

The **outer episode_001** is scenario group index 1. **Inner episode_000001** is a recording attempt within that run. HDF5 labels and episode result use the same pre-reset outcome policy. New metadata separates `generation_contract` (historical layout provenance, including its 20 mm record) from `runtime_contract` (the executing checkout, currently strict <40 mm). Diagnostic/training-readiness flags are retained: observed success does not establish training quality or action-replay fidelity. Waiting frames are not demonstrations. Keep the full run together.

Each MP4 combines the head, left wrist and right wrist RGB camera views. New videos use **25 fps wall-clock playback** with sample-and-hold frames, not interpolation. “1×” means monotonic wall-clock duration; it does **not** guarantee real-time simulation. HDF5 simulation/action timing is unchanged. Legacy conversion preserves original files:

```bash
# Use Python with numpy and imageio-ffmpeg installed.
python3 scripts/quest_diagnostic/convert_video_wallclock.py /path/to/completed/episode_000001
```

It creates `video_wallclock.mp4` and separate sidecars; it refuses existing outputs. Legacy timestamps cannot recover an unknown exact start/end or dropped images. See [recording details](../scripts/quest_diagnostic/RECORDING.md) and [diagnostics](../scripts/quest_diagnostic/DIAGNOSTICS.md).

For inspection or playback, run the following commands from the **host repository directory**. Set `DATASET` to the **absolute container path** of your HDF5 file: replace `/workspace/cyclo_lab/recordings/...` with the matching path under that container mount. `scripts/run.sh` runs the Python script inside the container; do not run the wrapper from a container shell.

```bash
export DATASET=/workspace/cyclo_lab/recordings/quest_base_B1/episode_001/run_DATE_TIME_UUID/recording/dataset.hdf5
bash scripts/run.sh scripts/tools/toast_recording_metadata.py "$DATASET"
bash scripts/run.sh --gui scripts/imitation_learning/isaaclab_recorder/replay_demos.py \
  --dataset_file "$DATASET" --enable_cameras
```

Playback has not been exercised on a GPU for this release. Replay uses the adjacent manifest; preserve it with the HDF5 file.

[Documentation index](README.md)
