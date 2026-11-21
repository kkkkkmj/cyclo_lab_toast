"""Acquisition failures must not publish wrong/partial assets or overwrite data."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import install_bread_slot as rack
import download_make_toast_assets as downloader


class RackInstall(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.target = self.directory / 'bread_slot.usdz'
        shutil.copy2(rack.DESTINATION.with_name('rack.usda'), self.directory / 'rack.usda')

    def test_exact_source_install_idempotent_and_wrapper_unchanged(self):
        self.assertTrue(rack.DESTINATION.is_file(), 'Tracked rack USDZ must be present in the checkout')
        before = (self.directory / 'rack.usda').read_bytes()
        rack.install(rack.DESTINATION, self.target)
        self.assertEqual(hashlib.sha256(self.target.read_bytes()).hexdigest(), rack.SHA256)
        self.assertEqual(rack.install(self.target, self.target), 'Rack already verified')
        self.assertEqual(before, (self.directory / 'rack.usda').read_bytes())
        self.assertFalse(list(self.directory.glob('*.tmp')))

    def test_missing_input_has_acquisition_guidance(self):
        with self.assertRaisesRegex(ValueError, 'Missing input USDZ'):
            rack.install(self.directory / 'absent.usdz', self.target)
        self.assertFalse(self.target.exists())

    def test_wrong_input_does_not_publish(self):
        bad = self.directory / 'bad.usdz'; bad.write_bytes(b'not a rack')
        with self.assertRaisesRegex(ValueError, 'Wrong rack SHA256'):
            rack.install(bad, self.target)
        self.assertFalse(self.target.exists())

    def test_missing_wrapper_and_existing_wrong_rack(self):
        self.target.with_name('rack.usda').write_bytes(b'version https://git-lfs.github.com/spec/v1')
        with self.assertRaisesRegex(ValueError, 'wrapper'):
            rack.install(rack.DESTINATION, self.target)
        shutil.copy2(rack.DESTINATION.with_name('rack.usda'), self.target.with_name('rack.usda'))
        self.target.write_bytes(b'existing data')
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            rack.install(rack.DESTINATION, self.target)
        self.assertEqual(self.target.read_bytes(), b'existing data')


class Download(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.destination = Path(self.temp.name)
        self.payload = b'fixture object bytes'
        self.manifest = dict(repository='test/fixture', revision='fixed', files=[dict(
            path='bread/object.usdz', source_path='Assets/bread.usdz',
            size=len(self.payload), sha256=hashlib.sha256(self.payload).hexdigest())])
        self.target = self.destination / 'bread/object.usdz'

    def test_success_and_verified_cache_no_network(self):
        with patch.object(downloader.urllib.request, 'urlopen', return_value=io.BytesIO(self.payload)):
            downloader.download(self.manifest, self.destination)
        self.assertEqual(self.target.read_bytes(), self.payload)
        with patch.object(downloader.urllib.request, 'urlopen', side_effect=AssertionError('unexpected network')):
            downloader.download(self.manifest, self.destination)

    def test_bad_download_preserves_existing_and_removes_temporary(self):
        self.target.parent.mkdir(); self.target.write_bytes(b'prior file')
        with patch.object(downloader.urllib.request, 'urlopen', return_value=io.BytesIO(b'corrupt')):
            with self.assertRaisesRegex(RuntimeError, 'Checksum'):
                downloader.download(self.manifest, self.destination)
        self.assertEqual(self.target.read_bytes(), b'prior file')
        self.assertFalse(list(self.destination.rglob('*.tmp')))

    def test_network_failure_leaves_no_installed_file(self):
        with patch.object(downloader.urllib.request, 'urlopen', side_effect=urllib.error.URLError('offline')):
            with self.assertRaises(urllib.error.URLError):
                downloader.download(self.manifest, self.destination)
        self.assertFalse(self.target.exists())
        self.assertFalse(list(self.destination.rglob('*.tmp')))


if __name__ == '__main__':
    unittest.main()
