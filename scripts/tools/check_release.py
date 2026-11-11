#!/usr/bin/env python3
"""CPU-only release inventory and selection checks; use --assets before simulation."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
GROUPS = ['operator_A_1', 'operator_A_2', 'operator_B_1', 'operator_B_2']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', action='store_true')
    args = parser.parse_args()
    evidence = json.loads((ROOT / 'docs/release/integrity.json').read_text())
    for name in ('scenario_delivery', 'scenario_delivery_base', 'scenario_delivery_base_ptb'):
        manifest = ROOT / name / 'manifest.json'
        assert hashlib.sha256(manifest.read_bytes()).hexdigest() == evidence[name]['manifest_sha256'], name
        entries = json.loads(manifest.read_text())['scenarios']
        assert len(entries) == len({e['id'] for e in entries}) == 100
        assert Counter(e['scenario_group'] for e in entries) == dict.fromkeys(GROUPS, 25)
    for group in GROUPS:
        for index in (1, 25):
            plan = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/record_quest_base.py'),
                '--group', group, '--index', str(index), '--dry-run'], cwd=ROOT))
            assert plan['host_root'] == str(ROOT)
            assert plan['container_bridge'] == '/workspace/cyclo_lab/logs/quest_toast_recording'
            assert plan['host_bridge'] == str(ROOT / 'logs/quest_toast_recording')
            assert plan['container_run'] == str(Path('/workspace/cyclo_lab') / Path(plan['host_run']).relative_to(ROOT))
    for folder in ('scripts', 'source'):
        for file in (ROOT / folder).rglob('*.py'):
            ast.parse(file.read_text())
    if args.assets:
        manifest = json.loads((ROOT / 'source/cyclo_lab/cyclo_lab/manager_based/manipulation/make_toast/asset_manifest.json').read_text())
        base = ROOT / 'source/cyclo_lab/data/objects'
        for entry in manifest['files']:
            path = base / 'robodojo_make_toast' / entry['path']
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                parser.error('Missing/mismatched RoboDojo asset; run scripts/tools/download_make_toast_assets.py: ' + entry['path'])
        from install_bread_slot import SHA256, WRAPPER_SHA256
        rack = base / 'bread_slot/bread_slot.usdz'
        if not rack.is_file() or hashlib.sha256(rack.read_bytes()).hexdigest() != SHA256:
            parser.error('Obtain authorized rack and run scripts/tools/install_bread_slot.py; see README')
        wrapper = rack.with_name('rack.usda')
        if not wrapper.is_file() or hashlib.sha256(wrapper.read_bytes()).hexdigest() != WRAPPER_SHA256:
            parser.error('Missing/mismatched rack.usda: run git lfs pull and git lfs fsck')
        print('Local asset hashes verified; NVIDIA cloud materials and GPU loading remain unverified')
    print('PASS: three manifests, four groups x 25, eight launcher boundary plans, Python syntax')


if __name__ == '__main__':
    main()
