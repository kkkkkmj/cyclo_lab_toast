# Asset acquisition and rights review

## Four-groove rack: included in the repository

On 2026-11-21, the user explicitly authorized public upload of the exact
`source/cyclo_lab/data/objects/bread_slot/bread_slot.usdz`. It is now tracked as a
regular Git blob, not a Git LFS pointer. Both the existing checkout copy and
`/home/mj/Downloads/bread_slot.usdz` were verified as 72,165 bytes with SHA256
`338eb23d759224c0686857b3e793070b2bf03f9c7fe25f872a3c598bd67330d8`.
The Downloads path is provenance evidence, not an installation dependency.
User authorization is recorded here; no independently verified author, original
source URL or asset license is asserted, and no blanket code license is assigned
to the asset.

The 2026-11-11 validation excluded the binary because authorization was not
recorded then. Those historical results remain in [VALIDATION.md](VALIDATION.md).
This inclusion changes neither those results nor the original geometry.

`rack.usda` remains unchanged, with SHA256
`bf9d759dba0cc619eda5483bfba87db934e2b7ae1c4ac86af833cfaa5323dd52`.
It references `bread_slot.usdz`, applies 0.001 unit scale, +90° X rotation and
−0.044148661134794986 m Z translation, and retains static triangle collision.
The USDZ contains `bread_slot.usdc`; no substitute or regenerated mesh is used.

## Installation and failure behavior

No separate rack acquisition or installation is needed for a current clone.
The wrapper remains in Git LFS. RoboDojo assets still require downloading:

```bash
git lfs pull
git lfs fsck
python3 scripts/tools/download_make_toast_assets.py
python3 scripts/tools/check_release.py --assets
```

A missing/mismatched rack indicates an incomplete or modified checkout; restore
the tracked file from the intended revision. `install_bread_slot.py` remains an
optional recovery tool for older/incomplete checkouts with an exact source file.
It checks the original hash and wrapper and refuses different existing bytes.
It does not convert geometry or grant a license. NVIDIA table/material access,
PC/Docker/GPU setup and Quest networking/HTTPS/PIN pairing remain necessary;
including the rack does not establish a successful build or GPU/Quest execution.

## Formerly missing 66 LFS objects

All 66 original OIDs were found in the original Cyclo Lab's LFS object store,
read without modifying it, copied to an isolated audit cache, and checked for
both exact size and SHA256. **66 recovered in audit storage, 0 unrecovered; 0
restored into the distribution, 66 deliberately excluded as unrelated to toast.**
See [lfs_audit.json](lfs_audit.json) for every path, OID, size, recovery result and
exclusion reason. `missing-lfs.json` retains the original pointer inventory as
historical evidence; it no longer describes recovery availability.

The excluded objects are K1 meshes/motions, SH5 robot geometry, unrelated food-bag
textures, and upstream documentation media. The selected task instantiates
FFW_BG2_without_mimic, packing table, toaster, plate, bread and the four-groove
rack; none of the recovered objects is in the known local USD dependency graph.
These objects are not downloaded by the toast installer. Their recovery is **not
a remote GitHub LFS download test**.

## Runtime dependency closure and online acquisition

[asset_dependencies.json](asset_dependencies.json) records recursive USD layers,
asset paths and USDZ members for the selected BG2 robot, toaster, plate, bread and
rack. The installed RoboDojo objects are exact matches to the pinned manifest.
The toaster carries its MDL files in its package; bread and plate textures are
packaged. The rack has no external textures. Standalone USD leaves `OmniPBR.mdl`
and `gltf/pbr.mdl` unresolved; both were found in the installed Isaac Sim 5.1 MDL
library, but no renderer-load test was possible. They are supplied by Isaac Sim,
not copied from a developer installation into this repository.

The packing table inherits the configured Isaac Sim cloud root. The normal 5.1
URL, confirmed in the installed Isaac Sim 5.1 asset browser configuration, is:

`https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Props/PackingTable/packing_table.usd`

The table could not be acquired because DNS is unavailable. Its referenced
materials/meshes/textures and exact hash therefore **remain unverified**; the full
runtime asset closure is not certified. No fake hash, empty asset or weakened
asset check is used. On a connected machine, Isaac Sim resolves this cloud asset
and its dependencies under NVIDIA's terms. An independently acquired local table
can also be audited without starting a simulator:

```bash
# Requires a Python environment containing pxr/USD.
python3 scripts/tools/audit_toast_assets.py \
  --table /path/to/official/packing_table.usd --output /tmp/toast-assets.json
```

This reports failure if any dependency is unresolved. `check_release.py --assets`
is explicitly a **local pinned-file** check, not a table/cloud/renderer check.

For RoboDojo, [download_audit.json](download_audit.json) lists all nine exact
URLs, pinned revision, sizes, SHA256 values, installation destinations and new
remote checks. All URL checks failed DNS in the historical validation session. The official dataset
source is `RoboDojo-Benchmark/RoboDojo`, revision
`63fcc045f2e974902eb7800d29de48004cf86016`; the retained manifest identifies its
Apache-2.0 dataset-card license. The downloader validates existing files and
checks size and SHA256 before atomically replacing a target. A failed network or
checksum check leaves the old target intact, removes temporary files, exits
nonzero and gives a retry instruction. CPU tests exercise these failure cases;
that does not prove online availability.

The repository has one reachable LFS object (`rack.usda`); actual BG2 robot USDs
are regular Git blobs under retained `.gitattributes` exceptions. The rack USDZ is a regular Git blob; downloaded RoboDojo assets remain ignored. Vendored `third_party` source
trees contain no gitlinks; `.gitmodules` records upstream URLs and submodule
initialization is a no-op. Do not replace those snapshots with current upstream
branches.
