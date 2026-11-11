# Asset acquisition and rights review

## Four-groove rack: publication remains blocked by missing permission

The excluded file is `source/cyclo_lab/data/objects/bread_slot/bread_slot.usdz`.
Its source record identifies `/home/mj/Downloads/bread_slot.usdz` (a provenance
fact, never an installation dependency). The original and the local validation
copy are 72,165 bytes and SHA256
`338eb23d759224c0686857b3e793070b2bf03f9c7fe25f872a3c598bd67330d8`.
The archive contains exactly one member, `bread_slot.usdc`. USD traversal found
no external mesh or texture references. Layer custom data, documentation and
comment fields contain no author, license or redistribution grant. No associated
rights-holder notice or public source URL was found. Local existence, Git history
and a web search with no results are not permission evidence.

`rack.usda` is **a reference wrapper, not a converted replacement mesh**. Its SHA256
is `bf9d759dba0cc619eda5483bfba87db934e2b7ae1c4ac86af833cfaa5323dd52`.
It references `bread_slot.usdz`, applies 0.001 unit scale, +90° X rotation, and
−0.044148661134794986 m Z translation, and enables the existing static triangle
collision. These settings are unchanged. The geometry remains in the excluded
USDZ. `build_bread_slot_asset.py` is the historical wrapper builder, not a required
installation step; installation must not regenerate or replace geometry.

Ask the rights holder to identify the author/original source and provide written
permission or an applicable license covering:

- Public redistribution of the exact USDZ/embedded USDC in
  `kkkkkmj/cyclo-toast-teleop`, including GitHub downloads and Git LFS storage.
- Use with the provided transformed/collision-enabled USDA wrapper, and
  redistribution of that wrapper and any derivative geometry if applicable.
- Research simulation use, copying by other laboratories, and any limitations on
  modification, commercial use, attribution or sharing derived assets.
- The exact required copyright notice and license text. Identify the grant by
  filename **and the SHA256 above**, not an unrelated bread-rack model.

Until that evidence is supplied, the binary remains ignored/excluded. No other
rack is substituted. A clone alone cannot run the identical environment.

## Installation and failure behavior

After independently obtaining the authorized exact file:

```bash
git lfs pull
git lfs fsck
python3 scripts/tools/install_bread_slot.py /path/to/authorized/bread_slot.usdz
python3 scripts/tools/check_release.py --assets
```

The input is the original USDZ, not `rack.usda`, an extracted USDC or a renamed
archive. The installer verifies both the input SHA256 and the versioned wrapper,
then publishes the bytes atomically at
`source/cyclo_lab/data/objects/bread_slot/bread_slot.usdz`. No conversion, network
download or license grant happens. Reinstalling identical bytes is harmless;
wrong input, missing input, missing/corrupt wrapper or a different existing output
fails with an actionable message. It never overwrites a different installed rack.
The environment resolver now detects a missing USDZ behind an existing wrapper
and points to this procedure before requesting asset loading.

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
remote checks. All URL checks failed DNS in this session. The official dataset
source is `RoboDojo-Benchmark/RoboDojo`, revision
`63fcc045f2e974902eb7800d29de48004cf86016`; the retained manifest identifies its
Apache-2.0 dataset-card license. The downloader validates existing files and
checks size and SHA256 before atomically replacing a target. A failed network or
checksum check leaves the old target intact, removes temporary files, exits
nonzero and gives a retry instruction. CPU tests exercise these failure cases;
that does not prove online availability.

The repository has one reachable LFS object (`rack.usda`); actual BG2 robot USDs
are regular Git blobs under retained `.gitattributes` exceptions. The ignored
external USDZ files are never added by `git add .`. Vendored `third_party` source
trees contain no gitlinks; `.gitmodules` records upstream URLs and submodule
initialization is a no-op. Do not replace those snapshots with current upstream
branches.
