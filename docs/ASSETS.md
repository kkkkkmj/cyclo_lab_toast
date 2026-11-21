# Assets and downloads

| Asset | How it is supplied |
|---|---|
| FFW-BG2 robot | Tracked robot files and retained upstream notices. |
| Four-groove rack | Exact `source/cyclo_lab/data/objects/bread_slot/bread_slot.usdz` is a regular Git file; `rack.usda` is its Git LFS wrapper. No separate rack installation is required. |
| RoboDojo toaster, bread, plate and legacy shelf | Download the pinned files with the script below. Downloaded files remain ignored. |
| NVIDIA packing table and materials | Loaded from the configured Isaac Sim asset cloud and Isaac Sim MDL libraries, under NVIDIA terms. Requires network access and a working renderer. |

From the checkout:

```bash
git lfs pull
git lfs fsck
python3 scripts/tools/download_make_toast_assets.py
python3 scripts/tools/check_release.py --assets
```

The downloader checks size and SHA256 against the [asset manifest](../source/cyclo_lab/cyclo_lab/manager_based/manipulation/make_toast/asset_manifest.json).
It does not download demonstration datasets. Review the upstream RoboDojo terms
linked in [provenance](release/PROVENANCE.md). NVIDIA dependencies are separate;
`--assets` checks local pinned files, not complete cloud/renderer availability.

The rack is included in the repository. Its original author, source and license
have not been independently verified; the repository code license does not
automatically apply to this asset. Source records, upload authorization and
checksums are retained in the [asset audit](release/ASSETS.md).

For older/incomplete checkouts, `scripts/tools/install_bread_slot.py` remains an
optional recovery tool accepting only the original bytes; it is not a normal
installation step. Do not regenerate the wrapper or substitute geometry.

[Documentation index](README.md)
