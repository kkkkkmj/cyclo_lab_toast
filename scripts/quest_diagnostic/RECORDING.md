# Quest demonstration and MP4 recording

This workflow selects **scenario_delivery_base / operator_B_1 / group_index 1**:
`toast_base_20261109_025`. It preserves the selected layout and records each accepted X-started
teleoperation episode as Isaac Lab HDF5 data plus a simulation-camera MP4. The diagnostic JSONL
trace is separate from the demonstration data. Results are observed task verdicts, not a guarantee
of training readiness or action-replay fidelity.

## Setup

Follow [installation](../../README.md) first. The recording
process needs h5py, NumPy, Pillow and `imageio-ffmpeg==0.6.0`; the last is declared in the Cyclo Lab
package dependencies and provides the FFmpeg binary. Rebuild the separate image after updating:

```bash
export REPO=/path/to/cyclo-toast-teleop
cd "$REPO"
docker compose --project-name cyclo-toast-teleop --env-file docker/.env.base \
  -f docker/docker-compose.yaml -f docker/compose.mj.yaml --profile base build cyclo_lab
```

The commands below create a separate transient container with this checkout mounted at
`/workspace/cyclo_lab`. They do not enter or stop an existing container. Ensure resources and the
chosen bridge are available; do not launch another producer on an occupied bridge. The launcher uses
the GUI: set DISPLAY and XAUTHORITY for your desktop session. Do not restart an active server or
simulation merely to follow this example.

## Quest server — terminal 1

Replace the clone path and `YOUR_PC_LAN_IP`; use an unused HTTPS port reachable from Quest.
If an appropriate server already runs, use its bridge path consistently in both terminals.

```bash
export REPO=/path/to/cyclo-toast-teleop
export QUEST_HOST=YOUR_PC_LAN_IP
export QUEST_PORT=8766
cd "$REPO"
python3 scripts/quest_diagnostic/server.py \
  --host "$QUEST_HOST" --port "$QUEST_PORT" \
  --bridge-dir "$REPO/logs/quest_toast_recording"
```

Open `https://<QUEST_HOST>:<QUEST_PORT>/` in Quest Browser, confirm the certificate and pair with the
terminal PIN. Certificates/private keys default to `~/.local/state/cyclo-quest-tls`; optional
`--cert /path/to/certificate --key /path/to/private_key` selects your own. Keep keys out of Git.
Reload the current page before entering VR when client/server builds differ.

## Record B_1, first scenario — terminal 2

Use your actual clone path and desktop display/cookie file. The host-side
[launcher](../record_quest_base.py) uses GROUP and INDEX for both scenario selection and storage.
It defaults to `scenario_delivery_base`, `operator_B_1`, index 1. INDEX must be 1–25.
Each invocation creates a new run; it leaves `recording/` absent for the recorder to create.
MP4 recording starts automatically with HDF5; there is no separate video-enable flag.

```bash
export REPO=/path/to/cyclo-toast-teleop
export DISPLAY=:0  # Replace with your desktop display.
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"  # Must be an existing desktop cookie file.
cd "$REPO"
GROUP=operator_B_1 INDEX=1 python3 scripts/record_quest_base.py
```

For the second scenario (`toast_base_20261109_091`), after the previous run exits:

```bash
cd "$REPO"
GROUP=operator_B_1 INDEX=2 python3 scripts/record_quest_base.py
```

The launcher preserves `--gui --keep-open --enable-grippers --control-profile practice`,
`--position-scale 1 --rotation-scale 1 --no-home-limits --no-speed-limits --workspace off`,
`--max-target-lead 0.12 --max-angular-lead-deg 45 --tracking-stall-seconds 2`,
`--preview-hz 15 --seed 1 --record-seconds 0`. The bridge remains
`logs/quest_toast_recording` on the host and `/workspace/cyclo_lab/logs/quest_toast_recording`
in the container. It enables HDF5/MP4 and `diagnostic.jsonl`, captures output through `tee -i`,
and writes `exit_code` after the simulation relay exits and the log pipe drains.

Check the resolved ID, full command and host/container paths without starting Docker or creating files:

```bash
cd "$REPO"
GROUP=operator_B_1 INDEX=2 python3 scripts/record_quest_base.py --dry-run
```

`--group` and `--index` override the corresponding environment defaults. The other supported
subgroups use separate `quest_base_A1`, `quest_base_A2` or `quest_base_B2` roots; this launcher
always uses the base manifest, never the mixed-order or PTB sets.

1. Confirm `SCENARIO_SELECTED` identifies `toast_base_20261109_025`, then inspect fresh camera previews.
2. Release both squeeze buttons. Press **X** to request reset/start; recording begins only when the
   start is accepted. `RECORD_STARTED` and **REC** identify the active recording. Waiting renders add
   neither HDF5 action rows nor MP4 frames.
3. Squeeze controls the corresponding arm target and trigger controls its gripper. The practice profile
   and 1:1 target scales do not imply instantaneous tracking or a measured robot velocity.
4. **A** ends the episode manually. Success, task failure, timeout or tracking stall also ends it.
   HDF5/MP4 finalize, then the environment waits. The result stays beside NO REC until the next
   accepted X resets/starts another episode. `--record-seconds 0` disables the optional wall-time
   recording cap; it does not disable the task's existing simulation timeout.
5. Ctrl+C or the console `q` command finalizes an active recording and exits. A forced kill or power
   loss cannot guarantee recovery of buffered data. Never delete or overwrite an existing run to restart.

[Episode results](EPISODE_RESULTS.md) documents the exact serving predicate and outcome priority:
explicit stop/stall is non-success; failure beats simultaneous success; success beats a simultaneous
time limit when no failure is present. The result display also works without `--record-dir`.

## Outputs and interpretation

```text
recordings/quest_base_B1/
├── episode_001/                      # scenario group_index 1
│   ├── run_YYYYMMDD_HHMMSS_UNIQUE/
│   │   ├── recording/
│   │   │   ├── dataset.hdf5
│   │   │   ├── metadata.json
│   │   │   ├── manifest.json
│   │   │   ├── episode_000001/        # demonstration attempt, not scenario index
│   │   │   └── ...                    # preserve original attempt names, including _success
│   │   ├── diagnostic.jsonl
│   │   ├── run.log
│   │   ├── exit_code
│   │   ├── launch.json
│   │   ├── launcher_result.json
│   │   └── run.lock
│   └── run_.../                       # a separate execution of the same scenario
├── episode_002/
└── ... episode_025/                   # scenario directories are created on demand
```

The outer `episode_001`–`episode_025` are **scenario numbers**. Inner `episode_000001` names
are **demonstration attempt numbers** and are never renumbered by this launcher or by migration.
Host paths below the checkout map to the same relative paths under `/workspace/cyclo_lab`;
mapping only the run's basename would lose the scenario directory and is incorrect.

| Path under RUN_DIR | Contents |
|---|---|
| `recording/dataset.hdf5` | Standard `data/demo_*/{actions,obs,states,initial_state,processed_actions,timing}` |
| `recording/manifest.json`, `metadata.json` | Selected manifest snapshot, assignment, code/source hashes and finalization metadata |
| `recording/episode_000001/video.mp4` | HEAD / LEFT WRIST / RIGHT WRIST simulation RGB atlas, 768×256; one directory per episode |
| `recording/episode_000001/episode.json` | Result, reason, raw termination terms, HDF5 group and video summary |
| `recording/episode_000001/frames.jsonl`, `video.json` | Frame-to-sample mapping, timing, dropped frames and encoder errors |
| `recording/record_audit/` | Diagnostic reset/timing evidence, not additional training demonstrations |
| `diagnostic.jsonl`, `run.log` | Control/input trace and terminal output, separate from HDF5/MP4 |
| `exit_code` | `run_mj.sh`/Compose exit status after cleanup; not an episode success label |
| `launch.json` | Resolved manifest hash, scenario/group/index, full command and host/container paths |
| `launcher_result.json`, `run.lock` | Relay/logging exit results and a lock held for the launch lifetime; lock-file presence alone does not mean a run is active |

Existing migrated runs keep all original files, including converted videos and historical metadata
paths. Their matched relay recovery logs are stored as `relay_recovery.log`; files not present in an
old run are not fabricated, except an explicitly documented recovered exit code. Local migration
reports and before/after SHA-256 inventories live under `recordings/migration_reports/`, outside Git.
Replay resolves `manifest.json` next to the selected dataset, so historical `record_directory` and
`manifest_source` fields do not need rewriting. Do not move a run with an active writer or uncertain
execution status; the mere presence of saved episodes or an available HDF5 lock is insufficient.

HDF5 `success`, `task_success_observed` and `episode.json` use the same pre-reset outcome policy.
`diagnostic=true` and `training_ready=false` remain: task success does not certify demonstration quality.
The MP4 uses recorded pre-action RGB, not desktop capture. New recordings play in monotonic
wall-clock time at 25fps using sample-and-hold (repeated captured images, no motion interpolation).
HDF5 sample times and simulation/control periods are unchanged. No frames means
no MP4 or HDF5 demo, but the episode sidecar is retained. Keep each complete run directory together.

Recording provenance uses `git -c safe.directory=<resolved checkout> ...` for each read-only query.
This permits the container's `/workspace/cyclo_lab` bind mount without changing global Git trust or
using `safe.directory=*`. The current commit, dirty status, tracked diff hash and recorder source hashes
are stored; private diff contents are not copied into metadata.

## Inspect the saved run

After the simulator exits, replace `run_DATE_TIME_UNIQUE` with the run printed by the launcher.
The explicit conversion also works for migrated runs without `launch.json`:

```bash
export RUN_DIR="$REPO/recordings/quest_base_B1/episode_001/run_DATE_TIME_UNIQUE"
CONTAINER_RUN=$(python3 -c 'import sys; from pathlib import Path; print(Path("/workspace/cyclo_lab") / Path(sys.argv[2]).resolve().relative_to(Path(sys.argv[1]).resolve()))' "$REPO" "$RUN_DIR")
bash scripts/run_mj.sh scripts/tools/toast_recording_metadata.py \
  "$CONTAINER_RUN/recording/dataset.hdf5"
```

The inspector checks action/state/image time axes, selected scenario provenance, success-label agreement
and video frame-to-sample timing. It requires at least one nonempty episode. CPU integration tests use
the pinned HDF5 writer and real MP4 encoding/decoding with synthetic frames. Serving, lifecycle and
HUD tests cover pre-reset capture, simultaneous terminations, WAITING persistence and accepted starts.
**Actual PhysX/Quest recording, headset readability and casting crop remain unverified.**

For the fields recorded during inactive transitions, full-loop timing and asynchronous video work,
see [Inactive transitions and loop timing](DIAGNOSTICS.md). The existing `--diagnostic-log` command
above enables them; no new runtime option or control threshold is required.

## Terminal interrupt forwarding

`run_mj.sh` now owns a uniquely named transient Compose container and uses `-T`
independently of whether stdout is a terminal or a tee pipe. The host relay keeps
Compose in a separate session; a terminal SIGINT/SIGTERM is sent with `docker exec`
to the exact Python PID registered by `mj_python.py` inside that container. Requests
arriving before PID registration are retried. No sudo, process-name matching, or
signals to other containers are used. The existing Docker permission is required.

For Quest, signal handlers only latch a request. `--keep-open` still waits between
episodes but does not override this request. The main path finalizes complete
samples and video with reason `signal_SIGINT`, closes the writer, then releases
preview/probes, camera annotators, environment, this process's lock descriptor,
and SimulationApp. Kit may terminate Python inside `SimulationApp.close`, hence
the lock is released first. Every stage logs BEGIN/END/ERROR and reports WAIT every
five seconds; this identifies a stuck codec, environment close, or Kit shutdown.
No forced timeout kills the process or discards buffered recordings.

The host launcher uses `tee -i` and separate process sessions to keep the terminal log open during
Ctrl+C. It forwards the first SIGINT/SIGTERM to its own `run_mj.sh` relay, waits for cleanup and log
drain, then records the simulation exit status. It does not signal existing containers or set a
forced shutdown timeout. No extra outer tee pipeline is needed:

```bash
GROUP=operator_B_1 INDEX=1 python3 scripts/record_quest_base.py
```

CPU launcher checks cover indices 1, 2 and 25 in all four subgroups, invalid input rejection,
unique run creation, host/container argument mapping, tee drain, and SIGINT/SIGTERM propagation
through the real wrapper/relay with a mocked Docker executable. These checks do not launch PhysX,
the GUI or Quest, and do not establish runtime validation of the new launcher.

Plain `tee` is also supported for shutdown, but it may exit on SIGINT before final
logs arrive. `MJ_RUN` prints a unique `/tmp/cyclo-mj-run-*.log` recovery log; the
relay continues draining Compose output there if the pipe closes. `MJ_SIGNAL`
means delivery to the registered Python PID succeeded; `SHUTDOWN_REQUEST` means
Python reached cooperative cleanup. `SHUTDOWN_WAIT stage=...` identifies delayed
cleanup; `MJ_RUN_EXIT` records Compose's final return code in the recovery log.
A native call which never returns can still prevent Python from handling signals;
the relay does not claim to make such calls interruptible.

CPU validation covers real process signals in a mocked Docker adapter for
initialization, WAITING, RUNNING, tee/no-tee, and repeated interrupts. Separate
fake-physics integration reopens actual HDF5 files and decodes real MP4s after a
`signal_SIGINT` finalization, including incomplete-step trimming. Actual Isaac GUI
and container exit require a fresh user-run validation; existing sessions are not
modified or interrupted by installing this change.

## Wall-clock video playback

New `video.mp4` files use 25fps independently of `control_dt`. Each output tick
shows the latest retained observation sample by `wall_monotonic`. This timestamp
is the pre-action observation sample time; `enqueued_monotonic` is the later CPU
readback/submission time, not camera exposure. The first sample is never shown
before its timestamp: any initial gap is black. Subsequent gaps (including queue
drops) hold the previous sample, and the final sample is held until close is
requested. Final encoder drain time is excluded. Successful output duration is
`ceil(recording_wall_seconds * 25) / 25`, within one frame (40ms) of wall duration.
An episode with no retained samples has no playable MP4, as before.

Atlas composition, repeated-frame writes and FFmpeg remain in the bounded-queue
worker. No extra camera readback, HDF5 rows, physics steps or interpolated poses
are produced. Finalization waits at the episode boundary, as before; the existing
shutdown stage logs show a slow drain. The higher output frame count may cost
more encoder CPU, but the control thread never writes duplicated frames.

`video.json` records `time_basis`, start/end monotonic timestamps,
`actual_recording_duration_s`, `mp4_duration_s` (successful CFR frames / fps),
`original_frames` (submitted samples), `retained_source_frames` / `encoded`,
`output_frames`, `duplicate_frames`, `blank_frames`, `omitted_source_frames`
(samples too close together to occupy a 25fps tick), queue/total drops and errors.
`frames.jsonl` still has one row per retained source sample. Its
`output_frame_start` and `output_frame_count` identify the half-open output range
holding that source; count zero means that sample is not visible at this fps.
`duplicate_frames` distinguishes copies. It retains original sample index,
wall/simulation timestamps and readback intervals.

### Convert a completed legacy episode without overwriting it

Use the same Python dependencies as recording (`numpy`, `imageio-ffmpeg`).
The utility requires an existing completed legacy `video.json` with
`time_basis=simulation_time`, its `frames.jsonl`, and `video.mp4`:

```bash
python3 scripts/quest_diagnostic/convert_video_wallclock.py \
  /absolute/path/to/completed/episode_000001
```

It creates `video_wallclock.mp4`, `frames_wallclock.jsonl`, and
`video_wallclock.json`; any existing output causes refusal. Original MP4, sidecars
and HDF5 are not modified. By default the interval starts at the first sample and
ends 40ms after the last sample. Legacy frame timestamps alone do not reveal the
exact X-start-to-stop interval, so the report marks the final tail as estimated
and does not claim to recover the full original recording duration. If separate
logs provide exact same-clock bounds, pass `--start-wall-monotonic SECONDS` and
`--end-wall-monotonic SECONDS`. Do not use Unix epoch or simulation timestamps for
these options. The conversion cannot recover already dropped source frames.
