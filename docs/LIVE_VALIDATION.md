# Operator-assisted live validation

**Procedure only — not executed validation evidence.** Continue only after the
host operator confirms available GPU capacity, an unused LAN port and no impact
on running sensor, training or simulation work. If that cannot be established,
stop and record NOT TESTED. Do not stop/reconfigure another workload. Keep GitHub
Private; the [rights gate](PREPUBLICATION_REVIEW.md) is independent of runtime tests.

## Read-only host preflight

Run in the actual Ubuntu desktop terminal, not a restricted sandbox:

```bash
nvidia-smi
docker ps --format '{{.ID}} {{.Names}} {{.Image}} {{.Status}} {{.Ports}}'
docker image ls
docker compose ls
ps -eo pid,comm,args | grep -E 'isaac|torchrun|python.*train'
ss -ltnp
```

Record GPU memory/processes, driver version, existing projects/images and ports.
These commands must succeed before concluding the host is idle. The default
Compose configuration reserves all GPUs and uses host networking/IPC; do not run
this procedure alongside other experiments merely because container names differ.

## Separate checkout, image, project and output paths

Use a new private GitHub checkout, not a clone of a working directory or a
shared cache. These commands require GitHub authentication and network access.
Run all subsequent commands from this fresh checkout, in the same shell:

```bash
export AUDIT_ROOT=$(mktemp -d /tmp/cyclo-publication.XXXXXX)
export AUDIT_STAMP=$(date +%Y%m%d_%H%M%S)
export AUDIT_PROJECT="cyclo-lab-toast-audit-$AUDIT_STAMP"
export AUDIT_IMAGE="$AUDIT_PROJECT:isaacsim-5.1.0"
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/kkkkkmj/cyclo_lab_toast.git "$AUDIT_ROOT/repo"
cd "$AUDIT_ROOT/repo"
export AUDIT_REPO="$PWD"
git config --local lfs.storage "$AUDIT_REPO/.git/lfs"
git lfs pull
git lfs fsck
git rev-parse HEAD
python3 scripts/tools/download_make_toast_assets.py
python3 scripts/tools/check_release.py --assets
export AUDIT_OVERRIDE="$AUDIT_ROOT/compose.audit.yaml"
cat > "$AUDIT_OVERRIDE" <<'YAML'
services:
  cyclo_lab:
    image: ${AUDIT_IMAGE}
    container_name: ${AUDIT_PROJECT}
YAML
```

Stop on any failure. Record the actual commit, all acquisition output and hashes.
Do not copy missing ignored assets from a developer checkout and call it a fresh
installation. Keep the temporary directory after testing as the evidence bundle.
Choose a fresh project name; do not prune old images/volumes. Review NVIDIA terms
before accepting the existing `ACCEPT_EULA=Y` setting. A build can consume substantial
CPU/disk/network resources even without GPU execution.

```bash
set -o pipefail
docker compose --project-name "$AUDIT_PROJECT" --env-file docker/.env.base \
  -f docker/docker-compose.yaml -f docker/compose.mj.yaml -f "$AUDIT_OVERRIDE" \
  --profile base config > "$AUDIT_ROOT/compose.resolved.yaml"
docker compose --project-name "$AUDIT_PROJECT" --env-file docker/.env.base \
  -f docker/docker-compose.yaml -f docker/compose.mj.yaml -f "$AUDIT_OVERRIDE" \
  --profile base build --no-cache cyclo_lab 2>&1 | tee "$AUDIT_ROOT/build.log"
```

The new project names its own volumes and image; the fresh checkout supplies its
own `docker/zenoh_cache`. No existing project/image is overwritten. This still uses
host networking/IPC/devices, so it is not a security or GPU scheduling boundary.
Do not run `scripts/run_mj.sh` for these isolated tests: it intentionally retains
the original project name. Use the same signal relay with this project's options:

```bash
: "${DISPLAY:?Use the active desktop DISPLAY}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
test -f "$XAUTHORITY"
audit_run() {
  python3 scripts/tools/mj_signal_relay.py docker compose \
    --project-name "$AUDIT_PROJECT" --env-file docker/.env.base \
    -f docker/docker-compose.yaml -f docker/compose.mj.yaml -f "$AUDIT_OVERRIDE" \
    --profile base --mj-command \
    --env "DISPLAY=$DISPLAY" --env XAUTHORITY=/tmp/mj.xauthority \
    --env HEADLESS=0 --env LIVESTREAM=0 \
    --volume /tmp/.X11-unix:/tmp/.X11-unix:ro \
    --volume "$XAUTHORITY:/tmp/mj.xauthority:ro" \
    -w /workspace/cyclo_lab cyclo_lab \
    /isaac-sim/python.sh scripts/tools/mj_python.py "$@"
}
```

The relay creates and tracks its own uniquely named one-off container. Retain its
`MJ_RUN` container name/recovery-log path. Check it exits after each run. Never
use blanket container/process termination commands.

## Representative GUI layouts

Use these manifest-confirmed examples one at a time:

| Set | Scenario ID | Robot left → right |
|---|---|---|
| Mixed | `toast_v20261108_000` | Toaster, plate, rack |
| Mixed | `toast_v20261108_017` | Toaster, rack, plate |
| Mixed | `toast_v20261108_034` | Plate, toaster, rack |
| Mixed | `toast_v20261108_051` | Plate, rack, toaster |
| Mixed | `toast_v20261108_068` | Rack, toaster, plate |
| Mixed | `toast_v20261108_084` | Rack, plate, toaster |
| Fixed TPB | `toast_base_20261109_025` | Toaster, plate, rack; default B_1 / 1 |
| Fixed PTB | `toast_base_ptb_20261109_020` | Plate, toaster, rack; B_1 / 1 |

Example (substitute the set path and ID from the table):

```bash
audit_run scripts/tools/view_make_toast_scenario.py \
  --scenario_manifest scenarios/mixed/manifest.json \
  --scenario_id toast_v20261108_000 --steps 300 --reset_every 100 \
  2>&1 | tee "$AUDIT_ROOT/gui_mixed_000.log"
python3 scripts/record_quest_base.py --group operator_B_1 --index 1 --dry-run \
  > "$AUDIT_ROOT/default_tpb_plan.json"
```

Check robot, toaster, plate, rack and all four breads, actual initial position and
quaternion, repeated reset, contacts/penetration and subsequent settling. Save a
real GUI screenshot for each ID and camera views; do not substitute overview-card
images. `RESET_POSES_OK` checks immediate poses against existing tolerances
(position absolute 5e-5 m; quaternion absolute-dot deviation 5e-5). It does not
print a numerical error table or measure settling. Do not claim such measurements
from that marker alone.

Record actual per-object initial/reset positions and quaternions, plus observations
after settling. Existing recording metadata contains `applied_reset_poses`; compare
those to the selected manifest. Report maximum absolute position component error
in metres and angular error `2*acos(clamp(abs(dot(q_actual, q_expected)),0,1))`
after normalizing quaternions, in degrees. Record maximum displacement during a
stated settling interval separately. Do not alter tolerances to obtain a pass.
If the instrumentation does not expose a measurement, mark it NOT TESTED and retain
the logs rather than inventing a number. Screenshot evidence alone cannot prove
pose accuracy. Inspect missing MDL/cloud errors and native shutdown separately.

## Actual Quest control and new recordings

A human wearing a Meta Quest is required. In the same shell choose an unused LAN
port and reachable PC address, then start the server in terminal 1:

```bash
export QUEST_HOST=192.168.1.10  # Replace with this PC's reachable LAN address.
export QUEST_PORT=8766        # Replace if already in use.
export AUDIT_REL="recordings/publication_$AUDIT_STAMP"
export AUDIT_BRIDGE_REL="logs/publication_$AUDIT_STAMP"
python3 scripts/quest_diagnostic/server.py \
  --host "$QUEST_HOST" --port "$QUEST_PORT" \
  --bridge-dir "$AUDIT_REPO/$AUDIT_BRIDGE_REL"
```

Keep certificates and pairing secrets private. In terminal 2, restore the same
exported audit variables and `audit_run` function, and use a **new** recording path:

```bash
audit_run scripts/quest_diagnostic/teleop_toast.py \
  --keep-open --enable-grippers --control-profile practice \
  --scenario_manifest scenarios/fixed_tpb/manifest.json \
  --scenario_group operator_B_1 --group_index 1 \
  --bridge-dir "/workspace/cyclo_lab/$AUDIT_BRIDGE_REL" \
  --position-scale 1 --rotation-scale 1 --no-home-limits --no-speed-limits \
  --workspace off --max-target-lead 0.12 --max-angular-lead-deg 45 \
  --tracking-stall-seconds 2 --preview-hz 15 --seed 1 \
  --record-dir "/workspace/cyclo_lab/$AUDIT_REL/recording" --record-seconds 0 \
  --diagnostic-log "/workspace/cyclo_lab/$AUDIT_REL/diagnostic.jsonl" \
  2>&1 | tee "$AUDIT_ROOT/quest.log"
```

1. Open the server HTTPS address in Quest Browser, accept the local certificate,
   enter its single-use PIN and enter VR. Check both controllers and all cameras.
2. Release both squeeze buttons, press X, and wait for `REC` / `RECORD_STARTED`.
3. Hold left squeeze and test left translation/rotation; repeat on the right.
   While holding the same controller's squeeze, test its trigger/gripper. Then
   exercise simultaneous bimanual movement. Do not infer any of these from mocks.
4. Attempt the actual toast task. Preserve a real successful episode if achieved;
   inability to achieve success is a result, not a reason to modify the predicate.
5. Start another attempt with X and observe a genuine failure or configured task
   timeout. A manual A stop or tracking stall is not a TIMEOUT episode. Test A stop
   and tracking loss separately, retaining the exact observed outcome.
6. Finalize with `q` / Ctrl+C and wait for the owned container to exit; stop the
   server separately. Use [targeted shutdown guidance](TROUBLESHOOTING.md) for a
   hung owned run; never terminate other sessions.

## Metadata, video and GPU replay

Preserve the complete new run. Inspect its real HDF5 and adjacent manifest using:

```bash
export AUDIT_DATASET="/workspace/cyclo_lab/$AUDIT_REL/recording/dataset.hdf5"
audit_run scripts/tools/toast_recording_metadata.py "$AUDIT_DATASET" \
  2>&1 | tee "$AUDIT_ROOT/hdf5_inspection.log"
audit_run scripts/imitation_learning/isaaclab_recorder/replay_checked.py \
  --dataset_file "$AUDIT_DATASET" --enable_cameras --num_envs 1 --validate_states \
  2>&1 | tee "$AUDIT_ROOT/gpu_replay.log"
```

The checked replay wrapper requires a complete validation verdict, not just a
zero Kit process exit. Preserve `REPLAY_FIELD_ERRORS`, checked/expected/mismatched
counts and the supervisor verdict. This still does not prove task success replay;
record that separately from the actual task outcome. Do not use saved-state video
export as evidence of action replay fidelity.

Record independent results for HDF5 creation; observation/actions and timing;
ID/group/manifest snapshot hash; success/failure/timeout labels; three camera
views; MP4 decoding/duration/frame mapping; replay process completion; actual
action/state fidelity; and task-success reproduction. Verify labels against
`termination_terms` and [the outcome policy](../scripts/quest_diagnostic/EPISODE_RESULTS.md).
Check the paired `video.json`/`frames.jsonl` sample indices and monotonic timestamps.
Do not rewrite original recordings or relabel a failed replay as success. Preserve
all output even when partial; HDF5 existence alone is not a quality assessment.
