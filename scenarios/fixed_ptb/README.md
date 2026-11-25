# Toast Task — 100 Fixed-Base PTB Scenarios

## Overview

This [manifest](manifest.json) provides 100 initial object configurations for collecting robot
manipulation demonstrations around **one fixed reference configuration**. **PTB** means
**Plate → Toaster → Bread Rack**, from robot left to right. The
[six-order set](../mixed/README.md), [fixed T/P/B set](../fixed_tpb/README.md),
environment defaults and default manifest remain unchanged. These files are placement data, not
recorded demonstrations. Selecting an ID restores the same configuration on reset.

## Scenario Design

Coordinates use the environment frame: **+X is robot forward, +Y is robot left, and +Z is up**.
Left-to-right order follows **+Y → −Y**. Positions are in **metres (m)**, quaternions use **wxyz**,
and yaw is in degrees about +Z. Cloned environments add their environment origins.

The reference uses the existing six-order generator's **zero-jitter PTB anchors**: object-specific
X coordinates and Y coordinates (+0.4, 0, −0.4) by rank. It is not taken from any sampled scenario.
The full XY/yaw variation envelope passes the static checks below, so no further anchor adjustment
is needed. In particular, the plate reference X=0.49 m leaves room for both signs of ΔX; the other
fixed-base set's default plate at X=0.43 m would reject much of the negative-X side.

| Object | Reference position (X, Y, Z), m | Reference quaternion (w, x, y, z) | Yaw | Scale |
|---|---|---|---:|---|
| Plate | (0.49, 0.40, 1.004222776) | (1, 0, 0, 0) | 0° | (1.5, 1.5, 0.22) |
| Toaster | (0.55, 0, 1.0818) | (0.2588190450974359, 0, 0, 0.9659258262904309) | 150° | (1, 1, 1) |
| Bread Rack | (0.46, −0.40, 1.0382000207901) | (0.7071067811865475, 0, 0, −0.7071067811865475) | −90° | (1, 1, 1) |

[generation_config.json](generation_config.json) stores the exact reference, including all four
bread poses. `generation.reference_poses` is the sampling reference. The manifest's `baseline` and
`baseline_bread` deliberately retain the **environment-default calibration** required by the loader;
they do not redefine the sampling reference or modify the environment defaults.

| Object | ΔX | ΔY | Δyaw |
|---|---|---|---|
| Plate | [−0.02, +0.02] m | [−0.02, +0.02] m | [−5, +5]° |
| Toaster | [−0.02, +0.02] m | [−0.02, +0.02] m | [−5, +5]° |
| Bread Rack | [−0.02, +0.02] m | [−0.02, +0.02] m | [−5, +5]° |

All nine offsets are sampled independently and uniformly for each candidate. XY offsets apply in
the environment frame; the yaw-offset quaternion left-multiplies the reference quaternion. Offsets
never accumulate between scenarios. Z, roll, pitch and scale remain fixed. Invalid whole
configurations are rejected and resampled; the accepted distribution is reported explicitly.

### Generation and exclusion criteria

| Check | Applied condition |
|---|---|
| Table limits | Full containment in the authored tabletop support polygon: approximately X [0.341857712, 1.058142302], Y [−1.318215319, 1.118215316] m; top Z=0.994051339 m |
| Object footprint | Current USD mesh/collider convex XY bounds at the saved orientation/scale; main-object bounds expanded by 1 mm; rack and all four breads combined |
| Object spacing | Strictly positive gap between main-object footprints and between bread footprints |
| Order | Plate Y > toaster Y > rack Y in every accepted configuration |
| Plate | Environment-frame X >0.419 m, as required by the unchanged task success predicate |
| Duplicates | Reject repeated pose signatures within this set or matches to either existing set; use a separate ID prefix |

These are the fixed-base set's support/non-overlap criteria, with PTB order. No physical parameter,
task tolerance, or success criterion is relaxed. The additional 20 mm edge/60 mm approach filters
of the six-order generator are not applied as sampling filters here.

Before sampling, the generator computes continuous yaw extrema of authored bound vertices,
including extrema inside the ±5° interval, and adds the complete ±20 mm translation intervals.
Containment and separation of the resulting conservative envelopes cover the **whole proposal
range**, not just its corners or the 100 sampled poses.

| Full-range envelope check | Conservative clearance |
|---|---:|
| Plate to tabletop edge | 29.875 mm |
| Toaster to tabletop edge | 59.162 mm |
| Rack + four breads to tabletop edge | 23.238 mm |
| Plate / toaster separation | 138.195 mm |
| Toaster / rack-with-bread separation | 115.171 mm |
| Plate / rack-with-bread separation | 541.571 mm |
| Plate X above the success threshold | 51.000 mm |

**100 candidates were accepted; 0 were rejected.** There is no rejection-induced truncation in
this realization. The finite sample is not perfectly symmetric or evenly spaced: plate ΔX has
49 negative and 51 positive values, range **[−19.743, +18.911] mm**, mean **+0.175 mm**. The full
set's mean ΔY is −1.107 mm for the plate, −0.945 mm for the toaster and −0.595 mm for the rack.
These finite-sample offsets are retained. Exact extrema, means, standard deviations, quartiles and
sign counts for every object/axis/group are in [distribution.json](distribution.json), including `all`.
The sampled configurations have minimum object gap **145.278 mm** and minimum tabletop clearance
**27.846 mm** beyond the expanded footprint. These distances do not prove manipulation clearance.

### Reference poses and bread placement

The native four-groove rack is 230 × 130 × 45 mm. Its rigid transform moves all four bread slices
together; no independent bread noise is added. The unchanged rack-relative poses are:

| ID | Local X (m) | Local Y (m) | Local Z (m) |
|---|---:|---:|---:|
| bread_0 | 0.084392445 | 0.000249905 | 0.044351338865 |
| bread_1 | 0.024392445 | 0.000249905 | 0.044351338865 |
| bread_2 | −0.035607555 | 0.000249905 | 0.044351338865 |
| bread_3 | −0.095607555 | 0.000249905 | 0.044351338865 |

Their common rack-relative quaternion is approximately (0.7071067812, 0, 0.7071067812, 0), with
unit scale. The toaster lever, bread carriage and LED retain their existing body-relative
relationships. The known rack-settling issue remains unresolved.

### Reproduction

Generation seed: **2026110901**. Assignment seed: **2026110902**. The
[generator](../../scripts/tools/generate_ptb_toast_scenarios.py) refuses a nonempty output directory.
It reads tracked calibration/evidence and duplicate signatures from the two existing manifests,
plus the installed checksum-pinned assets. For historical byte reproduction, the command below uses archived generation sources with the original 20mm metadata; current runtime remains strict <40mm. It never writes to those sets.

Run from the checkout root with a CPU Python environment containing NumPy, SciPy, torch, OpenUSD
`pxr`, Shapely 2.x, Matplotlib and Pillow. Historical generation notes listed Python 3.12.14, NumPy 2.5.1,
SciPy 1.17.0, torch 2.11.0+cu128, usd-exchange 2.3.0 (OpenUSD 0.25.5), Shapely 2.1.2,
Matplotlib 3.10.8 and Pillow 12.2.0. This is separate from the simulator's Python environment.
The [dependency guide](../../README.md) describes runtime dependencies and
asset downloads. `TOAST_PYTHON` below must point to your prepared CPU interpreter.

```bash
export TOAST_PYTHON=python3
PTB_OUTPUT=$(mktemp -d /tmp/toast-ptb-rebuild.XXXXXX)
"$TOAST_PYTHON" scripts/tools/reproduce_toast_generation.py \
  --set scenarios/fixed_ptb --output "$PTB_OUTPUT"
"$TOAST_PYTHON" scripts/tools/render_base_scenario_pngs.py \
  --delivery "$PTB_OUTPUT" --output "$PTB_OUTPUT/images"
"$TOAST_PYTHON" scripts/tools/test_ptb_toast_delivery.py -v
```

The test command validates the checked-in PTB delivery and regenerates its nine data/card/input
files in a separate temporary folder for byte comparison. README and PNGs are separate outputs.
Other library versions can change serialization or floating-point allocation details; use the
saved manifest to select the delivered IDs without regenerating them.

## Installation and operation

See the [project guide](../../README.md) for installation, Quest pairing, recording and playback.
Select this directory’s manifest explicitly; the base recording launcher always uses `scenarios/fixed_tpb`.

## Operator Assignments

**operator_A and operator_B each have 50 scenarios**, split into two groups of 25.
All four groups use **Plate → Toaster → Bread Rack**.

<table>
  <thead><tr><th>Operator</th><th>Group</th><th>Scenarios</th><th>Group index</th><th>Operator index</th><th>First scenario ID</th></tr></thead>
  <tbody>
    <tr><td rowspan="2">operator_A</td><td>operator_A_1</td><td>25</td><td>1–25</td><td>1–25</td><td>toast_base_ptb_20261109_000</td></tr>
    <tr><td>operator_A_2</td><td>25</td><td>1–25</td><td>26–50</td><td>toast_base_ptb_20261109_037</td></tr>
    <tr><td rowspan="2">operator_B</td><td>operator_B_1</td><td>25</td><td>1–25</td><td>1–25</td><td>toast_base_ptb_20261109_020</td></tr>
    <tr><td>operator_B_2</td><td>25</td><td>1–25</td><td>26–50</td><td>toast_base_ptb_20261109_098</td></tr>
  </tbody>
</table>

IDs run from `toast_base_ptb_20261109_000` through `toast_base_ptb_20261109_099`; an ID suffix is
not an assignment index. `group_index` is 1–25; `operator_index` is that number for group 1 and
that number +25 for group 2. See [ASSIGNMENTS.md](ASSIGNMENTS.md) and [assignments.csv](assignments.csv).

Allocation starts with seeded 25-per-group labels and attempts 50,000 quota-preserving label swaps.
It balances standardized signed ΔX/ΔY/Δyaw, second moments weighted 0.35, and 25/50/75% quartile
exceedance indicators weighted 1.5. The sum-of-squared-centered-group-feature objective decreases
from **1520.493 to 122.946**. Poses are not altered during allocation. Distribution balance does
not establish equal robot manipulation difficulty or remove finite-sample offsets.

Mean offsets below use **mm, mm, degrees** for each (ΔX, ΔY, Δyaw) triple.

| Group | Count | Plate mean offsets | Toaster mean offsets | Bread Rack mean offsets |
|---|---:|---|---|---|
| operator_A_1 | 25 | (0.249, −1.393, −0.037) | (0.148, −0.546, 0.338) | (1.222, −0.286, 0.173) |
| operator_A_2 | 25 | (0.403, −1.501, −0.071) | (−0.064, −1.020, 0.079) | (0.617, −0.677, 0.234) |
| operator_B_1 | 25 | (−0.127, −0.722, −0.236) | (−0.468, −1.217, 0.040) | (1.029, −0.456, 0.144) |
| operator_B_2 | 25 | (0.175, −0.809, −0.164) | (0.236, −0.998, 0.373) | (1.116, −0.961, 0.289) |

## Using the Scenarios for Data Collection

The task remains `Cyclo-Make-Toast-FFW-BG2-Bimanual-IK-Rel-v2`. The recorder copies the selected
manifest into the new run directory and stores its hash, source path, ID, group and both indices.
The same snapshot configures reset and replay. The runtime reset check compares all seven measured
object poses against the selected manifest before recording starts.

`recording/dataset.hdf5` stores actions/observations/states; per-episode MP4, `episode.json` and frame
mapping files are adjacent. `diagnostic.jsonl` and `run.log` are diagnostic records, not additional
training demonstrations. Success labels use the existing pre-reset outcome policy; `diagnostic=true`
and `training_ready=false` remain. Recorded success does not certify training quality or replay fidelity.
See [recording format and controls](../../scripts/quest_diagnostic/RECORDING.md) for details.

## Usage limitations

Layout constraints and balanced assignments do not guarantee physical stability,
robot reachability or collision-free manipulation. Inspect rack/bread settling
before collection; see [troubleshooting](../../docs/TROUBLESHOOTING.md#scenario-settling-and-control).
Overview cards show projected geometry, not simulator renders or collision meshes.

## Files

| File | Purpose |
|---|---|
| [manifest.json](manifest.json) | 100 layouts, checks, calibration and provenance |
| [assignments.csv](assignments.csv) / [ASSIGNMENTS.md](ASSIGNMENTS.md) | Four-group and parent assignments |
| [poses.csv](poses.csv) | 700 poses keyed by scenario ID and object |
| [generation_config.json](generation_config.json) | Reference, variation ranges, envelope checks, seeds and allocation |
| [distribution.json](distribution.json) | All-set, group and parent variation statistics |
| [overview_cards.html](overview_cards.html) | Self-contained cards with all/A/B/four-group filters |
| [inputs/geometry_evidence.json](inputs/geometry_evidence.json) | Required authored tabletop support evidence |
| [inputs/table_frame.json](inputs/table_frame.json) | Authored table snapshot for card geometry |

Download and open the HTML directly, or run from the checkout root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/scenarios/fixed_ptb/overview_cards.html`.
To rebuild only the cards from the saved manifest:

```bash
export TOAST_PYTHON=python3
"$TOAST_PYTHON" scripts/tools/build_toast_overview_cards.py \
  --delivery scenarios/fixed_ptb \
  --table-source scenarios/fixed_ptb/inputs/table_frame.json
```

### PNG layout sheets

These are **schematic top views, not simulation screenshots**: **+X up, +Y left**. Every card uses
the same coordinate bounds and pixel scale, with the current table/asset dimensions, XY positions
and yaw. Orange denotes the toaster, blue the plate, green the four-groove rack and beige its four
bread slices. The images depict saved initial configurations and do not constitute physical validation.

| Image | Layout | Resolution |
|---|---|---|
| [operator_A_1](images/operator_A_1.png) | 25 cards, 5 × 5 | 8000 × 3520 px |
| [operator_A_2](images/operator_A_2.png) | 25 cards, 5 × 5 | 8000 × 3520 px |
| [operator_B_1](images/operator_B_1.png) | 25 cards, 5 × 5 | 8000 × 3520 px |
| [operator_B_2](images/operator_B_2.png) | 25 cards, 5 × 5 | 8000 × 3520 px |
| [All 100](images/overview_100.png) | 100 cards, 10 × 10 | 16000 × 6920 px |
| [Individual PNGs](images/individual/) | One per scenario ID | 1600 × 680 px |

Cards run left to right, then top to bottom in group-index order. The overview orders groups A_1,
A_2, B_1, B_2. Download large sheets for full-resolution inspection; for example,
[B_1 / 1](images/individual/toast_base_ptb_20261109_020.png).

```bash
export TOAST_PYTHON=python3
"$TOAST_PYTHON" scripts/tools/render_base_scenario_pngs.py \
  --delivery scenarios/fixed_ptb --output scenarios/fixed_ptb/images
```

The renderer checks fresh geometry against the saved HTML, assignments and all pose rows before
rendering. It leaves the manifest, CSVs and HTML unchanged. PNG metadata records IDs, the manifest
hash and common coordinate bounds; individual PNGs also contain exact poses and group indices.

Reproduction dependency versions are recorded in [cpu_environment.json](../../docs/release/cpu_environment.json).
