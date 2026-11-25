"""Resolve historical evidence paths without rewriting saved provenance."""
from pathlib import Path

SCENARIO_PATHS = {
    'scenario_delivery': 'scenarios/mixed',
    'scenario_delivery_base': 'scenarios/fixed_tpb',
    'scenario_delivery_base_ptb': 'scenarios/fixed_ptb',
}


def relocated_path(root, path):
    """Map only a repository-relative legacy scenario prefix, preserving suffixes."""
    path = Path(path)
    if not path.is_absolute() and path.parts and path.parts[0] in SCENARIO_PATHS:
        path = Path(SCENARIO_PATHS[path.parts[0]]).joinpath(*path.parts[1:])
    return Path(root) / path
