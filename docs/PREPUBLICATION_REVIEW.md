# Pre-publication review — 2026-11-25

**Decision: C — additional validation and rights confirmation required. Keep the
repository Private.** The included bread rack has no established redistribution
grant. User authorization to upload it is not proof of permission from its rights
holder. No asset was removed/replaced and no visibility change or push was made.

Reviewed revision: `b929be912431a4c6a432f602975a0d1f646dd684`. The maintainer reported
that this revision was pushed and the repository is Private. The connector returned
404, so this session could not independently verify private remote state. Existing
289 CPU-test passes and scenario reproduction results are retained in
[the migration report](SCENARIO_REFACTOR.md); they were not repeated or relabeled
as live GPU/VR evidence. Earlier release documents remain historical evidence.

## Results

PASS means the stated scope was actually checked. NOT TESTED means no successful
end-to-end execution; failed access attempts are listed separately. FAIL in the
rights row means the publication gate is unmet, not a finding of infringement.

| Item | Result | Scope and limitation |
|---|---|---|
| Documentation | PASS | Named public guides reviewed against code; baseline SHA, stale rack exclusion, incorrect fixed-TPB success label and checkout example corrected; local links checked |
| Attribution | PASS | Local direct-baseline Git objects compared; reuse/adaptation/addition distinguished; exact ROBOTIS ancestor remains unknown |
| License | PASS | Retained code license texts/notices identified; this does not license every asset |
| Asset redistribution | FAIL | Rack mesh author/source/license unconfirmed; robot asset-specific scope also needs documented confirmation |
| Fresh clone | NOT TESTED | Network clone blocked; clean independent **local-source** checkout and its inventory check passed |
| Remote LFS | NOT TESTED | Fresh checkout LFS retrieval timed out after 30 s; no successful remote object retrieval |
| Asset acquisition | NOT TESTED | Empty RoboDojo destination; downloader failed DNS and installed no unverified files; fresh `--assets` exited 2 for missing toaster |
| Docker build | NOT TESTED | Daemon socket access denied; configuration rendering passed, build not started |
| GPU operation | NOT TESTED | `nvidia-smi` exited 9 in sandbox; not evidence that the host driver itself is broken |
| Scenario loading | NOT TESTED | Live loading of robot/toaster/plate/rack/four breads not run; previous CPU manifest/pose checks retained |
| Scenario reset | NOT TESTED | No live pose/quaternion error measurements or settling observations |
| VR connection | NOT TESTED | No headset, HTTPS/PIN session or controller input exercised |
| Arm control | NOT TESTED | No physical controller-driven movement or simultaneous bimanual session |
| Gripper control | NOT TESTED | No live trigger-driven opening/closing |
| Recording | NOT TESTED | No new real success/failure/timeout episode; no synthetic replacement recordings |
| Success evaluation | NOT TESTED | Previous CPU predicate/label tests do not establish live task success |
| Playback | NOT TESTED | No new GPU replay, action fidelity measurement or task-success reproduction |
| Repository cleanliness | PASS | Only reviewed documentation changes committed; no generated assets, credentials, recordings or test logs included |

Host GPU memory/process occupancy, active Docker projects/images and listening
ports could not be established. Docker ps/image ls returned permission denied;
`ss -ltn` printed a netlink permission error despite exit code 0. The sandbox's
process namespace is not a complete host process inventory. No simulator,
container, sensor or training process was started, stopped or reconfigured.
NVIDIA cloud loading, screenshots, camera outputs and graceful native shutdown
therefore remain untested. There are **no new screenshots or recording paths**.

## Attribution

Original framework: [ROBOTIS Cyclo Lab](https://github.com/ROBOTIS-GIT/cyclo_lab).
Direct toast baseline: [badajhong/cyclo_lab at 5f5086d11f664494119086de30a9e925b12022ad](https://github.com/badajhong/cyclo_lab/commit/5f5086d11f664494119086de30a9e925b12022ad).
The baseline commit was present in a separate local Git object store, read only.
Comparisons use those committed bytes, not uncommitted developer worktrees.

| Component | Verified relationship to direct baseline |
|---|---|
| Robot model/config | `FFW_BG2.py` and selected `FFW_BG2_without_mimic.usd` identical; resolved asset bytes compared to baseline LFS OID |
| Simulation framework | Inherited Cyclo Lab / vendored Isaac Lab; no claim to authorship of the simulator/framework |
| Existing toast environment | Baseline already contains single/bimanual toast environments; current environment configuration is adapted |
| IK and gripper action | `arm_action.py` and `gripper_action.py` identical; existing primitives reused |
| Meta Quest WebXR | Quest server/teleoperation integration absent at direct baseline; added later in this development lineage |
| Bimanual teleoperation | Baseline already supplies bimanual task/action infrastructure; Quest input mapping integrates with it |
| Toast cycle / success | `toast_cycle.py` and `bimanual_mdp.py` existed at baseline and differ now: adaptations, not an entirely new task foundation |
| Scenario generation | Current generation/selection modules added relative to baseline; saved corpora subsequently reorganized without changing layouts |
| Demonstration recording | `record_demos.py` and task `recorders.py` identical; Quest recorder extends the standard manager with episode control/metadata |
| HDF5/video | Reuses Isaac Lab recording; replay/video modules already existed and were adapted; format ownership is not claimed |
| Docker deployment | `Dockerfile.base` identical; Compose configuration adapted and transient launch wrapper added |
| Diagnostics / validation | Project-specific Quest/scenario checks added on top of inherited framework tooling |

Development history includes `87d971f` (Quest/scenario workflow), `f27d24e`
(scenario relocation) and `f09bdb6` (Quest MP4/outcome integration). File absence at
one baseline establishes an addition relative to it, **not exclusive individual
authorship or proof that no external code was reused**. Existing notices remain.
The upstream ROBOTIS exact source commit cannot be recovered from the flattened
available lineage; no arbitrary upstream SHA has been assigned.

## Licenses and assets

This is an evidence inventory, not a blanket redistribution grant. Code notices
must remain with their components. Repository inclusion alone is not rights proof.

| Component / asset | Original source | License evidence | Current delivery | Redistribution confirmation / required action |
|---|---|---|---|---|
| ROBOTIS Cyclo Lab code | ROBOTIS-GIT/cyclo_lab | Apache-2.0 and BSD-3-Clause repository texts/file notices | Tracked source | Code license evidence present; retain notices and identify modifications |
| Direct Toast Baseline code | badajhong/cyclo_lab, pinned SHA above | LICENSE and LICENSE-IsaacLab match baseline bytes | Adapted/reused source | Code evidence present; do not extend it automatically to all external assets |
| Isaac Lab | Vendored isaac-sim/IsaacLab | BSD-3-Clause; separate LICENSE-mimic and dependency notices | Vendored snapshot | Preserve component notices; no upstream version substitution |
| IsaacLab-Arena | isaac-sim/IsaacLab-Arena | Apache-2.0 in vendored LICENSE.md | Vendored snapshot | Code evidence present; external assets have separate terms |
| ai_sapiens | ROBOTIS-GIT/ai_sapiens | Apache-2.0 in vendored LICENSE | Vendored snapshot | Code evidence present; retain notices |
| zenoh_ros2_sdk | ROBOTIS-GIT/zenoh_ros2_sdk | Apache-2.0 in vendored LICENSE | Vendored snapshot | Code evidence present; retain notices |
| RoboDojo toaster/bread/plate/legacy shelf | RoboDojo-Benchmark/RoboDojo, revision `63fcc045f2e974902eb7800d29de48004cf86016` | Official dataset page declares Apache-2.0; pinned card could not be fetched in this review | Download on demand; ignored binaries | Published dataset license evidence present; retain attribution and verify any file-specific terms before redistribution; acquisition remains untested here |
| NVIDIA table/materials/Isaac Sim | NVIDIA Isaac Sim distribution and asset cloud | NVIDIA product/asset terms; no blanket repository license | External runtime download/base image | Not bundled; operator must review applicable terms; cloud asset dependency closure unverified |
| FFW-BG2 robot USD | Direct Cyclo Lab baseline / ROBOTIS lineage | Repository-level notices retained; no independently established asset-specific grant found in this review | Tracked Git blobs | Identity/source confirmed; document rights-holder coverage for these assets before claiming comprehensive asset clearance |
| `bread_slot.usdz` | Local Downloads copy; original creator/source unknown | No license/readme in archive; no authored rights metadata found | Tracked 72,165-byte Git blob | **Unconfirmed — publication blocker.** Obtain original source/license or rights-holder grant tied to exact file/hash |
| `rack.usda` | Project wrapper built by `scripts/tools/build_bread_slot_asset.py` | Repository source-license context; no separate mesh grant | Git LFS object | Wrapper provenance is established, but its reference does not authorize redistributing the mesh; retain wrapper and resolve mesh rights |

The [official ROBOTIS repository](https://github.com/ROBOTIS-GIT/cyclo_lab) identifies
Apache-2.0/BSD-3-Clause, and the [official RoboDojo dataset page](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo)
identifies Apache-2.0. These live pages do not replace pinned historical source
comparison or establish the unknown rack's license. NVIDIA terms and distribution
links are available in [Isaac Sim download documentation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/download.html).

### Rack investigation

The tracked binary and Downloads copy both hash to
`338eb23d759224c0686857b3e793070b2bf03f9c7fe25f872a3c598bd67330d8`.
The archive contains only `bread_slot.usdc`, with no archive comment. Authored
stage metadata supplies default prim, millimetre units and Y-up; custom layer
data is empty and no authored author/license/copyright/assetInfo evidence was
found. Generic USD schema documentation is not asset authorship metadata.
The retained development record traces copying from Downloads on 2026-11-08;
it supplies no original website, creator or permission document.
USD metadata inspection used the existing CPU Python/USD installation explicitly;
it was not counted as a fresh-runtime installation test.
The wrapper hash remains `bf9d759dba0cc619eda5483bfba87db934e2b7ae1c4ac86af833cfaa5323dd52`.
No geometry was edited, no asset was deleted, and neither the user upload record
nor these hashes is treated as a copyright-holder grant.

## Fresh-installation scope

A new local-source clone used `--no-hardlinks` and LFS smudging disabled. It has
its own Git object store and no inherited ignored RoboDojo cache or Python venv.
The origin was changed to the new GitHub repository. No existing LFS cache was
silently supplied. `check_release.py` passed with system Python; `--assets`
correctly failed on absent downloaded assets. The network downloader failed DNS.
LFS retrieval timed out; the wrapper remains a pointer in this fixture. This is
**not a successful network fresh installation**, and previous cache-backed passes
are not substituted for it.

Compose rendering passed without a daemon. The bind mount resolves to this clean
checkout at `/workspace/cyclo_lab`; versions are Isaac Sim 5.1.0, Isaac Lab 2.3.0
(vendored VERSION), and constrained torch 2.7.0. No Docker image build or installed
dependency/import check ran. Dependency ranges remain incompletely locked.
The inherited project/image name is `cyclo-toast-teleop`; host networking/IPC,
shared host devices and all-GPU reservation require operator review. A distinct
project/image and fresh checkout avoid accidental tag/cache reuse but do not by
themselves make concurrent GPU workloads safe. See [live validation](LIVE_VALIDATION.md).

## Changes and evidence

This review changes documentation only:

- Root README: exact direct-baseline commit, verified contribution boundaries,
  rights/live-validation status and inherited Docker-name explanation.
- `THIRD_PARTY_LICENSES.md`, `docs/ASSETS.md`: correct included-rack status and
  distinguish upload approval from redistribution rights.
- Fixed TPB README: remove incorrect always-false success-label statement and
  update the remaining old checkout-name example.
- `ASSET_SOURCES.md`: add a scope note above historical baseline descriptions;
  preserve the original text and point to current task/rights guidance.
- `docs/README.md`: link this review and operator procedure.
- This report and `LIVE_VALIDATION.md`: separate current audit from past release
  evidence, with explicit unexecuted steps and required measurements.

Transient evidence is outside Git under
`/home/mj/nrf_humanoid/cyclo_publication_audit_20261125/`: baseline comparison JSON,
rack metadata JSON, GPU/Docker/port/network/preflight/download logs, rendered
Compose configuration and the unpopulated fresh-local fixture. These are audit
locations, not installation dependencies. No screenshot or demonstration is
claimed. The original protected checkout is verified separately without writes.

## Remaining publication gates

1. Establish rack rights and document any remaining robot asset license scope.
2. Complete remote Git/LFS retrieval, pinned asset acquisition, isolated Docker
   build and NVIDIA cloud loading from a clean checkout on an accessible host.
3. Measure GUI initial/reset pose errors, settling, cameras and clean shutdown
   for six Mixed orders and both fixed sets.
4. Complete real Quest control, real success and failure/timeout recordings,
   metadata/video checks and GPU action-replay fidelity/task-success checks.

Do not label these pending items PASS based on CPU mocks, a generated HDF5 file,
or a license applying to unrelated code. Do not automatically make the repository
Public after pushing these documentation corrections.
