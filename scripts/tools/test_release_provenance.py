"""Historical evidence integrity and current-runtime metadata must not be confused."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import toast_provenance as provenance
from toast_recording_metadata import create_diagnostic
from generate_current_toast_scenarios import current_contract


class ProvenanceTests(unittest.TestCase):
    def test_every_saved_source_has_exact_path_bound_evidence(self):
        for manifest in provenance.ROOT.glob('scenario_delivery*/manifest.json'):
            for path, digest in json.loads(manifest.read_text())['provenance']['source_sha256'].items():
                self.assertEqual(hashlib.sha256(provenance.generation_source(path, digest)).hexdigest(), digest)
                with self.assertRaises(ValueError):
                    provenance.generation_source('wrong/' + path, digest)

    def test_corrupt_archive_is_rejected(self):
        path = provenance.PREFIX + 'assets.py'
        manifest = json.loads((provenance.ROOT / 'scenario_delivery_base/manifest.json').read_text())
        digest = manifest['provenance']['source_sha256'][path]
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp)
            (archive / 'index.json').write_text(json.dumps({digest: {'path': path}}))
            (archive / (digest + '.source')).write_bytes(b'corrupt evidence')
            with patch.object(provenance, 'ARCHIVE', archive), self.assertRaises(ValueError):
                provenance.generation_source(path, digest)

    def test_runtime_and_historical_radius_are_separate(self):
        manifest = provenance.ROOT / 'scenario_delivery_base_ptb/manifest.json'
        raw = manifest.read_bytes(); data = json.loads(raw)
        self.assertEqual(data['environment_contract']['success_center_radius_m'], .02)
        runtime = provenance.runtime_contract()
        self.assertEqual(runtime['serving_center_xy_radius_m'], .04)
        self.assertEqual(runtime['serving_center_xy_comparison'], 'strict_less_than')
        _, actual = current_contract()
        self.assertEqual(actual['success_center_radius_m'], .04)
        entry = data['scenarios'][0]
        with tempfile.TemporaryDirectory() as tmp:
            directory, meta = create_diagnostic(Path(tmp) / 'run', manifest, entry['operator'], entry['id'], entry['operator_index'])
            self.assertEqual(meta['runtime_contract'], runtime)
            self.assertEqual(meta['generation_contract']['environment_contract'], data['environment_contract'])
            self.assertEqual((directory / 'manifest.json').read_bytes(), raw)
            self.assertEqual(json.loads((directory / 'metadata.json').read_text())['runtime_contract'], runtime)

    def test_asset_fingerprint_never_falls_back_to_source_archive(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(provenance, 'ROOT', Path(tmp)):
            p = Path(tmp) / 'asset.usdz'; p.write_bytes(b'wrong')
            with self.assertRaises(ValueError):
                provenance.verify_fingerprint('asset.usdz', hashlib.sha256(b'expected').hexdigest())


if __name__ == '__main__':
    unittest.main()
