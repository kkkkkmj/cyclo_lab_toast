"""Separate immutable generation evidence from the executing task's contract.

Source hashes in saved manifests describe generation time, not the current runtime.
Every archived source must match both the manifest SHA256 and its indexed path.
Assets are never substituted from the archive: installed bytes must match exactly.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = 'source/cyclo_lab/cyclo_lab/manager_based/manipulation/make_toast/config/ffw_bg2/'
ARCHIVE = ROOT / 'docs/release/generation_sources'


def generation_source(path, expected):
    """Return exact generation bytes, or fail; never change the expected hash."""
    index = json.loads((ARCHIVE / 'index.json').read_text())
    entry = index.get(expected)
    if entry is None or entry['path'] != path:
        raise ValueError(f'No path-bound generation source: {path} @ {expected}')
    source = ARCHIVE / (expected + '.source')
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'Corrupt generation source: {path}')
    return raw


def verify_fingerprint(path, expected):
    """Verify original generation evidence, independently of runtime evolution."""
    if path.startswith(('scripts/', 'source/cyclo_lab/cyclo_lab/')):
        generation_source(path, expected)
    else:
        actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Installed asset/input hash mismatch: {path}: {actual} != {expected}')


def runtime_contract():
    """Read the running checkout, not the historical manifest or archived code."""
    path = ROOT / PREFIX / 'assets.py'
    tree = ast.parse(path.read_text())
    radius = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'SERVING_BREAD_CENTER_RADIUS' for t in n.targets))
    return dict(schema_version=1, scope='executing_checkout_not_generation_metadata',
                serving_center_xy_radius_m=radius, serving_center_xy_comparison='strict_less_than',
                source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((ROOT / PREFIX).glob('*.py'))})
