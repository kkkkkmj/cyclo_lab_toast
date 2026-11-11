#!/usr/bin/env python3
"""Recursively audit real toast USD dependencies without starting Isaac Sim.

--table is an independently acquired official table USD; without it, the full
runtime closure is explicitly incomplete. NVIDIA MDL resolution needs Isaac Sim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from pxr import UsdUtils

ROOT = Path(__file__).resolve().parents[2]
TABLE_URL = 'https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Props/PackingTable/packing_table.usd'


def audit(table=None):
    base = ROOT / 'source/cyclo_lab/data'
    roots = [base / 'robots/FFW/FFW_BG2_without_mimic.usd',
             *[base / 'objects/robodojo_make_toast' / n / 'object.usdz' for n in ('toaster', 'plate', 'bread')],
             base / 'objects/bread_slot/rack.usda']
    if table is not None:
        roots.append(Path(table).resolve())
    def label(path):
        return str(path).replace(str(ROOT) + '/', '')
    report = dict(schema_version=1, scope='recursive USD asset dependencies; no PhysX or renderer',
                  table=dict(url=TABLE_URL, status='local_USD_audited' if table else 'NOT_ACQUIRED_NOT_RECURSIVELY_VERIFIED'), roots=[])
    for path in roots:
        entry = dict(path=label(path))
        if not path.is_file():
            entry['error'] = 'required root missing'
        else:
            layers, assets, unresolved = UsdUtils.ComputeAllDependencies(str(path.resolve()))
            entry.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         layers=[label(x.identifier) for x in layers],
                         assets=[label(x) for x in assets], unresolved=[label(x) for x in unresolved])
            if path.suffix == '.usdz':
                with zipfile.ZipFile(path) as z:
                    entry['package_members'] = z.namelist()
        report['roots'].append(entry)
    report['complete_runtime_closure_verified'] = bool(table) and all(not x.get('error') and not x.get('unresolved') for x in report['roots'])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--table', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.table)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    if not result['complete_runtime_closure_verified']:
        parser.exit(2, 'Incomplete runtime closure: inspect table/MDL/missing dependencies in the report; no GPU loading is certified.\n')
    print('All recursively enumerated dependencies resolved; GPU loading still unverified')


if __name__ == '__main__':
    main()
