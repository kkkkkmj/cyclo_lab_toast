# Provenance, assets and release changes

## Source relationship

This is a new, history-free distribution snapshot of the latest working files in the development checkout, including uncommitted files. Source HEAD: `d8ac88d` (full SHA in `source_snapshot.json`). Direct toast baseline: [badajhong/cyclo_lab, 5f5086d11f664494119086de30a9e925b12022ad](https://github.com/badajhong/cyclo_lab/commit/5f5086d11f664494119086de30a9e925b12022ad). Its direct child is `761c8ac77ccbe7841966e535fa7202d7be83c7a1`. The local `upstream` URL names badajhong; local ancestry checks confirm this baseline. Remote freshness could not be checked from the shell.

[ROBOTIS-GIT/cyclo_lab](https://github.com/ROBOTIS-GIT/cyclo_lab) is the underlying framework, robot/IK/recorder source. Package repository metadata, preserved copyright headers, LICENSE files and project structure identify that source. The available history is flattened at `ba34eae6a7e705e7f6466334e4249e1b9d4ef02b` (Initial commit); it contains vendored trees rather than submodule commit links. A precise ROBOTIS commit/merge-base is **not recoverable from this evidence**. The initial commit must not be mislabeled as a ROBOTIS commit.

The original worktrees, branches, remote settings, unstaged changes and Git history are not modified. The new repository deliberately does not import old Git history, credentials, recordings or local measurement reports. `source_snapshot.json` records hashes of included source files; `exclusions.json` records exclusions. Scenario reproduction inputs and original provenance hashes are retained as evidence even when current code differs.

## Retained license texts

- `LICENSE`: original Apache-2.0 text, byte-identical to development source and direct baseline.
- `LICENSE-IsaacLab`: original BSD-3-Clause notice, byte-identical to source and baseline.
- `THIRD_PARTY_LICENSES.md`: original notices for whole_body_tracking, zenoh_ros2_sdk and IsaacLab-Arena retained, with this audit linked.
- Vendored IsaacLab `LICENSE` and `LICENSE-mimic`, ai_sapiens `LICENSE`, zenoh_ros2_sdk `LICENSE`, Arena `LICENSE.md` and source headers are retained. No dependency was changed to a new upstream version.
- Vendored source tree hashes at the flattened initial commit: IsaacLab `755ead438df32ae3f8c4d7d46f4b64bb2ba0a374`, Arena `49381306b56876e8b61bbe20ae22394ce68f3cb1`, ai_sapiens `9e121eabd0780ee974d361b145eb566f8b373242`, zenoh_ros2_sdk `372cc44d624aca08dbda9650d70dcea4b87f183a`. These are **tree hashes**, not upstream commit IDs.

The public ROBOTIS project also identifies Apache-2.0 and BSD-3-Clause licenses. File-level notices continue to govern; this release does not assign a separate license or assert ownership of upstream components.

## External asset acquisition

| Asset | Source and treatment |
|---|---|
| FFW-BG2 robot USDs | Preserved from the Cyclo Lab source, under its retained notices. These are actual local Git blobs, not unresolved LFS pointers. |
| RoboDojo toaster, bread, plate and legacy shelf | Not republished; fetch using `python3 scripts/tools/download_make_toast_assets.py`. `asset_manifest.json` pins revision `63fcc045f2e974902eb7800d29de48004cf86016` and every SHA256/size. The manifest and [official dataset page](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo/tree/main) identify Apache-2.0. Review upstream terms for your use; no demonstration/training dataset download is needed. |
| Four-groove rack `bread_slot.usdz` | Source record only says it was copied from Downloads. Author, original URL and redistribution grant are absent. The binary is excluded and ignored. Obtain the exact file and permission directly from its rights holder; no public authorized download URL has been established. Run `python3 scripts/tools/install_bread_slot.py /path/to/authorized/bread_slot.usdz`. Required SHA256: `338eb23d759224c0686857b3e793070b2bf03f9c7fe25f872a3c598bd67330d8`. Hash verification proves identity, **not permission**. The wrapper `rack.usda`, offsets, tests and scenario poses are preserved. Until the file is lawfully acquired, simulation and mesh geometry checks are blocked. |
| Packing table | NVIDIA Isaac Sim configured cloud asset root + `/Isaac/Props/PackingTable/packing_table.usd`; fetched by Isaac Sim under NVIDIA terms, including referenced materials. Not bundled. |
| Other inherited missing LFS assets | 66 initially unavailable source pointers enumerated in `missing-lfs.json`; all have now been recovered and hash-verified in isolated audit storage (see `lfs_audit.json`), principally unrelated robot/food textures, motion and documentation media. Excluded because they are unrelated to toast; they are not published as unresolved pointers. This release supports the toast workflow, not every inherited upstream example. |

Downloaded RoboDojo and rack files used for local CPU validation are ignored and are not part of the commit or Docker publication. A new lab must independently obtain them. No small substitute mesh, altered physics or relaxed success tolerance was introduced to hide missing assets.

## Current settings (unchanged)

From `FFW_BG2.py` and the v2 overrides in `bimanual_env_cfg.py`:

| Joint group | Stiffness / damping | Velocity limit |
|---|---:|---:|
| Lift | 10000 / 100 | 0.2 m/s |
| Arm joints 1–2 | 600 / 30 | 15 rad/s |
| Arm joints 3–6 | 600 / 20 | 15 rad/s |
| Arm joint 7 | 200 / 3 | 6 rad/s |
| v2 gripper masters | 100 / 4 | 6.5 rad/s |
| v2 gripper slaves 2–4 | 100 / 4 | Authored USD values; no runtime override |
| Head | 150 / 3 | 2 rad/s |
| Carriage | 8000 / 120 | 0.12 m/s |

The base shared gripper defaults 2.2 rad/s and slave gains 2/0.5 are overridden by v2. Do not confuse them with the effective serving configuration. Source settings are not measurements of actual tracking speed.

## Distribution-only changes

- New English root guide and per-set links replacing duplicated setup/operation instructions.
- Unique `cyclo-toast-teleop` Compose project/container/image, preserving `/workspace/cyclo_lab`, source imports and relative host mounts. Removed the inherited shell-history bind, which could create a directory at a file mount on a new PC.
- Excluded personal/history/media/unknown-rights artifacts and unavailable LFS blobs; retained license and reproduction inputs.
- Added explicit asset installation/preflight and release validation/publishing tools.
- Updated a loop test fixture with the cooperative `shutdown.requested=False` object introduced in the latest implementation. No runtime shutdown or physics code is modified.

Known code/documentation distinctions: v2 needs at least one cooked/served ID despite an inherited “both slices” class docstring; 90% entry threshold differs from the shared 85% pressed predicate. Neither was changed to match a prose checklist.

For the updated rights-holder checklist, installer behavior, all 66 LFS results and incomplete cloud/MDL closure, see [asset audit](ASSETS.md).

## Historical generation source bundle

`generation_sources/index.json` binds each preserved source SHA256 to its original
path and the exact source Git commit containing those bytes. The one pre-35mm
configuration absent from the available Git objects is reconstructed by the
previously documented inverse migration; its bytes match the original manifest
SHA256 exactly. These files retain their original contents and notices. No saved
manifest hash was replaced with a current hash.

`verify_fingerprint` now checks **generation evidence**, not an assertion that
current runtime source is identical. Source evidence is read from the path-bound,
SHA256-checked archive; asset hashes still require the actual installed bytes and
never fall back to a source archive. Current control/task semantics are checked
separately by `current_contract`, serving-success/gain/LED tests and the new
runtime metadata tests. The historical 20mm value must not control the current
40mm task.

The base/PTB historical reproduction tool creates a temporary independent tree,
overlays exact archived generation sources, copies only checksum-verified assets,
and runs the original generator. It never mutates the current runtime or original
scenario files and never consults a developer repository or Git cache:

```bash
python3 scripts/tools/reproduce_toast_generation.py \
  --set scenario_delivery_base_ptb --output /tmp/new-ptb-generation
```

The output must be new/empty. PTB's nine generated files are compared byte-for-byte
with the saved delivery, including metadata; no assertion is removed or ignored.
The source bundle includes the older other-set fingerprints for evidence
verification, but only fixed base/PTB generation is exposed by this tool. External
rack authorization and the pinned USD assets remain prerequisites. CPU dependency
versions used for the new validation are recorded in `cpu_environment.json`.
