# cyclo-toast-teleop

## Overview

An **Isaac Sim toast preparation task environment** with **Meta Quest bimanual and gripper teleoperation**, demonstration collection, and reproducible scenario execution. This project is based on [ROBOTIS-GIT/cyclo_lab](https://github.com/ROBOTIS-GIT/cyclo_lab) and extends the toast environment in [badajhong/cyclo_lab](https://github.com/badajhong/cyclo_lab). The existing environment framework, robots, IK and recorder infrastructure belong to their upstream authors; this package integrates local toast, Quest, scenario and recording extensions.

**Release status:** GitHub publication is pending; the clone commands below apply after publication. CPU validation is documented in [validation](docs/release/VALIDATION.md). GPU/Quest operation and a fresh Docker build have not been verified for this release. **A clone alone is insufficient:** the four-groove rack requires an independently authorized exact asset file, RoboDojo assets require the pinned downloader, and NVIDIA table/materials require cloud access. Rack redistribution permission is still unconfirmed; cloud dependency loading is unverified. See the [asset acquisition/rights checklist](docs/release/ASSETS.md). Ctrl+C leaving Isaac Sim alive has been reported again and remains unresolved. This is not a fully validated turnkey release.

## Upstream Projects and Attribution

The source snapshot includes local uncommitted implementations on top of `d8ac88d` in the development checkout. Direct toast baseline: `badajhong/cyclo_lab` commit `5f5086d11f664494119086de30a9e925b12022ad`; its descendant `761c8ac77ccbe7841966e535fa7202d7be83c7a1` starts the later scenario work. Local history begins with a flattened initial commit, so a specific ROBOTIS upstream commit cannot be established from that history. We do not invent a merge-base or claim the flattened commit is a ROBOTIS commit. See [provenance and license audit](docs/release/PROVENANCE.md).

Original `LICENSE` (Apache-2.0), `LICENSE-IsaacLab` (BSD-3-Clause), source copyright headers and vendored third-party licenses are retained. No new blanket asset license is granted. This release starts a new Git history; personal recordings and historical Git objects are not included.

## Requirements and Installation

Linux x86-64, NVIDIA GPU/driver suitable for Isaac Sim, NVIDIA Container Toolkit, Docker with Compose v2, Git LFS, host Python 3.10+, OpenSSL and an X11 desktop are required. Quest Browser and the PC must share a reachable network. The repository configures Isaac Sim **5.1.0**, vendored Isaac Lab **2.3.0**, and PyTorch **2.7.0** in Docker. Docker client **29.9.2** was available; daemon access was denied during release validation. These are configured versions, not a claim that this release passed a GPU test. Optional upstream Python dependencies include version ranges, so Docker is not a fully locked build.

Install Git LFS using your OS package manager first. Then:

```bash
cd ~
git lfs install
git clone https://github.com/kkkkkmj/cyclo-toast-teleop.git
cd cyclo-toast-teleop
export REPO="$PWD"
git lfs pull
git lfs fsck
git submodule update --init --recursive
```

The four `third_party/` dependencies are vendored source snapshots, not gitlinks. `.gitmodules` preserves their upstream URLs; the submodule command is currently a no-op. Do not replace them with upstream `main`. The 66 formerly missing inherited LFS objects were recovered and hash-verified locally, but remain excluded as unrelated to toast. See the [per-object audit](docs/release/lfs_audit.json); this is not remote LFS verification.

Read the [asset terms and acquisition procedure](docs/release/PROVENANCE.md) before obtaining external assets:

```bash
# Downloads only pinned toast object assets; validates size and SHA256.
python3 scripts/tools/download_make_toast_assets.py
# Obtain this exact file and permission from the rack rights holder first.
python3 scripts/tools/install_bread_slot.py /path/to/authorized/bread_slot.usdz
python3 scripts/tools/check_release.py --assets
```

The rack installer verifies SHA256 and refuses a different geometry; no generic substitute is used. NVIDIA's packing-table USD and materials are resolved from the configured Isaac Sim asset cloud at runtime, subject to NVIDIA terms and network access. No local backup or original development folder is required.

After reviewing NVIDIA's license terms (the inherited `docker/.env.base` sets `ACCEPT_EULA=Y`):

```bash
docker compose --project-name cyclo-toast-teleop --env-file docker/.env.base \
  -f docker/docker-compose.yaml -f docker/compose.mj.yaml --profile base build cyclo_lab
```

The image is `cyclo-toast-teleop:isaacsim-5.1.0`; project volumes are separate from the development project. The host checkout can have any name. **`/workspace/cyclo_lab` is the intentional container mount and Python package context**, not a reference to another host checkout. Keep the two Compose files together.

## Quick Start: GUI Preview

Run in your desktop terminal. `echo "$DISPLAY"` and `echo "$XAUTHORITY"` show session values; keep those values when present. `:0` and `$HOME/.Xauthority` below are fallbacks, not universal desktop locations. If the cookie is elsewhere, set `XAUTHORITY` to that existing file. Do not disable X authentication globally.

```bash
cd ~/cyclo-toast-teleop
export REPO="$PWD"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
test -f "$XAUTHORITY"
bash scripts/run_mj.sh --gui scripts/tools/view_make_toast_scenario.py \
  --scenario_manifest scenario_delivery_base/manifest.json \
  --scenario_group operator_B_1 --group_index 1 --steps 0
```

This selects `toast_base_20261109_025`. `R` resets the selected layout. Close the preview before starting the recorder. Initial pose assertions are not a stability/IK/reachability certification.

## Quest Connection and Teleoperation

Terminal 1, in the checkout: replace `192.168.1.10` with the PC's LAN address (inspect `hostname -I` or `ip address`). Select an unused port reachable from Quest; the example uses 8766.

```bash
cd ~/cyclo-toast-teleop
export REPO="$PWD"
export QUEST_HOST=192.168.1.10
export QUEST_PORT=8766
python3 scripts/quest_diagnostic/server.py \
  --host "$QUEST_HOST" --port "$QUEST_PORT" \
  --bridge-dir "$REPO/logs/quest_toast_recording"
```

Open `https://PC_LAN_IP:8766/` in Quest Browser, acknowledge the local certificate, and enter the terminal's single-use **Pair** PIN. `p` + Enter in the server terminal issues a new PIN. Certificates and private keys default to `~/.local/state/cyclo-quest-tls`, outside the checkout. Reload the page when client/server builds differ, then enter VR.

Terminal 2, from the same checkout and desktop session:

```bash
cd ~/cyclo-toast-teleop
export REPO="$PWD"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
GROUP=operator_B_1 INDEX=1 python3 scripts/record_quest_base.py --dry-run
GROUP=operator_B_1 INDEX=1 python3 scripts/record_quest_base.py
```

The host bridge `$REPO/logs/quest_toast_recording` corresponds exactly to `/workspace/cyclo_lab/logs/quest_toast_recording` in the container. Use one simulation producer per bridge. This base launcher deliberately fixes the bridge and manifest; a custom direct teleop invocation must use matching paths in both processes.

Release both squeeze buttons; **X** requests reset/start. Recording begins only when accepted (`REC` / `RECORD_STARTED`). Hold each squeeze to control that arm target; its trigger controls its gripper. **A** manually ends the episode. Success, failure, timeout or tracking stall can also end an episode. The environment waits between attempts; the result, including **SUCCESS**, persists next to **NO REC** until the next accepted X-start.

The launcher's position and rotation scales are **1:1**. This target mapping does not imply instantaneous tracking or a measured physical robot speed. Existing joint gains, authored limits, IK and target-lead/stall guards still apply. The launcher retains the current practice profile and options; inspect `--dry-run` for the exact command.

The current HUD is `cast-fixed-14`, with Cast fit defaults scale 0.46, center (0.22, 0.04), margin 0.02. Browser display preferences persist per address; exit VR, adjust, and re-enter. Actual Meta casting crop and headset readability are unverified; PC preview is not a casting calibration.

Use console `q` or Ctrl+C in the simulation terminal to request finalization and exit; stop the server separately with Ctrl+C. The relay forwards signals to its own registered Python PID and logs shutdown stages, without a forced timeout. **Isaac Sim remaining alive after Ctrl+C has recurred. CPU signal mocks do not prove it fixed.** Check `SHUTDOWN_WAIT`, `MJ_RUN_EXIT` and container state before another launch. Do not kill unrelated sessions or assume an `exit_code` exists while cleanup is hung.

## Scenario Sets and Operator Assignment

| Directory | Robot left → right (+Y → −Y) | Count |
|---|---|---:|
| [scenario_delivery](scenario_delivery/README.md) | Six permutations of toaster, plate and rack | 100 |
| [scenario_delivery_base](scenario_delivery_base/README.md) | Toaster → Plate → Bread Rack | 100 |
| [scenario_delivery_base_ptb](scenario_delivery_base_ptb/README.md) | Plate → Toaster → Bread Rack | 100 |

Each has `operator_A_1`, `operator_A_2`, `operator_B_1`, `operator_B_2`, **25 scenarios each**. IDs, assignments, poses, seeds and reproduction inputs are preserved byte-for-byte; no regeneration/reassignment was performed. Coordinates are +X forward, +Y robot left, +Z up; quaternions are wxyz. The set READMEs retain design, distributions, rejection criteria and reproduction information.

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

The **outer episode_001** is scenario group index 1. **Inner episode_000001** is an accepted demonstration attempt within that run. HDF5 labels and episode result use the same pre-reset outcome policy. New metadata separates `generation_contract` (historical layout provenance, including its 20mm record) from `runtime_contract` (the executing checkout, currently strict <40mm). Diagnostic/training-readiness flags are retained: observed success does not establish training quality or action-replay fidelity. Waiting frames are not demonstrations. Keep the full run together.

MP4 is a HEAD/LEFT WRIST/RIGHT WRIST RGB atlas. New videos use **25fps wall-clock playback** with sample-and-hold frames, not interpolation. “1×” means monotonic wall-clock duration; it does **not** guarantee real-time simulation. HDF5 simulation/action timing is unchanged. Legacy conversion preserves original files:

```bash
# Use Python with numpy and imageio-ffmpeg installed.
python3 scripts/quest_diagnostic/convert_video_wallclock.py /path/to/completed/episode_000001
```

It creates `video_wallclock.mp4` and separate sidecars; it refuses existing outputs. Legacy timestamps cannot recover an unknown exact start/end or dropped images. See [recording details](scripts/quest_diagnostic/RECORDING.md) and [diagnostics](scripts/quest_diagnostic/DIAGNOSTICS.md).

For inspection/playback, substitute the relative path printed by your run (inside the container):

```bash
export DATASET=/workspace/cyclo_lab/recordings/quest_base_B1/episode_001/run_DATE_TIME_UUID/recording/dataset.hdf5
bash scripts/run_mj.sh scripts/tools/toast_recording_metadata.py "$DATASET"
bash scripts/run_mj.sh --gui scripts/imitation_learning/isaaclab_recorder/replay_demos.py \
  --dataset_file "$DATASET" --enable_cameras
```

Playback has not been exercised on a GPU for this release. Replay uses the adjacent manifest; preserve it with the HDF5 file.

## Task Behavior and Success Criteria

The v2 configuration and control/physics values are copied from the latest working tree:

- Four-groove rack, native 230 × 130 × 45mm, 60mm groove pitch. Dynamic rack/bread settling remains unresolved.
- Lever starts a loaded cycle on entry to **90%** travel. This differs intentionally from the shared lever-pressed predicate (85%); values were not unified.
- Heating begins after lowering reaches its measured position/velocity condition, then lasts **4 simulation seconds**. Per-ID presence throughout heating determines eligibility; removal/reinsertion invalidates that slice for the cycle. The phase drives LED behavior.
- Carriage rising target and upper limit are **+35mm**; lower travel is −45mm.
- v2 gripper master/slave gains are **100/4**; master velocity limit is **6.5rad/s**, slave velocity limits remain authored in the robot USD. Arm and lift settings are unchanged; see [configuration audit](docs/release/PROVENANCE.md).
- Success needs completed pop-up, released lever, and **at least one identical bread ID both heated and placed on the plate**. Plate-local bread geometry-center XY distance must be **<0.04m; exactly 40mm fails**. Height, flatness, linear-speed and plate pose conditions remain.
- Serving v2 no longer requires arms at standby, gripper angles below the old threshold, lift return, or reserve slices on the rack. Earlier non-serving tasks retain their distinct conditions. Some inherited class comments still describe “both slices”; executable v2 logic requires one or more.

## Validation Status and Known Issues

See [release validation](docs/release/VALIDATION.md) for exact tests, failures and limitations. CPU checks cover strict success boundaries, heated-ID history, recording labels, wall-clock MP4 timing, HUD logic and cooperative shutdown with a mocked Docker executable. They cannot establish PhysX stability, Quest/casting appearance, GPU performance, or actual Isaac Sim shutdown. A clean checkout also requires external rack authorization and asset acquisition. GitHub publication and remote LFS retrieval are not claimed until explicitly verified.

## License and Acknowledgments

See [LICENSE](LICENSE), [LICENSE-IsaacLab](LICENSE-IsaacLab), [third-party notices](THIRD_PARTY_LICENSES.md) and [asset/provenance audit](docs/release/PROVENANCE.md). Credit ROBOTIS, badajhong, NVIDIA/Isaac Lab, RoboDojo and all preserved source copyright holders. External asset rights are not replaced by the code license.

### Diagnosing a simulator that remains alive after Ctrl+C

The application can remain blocked in native code or Kit cleanup. This remains
an open issue, independent of the CPU signal-relay tests. Preserve the run folder
and inspect `SHUTDOWN_WAIT`, the recovery log named by `MJ_RUN`, and the exact
container name printed by that same launch. Do not identify a session by a broad
process name or stop every Compose container.

```bash
# Replace with the exact container from YOUR run's MJ_RUN line.
export RUN_CONTAINER=exact-container-name-from-your-run
# Read-only inspection; run these only after setting the exact name.
docker inspect --format '{{.Name}} {{.State.Status}}' "$RUN_CONTAINER"
docker logs --tail 100 "$RUN_CONTAINER"
```

If the original console is still responsive, enter `q` and allow finalization.
If it is not, an operator may resend SIGINT to that container's registered Python
PID after confirming its identity:

```bash
docker exec "$RUN_CONTAINER" sh -c \
  'read -r pid < /tmp/cyclo-mj-python.pid; case "$pid" in ""|*[!0-9]*) exit 2;; esac; kill -INT "$pid"'
```

A native hang may still prevent cleanup. As a **last resort chosen by the
operator**, `docker stop --time 60 "$RUN_CONTAINER"` sends TERM and eventually
KILL to this one container. That can lose buffered HDF5/MP4 data: preserve all
existing run files, treat interrupted outputs as incomplete and inspect them
before use. This is recovery guidance, not a shutdown fix; no such command was
run against an existing session during release preparation.
