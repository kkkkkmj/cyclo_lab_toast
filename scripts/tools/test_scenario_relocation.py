"""Regression checks for the path migration against the retained baseline commit."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from toast_scenario_paths import SCENARIO_PATHS, relocated_path
import toast_provenance
from test_toast_scenario_runtime import m as loader, fixture
from view_make_toast_scenario import build_parser, resolve_selection

ROOT = Path(__file__).resolve().parents[2]
BASELINE = '7fc8b5ebfa33de040f70cb5fa3552044f6e7c787'


class ScenarioRelocation(unittest.TestCase):
    def test_all_original_scenario_data_bytes(self):
        paths = subprocess.check_output(
            ['git', 'ls-tree', '-rz', '--name-only', BASELINE, '--', *SCENARIO_PATHS], cwd=ROOT)
        checked = 0
        for path in paths.decode().split('\0'):
            if not path or Path(path).name == 'README.md':
                continue
            original = subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=ROOT)
            self.assertEqual(relocated_path(ROOT, path).read_bytes(), original, path)
            checked += 1
        self.assertEqual(checked, 240)

    def test_all_sets_selection_and_config_poses(self):
        ids = set()
        for current in SCENARIO_PATHS.values():
            manifest = ROOT / current / 'manifest.json'
            data = loader.load_manifest(manifest)
            self.assertEqual(len(data['scenarios']), 100)
            for entry in data['scenarios']:
                self.assertNotIn(entry['id'], ids)
                ids.add(entry['id'])
                for selection in (
                    ['--scenario_id', entry['id']],
                    ['--scenario_group', entry['scenario_group'], '--group_index', str(entry['group_index'])],
                    ['--operator', entry['operator'], '--scenario_index', str(entry['operator_index'])],
                ):
                    args = build_parser().parse_args(['--scenario_manifest', str(manifest), *selection])
                    self.assertEqual(resolve_selection(args), entry['id'])
                cfg = fixture(data)
                cfg.scenario_manifest = manifest
                loader.apply_scenario(cfg, entry['id'])
                loader.apply_scenario(cfg, entry['id'])  # Reapplying must be idempotent.
                for name, pose in entry['poses'].items():
                    self.assertEqual(getattr(cfg.scene, name).init_state.pos, tuple(pose['position_m']))
                    self.assertEqual(getattr(cfg.scene, name).init_state.rot, tuple(pose['quaternion_wxyz']))
        self.assertEqual(len(ids), 300)

    def test_historical_input_mapping_preserves_hash_validation(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(toast_provenance, 'ROOT', Path(tmp)):
            path = 'scenario_delivery/inputs/evidence.json'
            relocated = relocated_path(tmp, path)
            relocated.parent.mkdir(parents=True)
            relocated.write_bytes(b'original evidence')
            expected = hashlib.sha256(relocated.read_bytes()).hexdigest()
            toast_provenance.verify_fingerprint(path, expected)
            relocated.write_bytes(b'changed evidence')
            with self.assertRaises(ValueError):
                toast_provenance.verify_fingerprint(path, expected)
            self.assertEqual(relocated_path(tmp, 'other/scenario_delivery/manifest.json'),
                             Path(tmp) / 'other/scenario_delivery/manifest.json')
            absolute = Path(tmp) / 'snapshot/manifest.json'
            self.assertEqual(relocated_path(tmp, absolute), absolute)


if __name__ == '__main__':
    unittest.main()
