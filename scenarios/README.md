# Toast Scenarios

## Scenario Overview

This directory contains **300 saved initial object layouts, not 300 recorded
demonstrations**. Each layout specifies the toaster, plate, bread rack and four
bread slices. Select a saved ID to use its exact poses; reset restores that layout
rather than generating another sample. The three sets remain separate datasets.

## Scenario Sets

| Scenario Set | Object Layout | Number of Scenarios |
|---------------|---------------|---------------------|
| [Mixed](mixed/README.md) | Six object-order permutations | 100 |
| [Fixed TPB](fixed_tpb/README.md) | Toaster → Plate → Bread Rack | 100 |
| [Fixed PTB](fixed_ptb/README.md) | Plate → Toaster → Bread Rack | 100 |
| Total | - | 300 |

Mixed spans all six orders under diverse placement conditions. Its order counts
are 17, 17, 17, 17, 16 and 16, in the order listed in its detailed README.
Fixed TPB perturbs the existing environment-default reference. Fixed PTB uses a
separate reference derived from zero-jitter PTB anchors: plate at XY (0.49, 0.40),
toaster at (0.55, 0), and rack at (0.46, −0.40) metres. That sampling reference
does not replace the environment-default calibration stored in its manifest.

## Object Layout Configuration

Coordinates are environment-local: +X is robot forward, +Y is robot left and +Z
is up. Left-to-right object order follows +Y to −Y. Positions use metres and
quaternions use **wxyz**. `bread_shelf` is the manifest key for the bread rack.
Four bread slices move rigidly with the rack, preserving their rack-relative poses.

All exact reference poses, object scales, generation constraints and final poses
remain in each set's `generation_config.json` and `manifest.json`. The detailed
READMEs retain the experimental conditions and geometric validation limits.
Static layout validity does not establish dynamic stability or robot reachability.

## Position and Orientation Variations

| Set | X offset | Y offset | Yaw offset |
|---|---|---|---|
| Mixed | Toaster/rack ±0.015 m; plate ±0.010 m | ±0.015 m | ±5° |
| Fixed TPB | ±0.020 m | ±0.020 m | ±5° |
| Fixed PTB | ±0.020 m | ±0.020 m | ±5° |

Mixed uses per-order Latin hypercube proposals around Y slots +0.40, 0 and −0.40 m.
The fixed sets use independent uniform proposals around one reference, rejecting
invalid whole configurations. Fixed TPB accepted 100 of 364 proposals; Fixed PTB
accepted all 100. Accepted distributions and constraints differ between the sets.
Z, roll, pitch, scale and rack-relative bread poses remain fixed. Use saved poses
for execution; do not resample to select a scenario.

## Scenario Selection

Each set contains `operator_A` and `operator_B`, with 50 layouts each. Four groups
(`operator_A_1`, `operator_A_2`, `operator_B_1`, `operator_B_2`) each contain 25.
`group_index` is 1–25; `operator_index` is 1–50. ID suffixes are not assignment indices.

Run from the repository root after completing [installation](../README.md):

```bash
bash scripts/run_mj.sh --gui scripts/tools/view_make_toast_scenario.py \
  --scenario_manifest scenarios/fixed_tpb/manifest.json \
  --scenario_group operator_B_1 --group_index 1 --steps 0
```

This selects `toast_base_20261109_025`. Use `scenarios/mixed/manifest.json` or
`scenarios/fixed_ptb/manifest.json` to select another set, with its own assignments.
Alternatively pass `--scenario_id` with an ID from that set's manifest. Group
selection and explicit-ID selection are mutually exclusive. `R` resets the layout.
The viewer/runtime default manifest remains Mixed when no manifest is supplied;
omitting all selection options retains the original environment layout.

## Demonstration Collection

The viewer does not record demonstrations. Follow [recording and playback](../docs/RECORDING.md)
for Quest pairing, recording controls and HDF5/video replay. The host launcher
continues to use **Fixed TPB**, with default `operator_B_1`, index 1:

```bash
python3 scripts/record_quest_base.py --group operator_B_1 --index 1 --dry-run
python3 scripts/record_quest_base.py --group operator_B_1 --index 1
```

Its dry-run resolves assignments and host/container paths without launching Docker.
Custom Quest commands select other manifests explicitly. Every recording retains
its manifest snapshot and hash, scenario ID and operator/group metadata. Replay
uses the recording's adjacent snapshot, so older recordings do not depend on the
current scenario folder name. HDF5 structure and success labels are unchanged.

## Reproducibility

| Set | Generation seed | Assignment seed |
|---|---:|---:|
| Mixed | 20261108 | 20261109 |
| Fixed TPB | 20261109 | 20261110 |
| Fixed PTB | 2026110901 | 2026110902 |

The directory migration preserves every non-README scenario file byte-for-byte,
including manifests, configurations, assignments, poses, HTML, images and inputs.
Only the detailed README paths/links change. Generation-time hashes and paths are
historical evidence, not current runtime paths. The immutable source archive,
release integrity inventory and earlier relocation records retain their old names.

| Historical prefix | Current directory |
|---|---|
| `scenario_delivery` | `scenarios/mixed` |
| `scenario_delivery_base` | `scenarios/fixed_tpb` |
| `scenario_delivery_base_ptb` | `scenarios/fixed_ptb` |

The provenance verifier maps historical input paths to their current locations
without rewriting evidence. The fixed-set reproduction tool restores the old
layout **only in a temporary workspace**, overlays checksum-verified archived
sources, and writes generated output to a separate empty directory:

```bash
MJ_REBUILD=$(mktemp -d /tmp/toast-ptb-rebuild.XXXXXX)
python3 scripts/tools/reproduce_toast_generation.py \
  --set scenarios/fixed_ptb --output "$MJ_REBUILD"
```

Use `scenarios/fixed_tpb` for the other fixed set. Historical `--set` names remain
accepted for compatibility. Installed checksum-pinned assets and the documented
CPU Python dependencies are required. Mixed reproduction uses its documented
current generator; exact layout/assignment reproduction is distinct from
byte-for-byte regeneration of historical metadata. See [Mixed reproduction](mixed/README.md#reproduction)
and [generation provenance](../docs/release/PROVENANCE.md).

## Directory Structure

```text
scenarios/
├── README.md
├── mixed/
├── fixed_tpb/
└── fixed_ptb/
```

Each set keeps `README.md`, `ASSIGNMENTS.md`, `assignments.csv`, `distribution.json`,
`generation_config.json`, `manifest.json`, `overview_cards.html`, `poses.csv` and
`inputs/`. The fixed sets also retain their `images/` directories. The Mixed
reference source snapshots and generation-history input remain in `mixed/inputs/`.
No sets are merged and no scenarios are added or removed.
