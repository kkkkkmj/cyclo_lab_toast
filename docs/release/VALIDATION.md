# Release validation

> Historical report: the results and publication/retry statements below describe
> the 2026-11-11 validation session. They are retained as recorded, including
> failed and unverified checks. For the separate 2026-11-21 repository-access
> review, see [repository-access history](PUBLICATION.md#prior-access-checks). That review
> could not resolve GitHub from its environment and does not supersede these
> asset, Docker, GPU or Quest limitations. Publication of code and validation of
> runtime prerequisites are separate claims.

Updated 2026-11-11 after rechecking the previous release
`6f713f07dd37127c76ac48520c5ee5f4d383b81a`. **Local CPU preparation is complete;
public deployment is not complete.** GitHub publication, online asset acquisition,
rack redistribution permission and actual GPU/Quest operation remain unverified
or blocked. No original worktree or running simulation was changed/stopped. Both original repositories’ status, refs, remotes and tracked diffs were compared against fresh pre-work snapshots and remain byte-identical.

## Newly executed tests

A separate `git clone --no-local` of code revision
`08cdc4ed8996a7b730e789c0e2a89b4131516666` was used. The clone has its own Git/LFS
storage and no remaining origin dependency on the source. This was a **local
transport clone, not a GitHub download**. Final subsequent changes are documentation
and report updates, not task/control/test implementations.

**41 suites passed (the original 39 plus 2 added suites), 259 test cases,
0 failures, 0 errors, 0 skipped.** Full per-suite results are in
[cpu_tests.json](cpu_tests.json); dependency versions are in
[cpu_environment.json](cpu_environment.json). Private transient logs and generated
synthetic recordings are outside the repository.

Covered: HDF5 lifecycle/labels and reopening, real FFmpeg MP4 encoding/decoding
using synthetic frames, wall-clock duration/conversion, strict <40mm success
boundary including exactly 40mm rejection, heated-ID history, gains/LED contracts,
HUD status integration, loop diagnostics, cooperative shutdown/mock Docker
signals, group selection, fresh recording directories and output path mapping.
These are CPU/mock checks, not actual PhysX/Quest execution.

Fresh V8 execution of clean-clone JavaScript passed 215 HUD logic checks in 12
suites and 13 controller-input checks. Three DOM/canvas HUD suites remain
unexecuted because that runtime has no browser document. No headset, raster or
Meta casting validation is implied. See [hud_tests.json](hud_tests.json).

## The four previously failing suites

All four were re-executed **before modifying their implementations** and failed
again. [prior_failure_reproduction.json](prior_failure_reproduction.json) records
the five failing assertions and hashes of the private reproduction logs.

| Suite | Cause | Repair and verification |
|---|---|---|
| `test_current_toast_delivery.py` | Generation-time source hashes were compared against evolved runtime files | Verify exact path-bound generation source bytes in the immutable archive; validate current settings separately |
| `test_base_toast_delivery.py` | The stored generator fingerprint described the 20mm-era generator | Same separation; current mesh/card/assignment assertions remain, and exact historical generator evidence is verified |
| `test_ptb_toast_delivery.py` | Both generator fingerprint and all-byte regeneration comparison mixed historical 20mm metadata with current 40mm runtime | Rebuild in an isolated tree using hash-verified historical generation code and pinned assets; all nine output files still must match byte-for-byte |
| `test_toast_collection_validation.py` | Collection coverage reused the same incorrect runtime-vs-generation fingerprint assumption | Validate original generation evidence and preserve selection coverage assertions |

No saved manifest/source hash was replaced with today's hash, no assertion was
deleted and no test was skipped. The 32 archived source versions are checked
against the original expected SHA256 and indexed original paths. One pre-35mm
source is reconstructed by the previously recorded inverse migration and matches
the original manifest hash exactly. The archive has no Git-history dependency.
New negative tests reject a corrupt archive, a mismatched source path and wrong
asset bytes; assets never fall back to the source archive.

A separate clean-clone base reproduction also matched all nine historical files byte-for-byte.

Current runtime remains **strict plate-local geometry-center XY distance <0.04m**;
40mm exactly fails. The original 20mm setting remains historical generation
metadata. New recording metadata has separate `generation_contract` and
`runtime_contract` fields, while adjacent manifest bytes and their hashes remain
unchanged. Physics, gains, speeds, VR mapping and success logic were not changed.
The only task-source edit adds an early error for a missing rack USDZ behind an
existing wrapper.

## Scenario preservation and independent clone

- All **240 tracked scenario artifacts** other than explanatory READMEs are
  byte-identical to the previous release. That includes IDs, all poses,
  assignments/order, seeds, geometry/reproduction inputs and diagrams.
- Each of three sets has 100 unique IDs and four subgroups of 25. Base launcher
  dry-runs cover each group at indices 1 and 25; default B_1/index 1 resolves to
  `toast_base_20261109_025`. Host/container run and bridge paths agree.
- Clean clone Git LFS pull/fsck and submodule initialization passed using local
  transport. There are zero gitlinks and no checkout symlinks. Vendored source
  dependencies were not swapped to new upstream versions.
- Clean-clone Compose config mounts only that clone at `/workspace/cyclo_lab`,
  with separate `cyclo-toast-teleop` project/image names. No developer absolute
  path or original working tree is in its effective Compose configuration.
- 406 project Python files parsed; shell syntax and distribution diff whitespace
  checks passed. Host server/installer/converter help and actual shared teleop
  option/practice parsers were checked. README/scenario/release/Quest local links
  resolve. Root README gives separate terminal setup rather than assuming shell
  variables automatically cross terminals.

## Asset acquisition: local evidence versus remote checks

See [asset audit](ASSETS.md), [recursive dependency graph](asset_dependencies.json),
[per-object LFS audit](lfs_audit.json) and [download URLs/results](download_audit.json).

All 66 previously missing LFS blobs were found in the original repository's LFS
store and copied to isolated audit storage after size/SHA256 verification. The
original store was read only. None is needed by the known selected local toast
roots, so 66 remain excluded, zero restored to the distribution, zero unrecovered.
This does not certify the unresolved NVIDIA cloud table graph.

Fresh clean-clone `check_release.py --assets` initially failed correctly for
absent external assets. Real public download attempts failed DNS. To run CPU
integration tests, exact checksum-verified files were then copied from the
existing deployment's ignored asset cache, and the rack was installed through
the checked installer. The resulting clone runs independently of that cache;
this **does not prove new-PC online acquisition or rack permission**.

Rack input/hash/idempotency/wrapper checks and missing/wrong-file refusal pass.
The original 72,165-byte USDZ embeds one USDC and no external meshes/textures.
Redistribution permission is absent, so the required binary is still excluded.
The public wrapper alone cannot load the rack. Obtain the exact file and grant
from its rights holder as described in ASSETS.md; no alternative mesh is used.

RoboDojo's nine pinned URLs, versions/hashes/install locations were rechecked;
all network checks failed DNS. Synthetic downloader tests verify successful
hash-checked publication, verified-cache reuse, network failure, bad checksum,
temporary cleanup and preservation of existing files. Those tests do not establish
remote availability.

Recursive local USD traversal identified packed bread/plate textures and toaster
MDL, plus external Isaac Sim MDL references (`OmniPBR.mdl`, `gltf/pbr.mdl`). These
modules exist in the installed Isaac Sim 5.1 library but renderer loading remains
untested. The packing-table USD could not be downloaded; its exact hash and
recursive materials/mesh closure remain unverified. Local preflight reports this
limitation rather than claiming every runtime dependency is satisfied.

## GPU, GUI, Quest and known issues

Docker client 29.9.2 is present. A fresh isolated Compose build was attempted and
failed because access to the Docker socket was denied. `nvidia-smi` failed to
communicate with the driver. No GPU/GUI simulation, reset, playback or live
container shutdown was run. Configured Isaac Sim 5.1.0/Isaac Lab 2.3.0 are not a
newly validated GPU installation. No headset pairing, physical button operation
or casting crop was verified automatically.

**Ctrl+C leaving Isaac Sim alive and dynamic rack/bread stability remain open.**
Mock signal success does not resolve a native hang. The README describes
read-only inspection of the exact run container, cooperative q/SIGINT requests
and an operator-selected last-resort stop, with possible buffered-data loss.
No recovery action was performed on existing sessions.

## Publication and retry

No repository was created or pushed in this follow-up. Direct Git/HTTP attempts
failed DNS for GitHub; `gh` is absent; global/system Git credential helpers were
not configured; the GitHub integration was checked and is not connected. Actual
GitHub authentication could not be tested. A failed lookup does not prove the
repository is absent. No token/password was printed or requested in chat.

After installing GitHub CLI and restoring network access, use browser login:

```bash
cd /path/to/cyclo_lab_toast
gh auth login --web
bash scripts/tools/publish_release.sh
```

The script inspects an existing repository's visibility, contents, refs and main
history. It allows only a compatible fast-forward to the authorized public target;
a private repository, missing existing main or conflicting history stops for
review. It never force-pushes or changes an unrelated origin. On verified absence
it creates the public repository. It then compares local/remote main and uses a
fresh HTTPS clone with independent LFS storage to verify download/submodules and
CPU preflight. External assets and GPU checks are still separate. None of these
remote success conditions has yet been observed.

## Re-run locally

With the pinned external assets installed and the CPU dependencies available:

```bash
python3 scripts/tools/check_release.py --assets
python3 scripts/tools/run_release_cpu_tests.py --output /tmp/new-toast-cpu-report
python3 scripts/tools/reproduce_toast_generation.py \
  --set scenarios/fixed_ptb --output /tmp/new-ptb-generation
```

Output directories must be new; retain reports outside Git. This validation does
not justify calling the public deployment complete. Another lab still needs the
rack rights/file, online downloads, a working NVIDIA/Docker stack and actual
GPU/Quest acceptance tests before identical operation can be asserted.
