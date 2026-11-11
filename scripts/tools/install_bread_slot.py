#!/usr/bin/env python3
"""Install an independently authorized rack file without changing its geometry."""
import argparse
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
SHA256 = '338eb23d759224c0686857b3e793070b2bf03f9c7fe25f872a3c598bd67330d8'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path, help='File supplied with permission by its rights holder')
    args = parser.parse_args()
    if hashlib.sha256(args.file.read_bytes()).hexdigest() != SHA256:
        parser.error('Wrong rack bytes; replacement geometry is not interchangeable with saved poses')
    target = ROOT / 'source/cyclo_lab/data/objects/bread_slot/bread_slot.usdz'
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != SHA256:
            parser.error('Refusing to overwrite a different installed rack')
        print('Rack already verified')
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as out, args.file.open('rb') as source:
        shutil.copyfileobj(source, out)
    print('Installed verified rack; permission is supplied separately, not granted by this script')


if __name__ == '__main__':
    main()
