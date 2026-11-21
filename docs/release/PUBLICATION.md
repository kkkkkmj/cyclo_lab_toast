# Repository publication history

## Completed repository split — 2026-11-21

The repository split and public upload are complete. The maintainer's GitHub CLI
results confirmed the following:

| Repository | Visibility | Preserved or published revision |
|---|---|---|
| `kkkkkmj/cyclo-toast-teleop-mj` | Private | Original source and history at `197d9926456f6e2ff97a76e20e71391edf25a540` |
| `kkkkkmj/cyclo-toast-teleop` | Public | Documentation update `66baaa37b3300f5f3ce70dd3f68310ee054f6e0a` |

The public upload included the required Git LFS object. The local public branch
and remote `main` matched at publication, and the working tree was clean.
Later documentation commits may advance the public branch beyond this revision.

This file is a historical maintainer reference. Users should follow the
[project installation guide](../../README.md#installation); no repository rename,
visibility change or repository creation is required to use the project.

## Local validation before publication

The CPU release preflight passed (three manifests, four groups of 25 scenarios,
eight launcher boundary plans and Python syntax). The seven asset installer /
synthetic downloader tests passed. The full `--assets` check correctly reported
missing RoboDojo files in the clean copy; ignored caches were not carried over.
The serving-success suite could not run because host Python lacks `torch`.
These outcomes do not supersede earlier validation results. No simulator or
container was started, stopped or otherwise manipulated.

## Scope and earlier access limitations

The preparation environment initially could not resolve GitHub, so remote
operations were completed later from the maintainer's terminal. Those earlier
failures describe that environment at the time, not the current publication
status. The historical [2026-11-11 validation report](VALIDATION.md) retains its
original results.

Local-clone and CPU checks do not establish fresh-PC Docker, GPU, Quest or
renderer operation. A GitHub push and matching remote HEAD are not themselves
a full clean-install acceptance test.
