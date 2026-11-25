# Scenario directory migration validation

Baseline: `7fc8b5ebfa33de040f70cb5fa3552044f6e7c787`.
The independent `cyclo_lab_toast` copy retains this history. Original-state remote
publication and Private visibility were confirmed by the maintainer before this
migration. No push or remote download was performed during this change.

## Scope and preserved evidence

| Before | After | Tracked files moved |
|---|---|---:|
| `scenario_delivery/` | `scenarios/mixed/` | 13 |
| `scenario_delivery_base/` | `scenarios/fixed_tpb/` | 115 |
| `scenario_delivery_base_ptb/` | `scenarios/fixed_ptb/` | 115 |

All 243 files are retained. The three detailed READMEs have updated commands and
relative links; the other **240 files are byte-identical** to the baseline Git
objects. They include poses, IDs, assignments, manifest/configuration files,
HTML, images and inputs. No scenario was regenerated in place.

| Manifest | Preserved SHA256 |
|---|---|
| Mixed | `e01b22564cb52b7f2e7edf2f8255270bdd9e972702a269b1bc01747dfee5e95e` |
| Fixed TPB | `31c7399a95df898e53295aa5a78e580ac2c4b36e95bdc1b660314104c424170d` |
| Fixed PTB | `11d3bc5d0ec4b05df4422cbc471539012a61b3d8957dcf2ca948ffb025ba9c46` |

Robot/control/task/physics code and assets retain their original bytes, except
for the default manifest path in the standalone scenario loader. License texts,
copyright headers and the four vendored dependency trees are unchanged. Their
Git tree mode is `040000`, not submodule mode `160000`; `.gitmodules` is retained.
The existing LFS object is preserved and passes local LFS integrity checks.

## Remaining historical names

A search of tracked files distinguishes these uses:

- **Current execution paths:** changed to the new directories in the loader,
  viewer, recorder defaults, geometry/validation/generation/render tools and tests.
  The recorder still selects Fixed TPB; the viewer/runtime default remains Mixed.
- **Historical provenance:** retained in saved manifests/configurations/inputs,
  `docs/release/*.json`, the archived `generation_sources/`, earlier relocation
  evidence, the geometry-source attribution and the generator's historical
  `remote_reference`. These strings are not current launch/download instructions.
- **Compatibility:** `toast_scenario_paths.py` maps old evidence prefixes;
  `reproduce_toast_generation.py` accepts old and new set names, restoring old
  directories only inside its temporary historical workspace. Regression tests
  deliberately exercise old input names. Original expected hashes are unchanged.

Recording replay continues to load its adjacent manifest snapshot, validating
its hash rather than following an obsolete checkout path in metadata. No HDF5
schema, observation/action format or success-label logic changed.

The installation URL now names `kkkkkmj/cyclo_lab_toast`. The optional publishing
helper also targets only that Private repository and verifies the push URL;
**it was not executed**. Upstream asset URLs and historical repository references
remain unchanged. Existing Docker project/image names and container paths are
preserved; Docker was not started, stopped or rebuilt.

## Executed validation

CPU tests used an existing Python environment with CUDA visibility disabled and
CPU thread limits. Required ignored RoboDojo files were copied from an existing
local audit cache only after matching every pinned asset SHA256. They are not
included in the commit. No network acquisition or global environment update was
performed. Test logs and regenerated outputs were kept outside the repository.

| Check | Result | Evidence/limits |
|---|---|---|
| Original checkout preservation | PASS | Original tracked bytes and all `.git` file hashes, refs, remote settings and clean status unchanged |
| Scenario integrity | PASS | 100 + 100 + 100; 240 immutable files match baseline bytes |
| Selection and initial config | PASS | All 300 IDs, group/index and operator/index choices; exact saved poses; idempotent loader application |
| Existing release CPU suites | PASS | 41 suites, 259 tests, zero skips/failures |
| Migration regression | PASS | 3 tests; included in the release runner for subsequent runs |
| Additional replay CPU suites | PASS | 4 suites, 27 tests: contact replay, replay validation, scene audit, slave-gain tests |
| Recorder dry-run | PASS | Fixed TPB default preserved; group boundaries and host/container bridge/run paths checked |
| Historical Fixed TPB regeneration | PASS | Nine generated files equal saved files byte-for-byte in a separate output directory |
| Historical Fixed PTB regeneration | PASS | Nine generated files equal saved files byte-for-byte, checked by the existing suite |
| Mixed regeneration | PASS | All scenario entries and assignments/poses/config/distribution/assignment report identical; current manifest differs only in runtime contract/provenance as already documented |
| Generation provenance | PASS | Path-bound archived source hashes and installed asset hashes verified; changed evidence is rejected |
| Local assets/LFS | PASS | Pinned local assets and actual LFS object hashes verified |
| Syntax/data parsing | PASS | All tracked Python, shell and JSON files checked |
| Documentation links | PASS | Local targets in changed guides resolve; external URLs were not fetched |
| Docker path configuration | PASS | Compose configuration renders the new checkout at `/workspace/cyclo_lab`; no container launched |
| Remote LFS download | NOT TESTED | Maintainer will push; network retrieval was not performed |
| Isaac Sim/GPU reset, VR, live recording and GPU playback | NOT TESTED | No simulator/headset session launched; CPU config/mock checks are not live physics tests |
| Browser rendering and external-link reachability | NOT TESTED | Static paths/data checked; no browser or network validation |

The existing rack-settling and simulator-shutdown limitations remain. This
migration does not claim physical stability, reachability or full-task replay
fidelity. The Mixed current generator intentionally does not reproduce historical
manifest metadata bytes; saved original metadata is preserved, not replaced.

## Re-run and inspect

From the repository root, using Python with the documented CPU dependencies:

```bash
python3 scripts/tools/check_release.py --assets
python3 scripts/tools/test_scenario_relocation.py
python3 scripts/tools/run_release_cpu_tests.py --output /tmp/new-toast-refactor-tests
```

Use a new output directory. The suite now includes the migration regression.
For individual modifications and renames, inspect the migration commit:

```bash
git diff --stat 7fc8b5ebfa33de040f70cb5fa3552044f6e7c787 HEAD
git diff --name-status --find-renames 7fc8b5ebfa33de040f70cb5fa3552044f6e7c787 HEAD
```

The [scenario guide](../scenarios/README.md) gives current paths and reproduction
commands; [historical provenance](release/PROVENANCE.md) retains original evidence.
