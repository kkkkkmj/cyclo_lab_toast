#!/usr/bin/env python3
"""Run the 39 original release suites plus release-specific regression suites.

Requires installed checksum-pinned local assets and a CPU Python environment with
numpy/scipy/torch/USD/Shapely/h5py/Pillow/imageio-ffmpeg. No GPU or Quest is tested.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New report directory outside the checkout')
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination == ROOT or ROOT in destination.parents:
        parser.error('Keep transient test logs outside the checkout')
    destination.mkdir(parents=True, exist_ok=False)
    paths = {row['test'] for row in json.loads((ROOT / 'docs/release/cpu_tests.json').read_text())}
    paths.update(('scripts/tools/test_release_provenance.py', 'scripts/tools/test_release_assets.py'))
    results = []
    for name in sorted(paths):
        start = time.monotonic()
        try:
            p = subprocess.run([sys.executable, name], cwd=ROOT, capture_output=True, text=True, timeout=240)
            output, code = p.stdout + p.stderr, p.returncode
        except subprocess.TimeoutExpired:
            output, code = 'Test process exceeded 240 seconds; incomplete result', 124
        (destination / (Path(name).stem + '.log')).write_text(output)
        count = re.search(r'Ran (\d+) tests?', output)
        skipped = re.search(r'skipped=(\d+)', output)
        failures = re.search(r'failures=(\d+)', output)
        errors = re.search(r'errors=(\d+)', output)
        row = dict(test=name, exit_code=code, test_count=int(count[1]) if count else None,
                   skipped=int(skipped[1]) if skipped else 0,
                   failures=int(failures[1]) if failures else 0,
                   errors=int(errors[1]) if errors else 0, seconds=round(time.monotonic() - start, 2))
        results.append(row)
        print(json.dumps(row), flush=True)
    versions = {'python': sys.version.split()[0]}
    for name in ('numpy', 'scipy', 'torch', 'usd-core', 'shapely', 'h5py', 'Pillow', 'imageio-ffmpeg'):
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name] = 'distribution metadata unavailable'
    (destination / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    (destination / 'environment.json').write_text(json.dumps(versions, indent=2) + '\n')
    return int(any(row['exit_code'] for row in results))


if __name__ == '__main__':
    sys.exit(main())
