#!/usr/bin/env python3
"""Optional recovery installer for the exact bundled rack USDZ; do not convert geometry.

The versioned rack.usda wrapper supplies the original unit/axis/collision transform.
No replacement mesh, texture download, or permission grant is produced here.
"""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SHA256 = '338eb23d759224c0686857b3e793070b2bf03f9c7fe25f872a3c598bd67330d8'
WRAPPER_SHA256 = 'bf9d759dba0cc619eda5483bfba87db934e2b7ae1c4ac86af833cfaa5323dd52'
DESTINATION = ROOT / 'source/cyclo_lab/data/objects/bread_slot/bread_slot.usdz'


def install(source, target=DESTINATION):
    source, target = Path(source), Path(target)
    if not source.is_file():
        raise ValueError(f'Missing input USDZ: {source}. Restore the tracked file from the intended repository revision.')
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError('Wrong rack SHA256; expected ' + SHA256 + '. Geometry substitutions are not allowed.')
    wrapper = target.with_name('rack.usda')
    if not wrapper.is_file() or hashlib.sha256(wrapper.read_bytes()).hexdigest() != WRAPPER_SHA256:
        raise ValueError('Missing/corrupt rack.usda wrapper. Run git lfs pull and git lfs fsck; no conversion is needed.')
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != SHA256:
            raise ValueError('Refusing to overwrite a different installed rack')
        return 'Rack already verified'
    fd, temporary = tempfile.mkstemp(prefix='.bread-slot-', suffix='.tmp', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        os.link(temporary, target)  # Atomic publication, refuses an existing target.
    finally:
        Path(temporary).unlink(missing_ok=True)
    return 'Installed verified rack; see docs/release/ASSETS.md for the recorded user authorization'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path, help='Exact USDZ supplied with rights-holder permission')
    args = parser.parse_args()
    try:
        print(install(args.file))
    except (OSError, ValueError) as error:
        parser.exit(2, f'Rack installation failed: {error}\n')


if __name__ == '__main__':
    main()
