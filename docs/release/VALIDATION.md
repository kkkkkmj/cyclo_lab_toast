# Release validation

Prepared on 2026-11-11. This file describes distribution checks, not a claim of production readiness.

## Scope

The source working tree, including uncommitted functionality, was copied without importing historical Git objects. Original LICENSE files match the direct baseline byte-for-byte. Scenario data/reproduction inputs/images match the source bytes; all three sets have 100 unique IDs and 25 assignments per subgroup. See `integrity.json` for manifest hashes and eight base-launcher plans (each group at indices 1 and 25). Python syntax and shell syntax checks pass. Docker Compose config resolves a checkout-relative host mount to `/workspace/cyclo_lab`, with separate project/image names.

CPU tests run using a separately available Python 3.12 environment with NumPy, SciPy, PyTorch, USD, h5py, Pillow and imageio-ffmpeg. These packages are test tools, not a runtime dependency on a personal directory. CPU tests used checksum-verified ignored external object/rack files; those files are not distributed. Recording tests use real HDF5 and FFmpeg with synthetic observations, not a GPU simulation.

## Limitations that remain open

- Ctrl+C leaving Isaac Sim alive has recurred in actual use. Mock Docker/Python signal tests only validate signal routing and cooperative cleanup. No actual Isaac Sim exit was tested or fixed here.
- Rack/bread dynamic settling, collision stability, robot manipulation feasibility, actual Quest pairing/control, headset HUD readability, casting crop, GPU rendering/performance, and playback remain unverified.
- Docker client 29.9.2 was present, but Docker socket access was denied. No image build, daemon version verification, or GPU session was attempted after that denial. No existing simulation was stopped.
- The current code differs from generation-time hashes in stored scenario provenance (including `assets.py` and `generate_current_toast_scenarios.py`). Legacy generation-fingerprint assertions can fail even though all saved IDs, assignments, poses and seeds are unchanged. Those hashes and task settings were not rewritten to force tests green.
- The rack has no documented redistribution permission and must be acquired independently. A clean clone without external assets is expected to fail `check_release.py --assets` with an acquisition instruction.
- GitHub DNS is unavailable from the shell, `gh` is absent, and the alternative GitHub integration was not connected during preparation. A failed web lookup does not establish that the requested repository is absent. No remote creation or push is claimed.
- A local clean-clone/LFS check does not prove remote GitHub LFS availability. Publication verification must use an independent GitHub clone.

## Recheck

```bash
python3 scripts/tools/check_release.py
python3 scripts/tools/check_release.py --assets
# Use a CPU Python environment with the dependencies listed above.
python3 scripts/tools/test_record_quest_base.py
python3 scripts/tools/test_graceful_shutdown.py
python3 scripts/tools/test_toast_serving_success.py
python3 scripts/tools/test_toaster_led.py
python3 scripts/quest_diagnostic/test_recording_session.py
python3 scripts/quest_diagnostic/test_wallclock_video.py
python3 scripts/quest_diagnostic/test_loop_diagnostics.py
```

The machine-readable test outcomes are recorded in `cpu_tests.json`. Transient test logs and generated synthetic recordings are kept outside the repository.

## Publish retry

After GitHub CLI installation, authentication and network access are available:

```bash
gh auth login
bash scripts/tools/publish_release.sh
```

This script checks for an existing repository and stops for inspection if one exists; it does not overwrite it, change its visibility, or force-push. On a verified 404 it creates the public repository, pushes main/LFS, compares the remote commit and downloads LFS into an independent clone. If creation succeeds but a later step fails, inspect that existing repository before any further push; rerunning deliberately stops at the existence check.
