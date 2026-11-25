# Asset reference

See [asset setup](../ASSETS.md) for the installation workflow.

## Four-groove bread rack

`source/cyclo_lab/data/objects/bread_slot/bread_slot.usdz` is included as a regular
Git file (72,165 bytes), with SHA256
`338eb23d759224c0686857b3e793070b2bf03f9c7fe25f872a3c598bd67330d8`.
It contains `bread_slot.usdc` and has no external textures.

The Git LFS wrapper `rack.usda` has SHA256
`bf9d759dba0cc619eda5483bfba87db934e2b7ae1c4ac86af833cfaa5323dd52`.
It applies 0.001 unit scale, +90° X rotation and −0.044148661134794986 m Z
translation, with static triangle collision.

No separate rack installation is required. For incomplete checkouts,
`scripts/tools/install_bread_slot.py` can recover the original bytes from an
exact source file; it rejects mismatched hashes and does not convert geometry.

## External assets

RoboDojo toaster, bread, plate and legacy shelf files are pinned to revision
`63fcc045f2e974902eb7800d29de48004cf86016`. The
[asset manifest](../../source/cyclo_lab/cyclo_lab/manager_based/manipulation/make_toast/asset_manifest.json)
records sizes, SHA256 values and download URLs. The downloader verifies existing
files and checks downloaded bytes before replacing a target. Network or checksum
failure leaves the existing target intact and exits with a retry instruction.
See [source provenance](PROVENANCE.md) for upstream terms.

The packing table uses the configured NVIDIA Isaac Sim cloud asset root.
Its meshes/materials and the Isaac Sim MDL libraries require network access and
a working renderer. `check_release.py --assets` checks local pinned files;
it does not check complete cloud or renderer availability.

To inspect an acquired official table and its dependencies without simulation:

```bash
# Requires a Python environment containing pxr/USD.
python3 scripts/tools/audit_toast_assets.py \
  --table /path/to/official/packing_table.usd --output /tmp/toast-assets.json
```

[asset_dependencies.json](asset_dependencies.json) retains the recorded USD layer
and package dependency inventory. The four vendored dependency snapshots and
their upstream notices are preserved; do not replace them with newer branches
as part of asset installation.
