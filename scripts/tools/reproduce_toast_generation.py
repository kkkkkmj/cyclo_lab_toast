#!/usr/bin/env python3
"""Rebuild fixed PTB/base generation using verified, archived generation sources.

Uses this checkout's checksum-verified external assets. Does not run a simulator,
change runtime settings, or read a developer checkout/Git object store.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from toast_provenance import ROOT, generation_source, verify_fingerprint

SETS = {'scenario_delivery_base': 'generate_base_toast_scenarios.py',
        'scenario_delivery_base_ptb': 'generate_ptb_toast_scenarios.py'}


def reproduce(name, output):
    if name not in SETS:
        raise ValueError('Only the fixed base/PTB historical generators are supported')
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be a NEW empty directory')
    manifest = json.loads((ROOT / name / 'manifest.json').read_text())
    # Check every original source and actual asset before executing archived code.
    for kind in ('source_sha256', 'asset_sha256'):
        for path, digest in manifest['provenance'][kind].items():
            verify_fingerprint(path, digest)
    with tempfile.TemporaryDirectory(prefix='toast-generation-') as tmp:
        work = Path(tmp)
        for folder in ('scripts/tools', 'source/cyclo_lab/cyclo_lab'):
            shutil.copytree(ROOT / folder, work / folder,
                            ignore=shutil.ignore_patterns('__pycache__', 'test_*'))
        for folder in ('scenario_delivery', 'scenario_delivery_base', 'scenario_delivery_base_ptb'):
            shutil.copytree(ROOT / folder, work / folder, ignore=shutil.ignore_patterns('images', '__pycache__'))
        for path, digest in manifest['provenance']['source_sha256'].items():
            target = work / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(generation_source(path, digest))
        for path in manifest['provenance']['asset_sha256']:
            target = work / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, target)
        # Verify the copied inputs again, including the fully composed rack's USDZ.
        for kind in ('source_sha256', 'asset_sha256'):
            import hashlib
            for path, digest in manifest['provenance'][kind].items():
                if hashlib.sha256((work / path).read_bytes()).hexdigest() != digest:
                    raise ValueError('Historical workspace mismatch: ' + path)
        subprocess.run([sys.executable, str(work / 'scripts/tools' / SETS[name]), '--output', str(output)],
                       cwd=work, check=True, stdout=subprocess.DEVNULL)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--set', choices=SETS, default='scenario_delivery_base_ptb')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reproduce(args.set, args.output)
    print('Historical generation complete; compare outputs with the original set')


if __name__ == '__main__':
    main()
