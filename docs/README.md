# Documentation

Start with the [project README](../README.md) for installation and a first run.

| Guide | Contents |
|---|---|
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
| `docs/release/` | Source provenance, asset references and reproduction inputs |
| `recordings/`, `logs/` | Local generated outputs, ignored by Git |

## Technical references

The [Quest recorder reference](../scripts/quest_diagnostic/RECORDING.md),
[episode outcomes](../scripts/quest_diagnostic/EPISODE_RESULTS.md) and
[diagnostics](../scripts/quest_diagnostic/DIAGNOSTICS.md) describe lower-level behavior.
Scenario READMEs document layout design and reproduction inputs.

[Source provenance](release/PROVENANCE.md) and [asset references](release/ASSETS.md)
describe inherited components and pinned assets. Release JSON files and
`release/generation_sources/` preserve source fingerprints and reproduction inputs.
