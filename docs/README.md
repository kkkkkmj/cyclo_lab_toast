# Documentation

Start with the [project README](../README.md) for installation and a first run.

| Guide | Contents |
|---|---|
| [Current publication review](PREPUBLICATION_REVIEW.md) | Rights, provenance, fresh-checkout results and remaining release gates |
| [Live validation procedure](LIVE_VALIDATION.md) | Operator-assisted isolated GUI, Quest, recording and replay checks |
| [Assets](ASSETS.md) | Included files, RoboDojo downloads and NVIDIA dependencies |
| [Task](TASK.md) | Serving v2 cycle, exact success predicates and control settings |
| [Recording](RECORDING.md) | Scenario selection, output structure, timing and replay |
| [Troubleshooting](TROUBLESHOOTING.md) | Quest pairing, missing assets, GUI and shutdown |

## Repository layout

| Folder | Role |
|---|---|
| `source/cyclo_lab/` | Environment/runtime code, robot and rack assets |
| `scripts/` | Launchers, Quest bridge, recording tools, CPU checks and reproduction scripts |
| `docker/` | Image and Compose configuration |
| [`scenarios/`](../scenarios/README.md) | Three fixed scenario sets, assignments and reproduction inputs |
| `third_party/` | Four vendored source snapshots; no submodule initialization needed |
| `docs/toast_quest/` | Scenario relocation metadata |
| `docs/release/` | Provenance, audit data and historical validation evidence |
| `recordings/`, `logs/` | Local generated outputs, ignored by Git |

## Developer references and historical evidence

The [Quest recorder reference](../scripts/quest_diagnostic/RECORDING.md),
[episode outcomes](../scripts/quest_diagnostic/EPISODE_RESULTS.md) and
[diagnostics](../scripts/quest_diagnostic/DIAGNOSTICS.md) describe lower-level behavior.
Scenario READMEs document layout design and reproduction inputs.

[Historical validation](release/VALIDATION.md), [provenance](release/PROVENANCE.md)
and [asset audit](release/ASSETS.md) retain their dated results and limitations.
They are evidence, not the default installation instructions. Release JSON files
and `release/generation_sources/` are consumed by integrity/reproduction checks;
do not translate, regenerate or remove them as documentation cleanup.

The [publication history](release/PUBLICATION.md) records the completed repository
split. It is a maintainer reference, not an installation step.
