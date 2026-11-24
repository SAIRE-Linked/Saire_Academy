"""Guarded source-only upgrade. Default is a read-only compatibility check."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import uuid
from zipfile import ZipFile, ZIP_DEFLATED


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def within(root, relative):
    name = PurePosixPath(relative)
    if name.is_absolute() or '..' in name.parts or '\\' in relative or ':' in relative:
        raise ValueError('Unsafe package path: ' + relative)
    target = root.joinpath(*name.parts)
    if not target.resolve().is_relative_to(root):
        raise ValueError('Path resolves outside the project: ' + relative)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_root', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='Check only (the default)')
    mode.add_argument('--apply', action='store_true', help='Back up affected files, then apply after all checks pass')
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    if not (root/'package.json').is_file() or not (root/'backend/manage.py').is_file():
        parser.error('Choose the Academy project root containing package.json and backend/manage.py.')
    package = Path(__file__).resolve().parent
    payload = (package/'files').resolve(strict=True)
    manifest = json.loads((package/'manifest.json').read_text(encoding='utf-8'))
    pending = []
    conflicts = []
    for row in manifest['changes']:
        target = within(root, row['path'])
        source = within(payload, row['path'])
        if not source.is_file() or digest(source) != row['after']:
            raise ValueError('Package file failed checksum: ' + row['path'])
        if target.exists() and not target.is_file():
            conflicts.append(row['path'] + ' is not a file'); continue
        actual = digest(target) if target.exists() else None
        if actual == row['after']:
            continue
        if actual != row['before']:
            conflicts.append(row['path']); continue
        pending.append((row['path'], source, target))
    if conflicts:
        print('No files changed. Review/merge these local differences first:')
        for conflict in conflicts:
            print(' - ' + conflict)
        return 2
    print(f'Compatible: {len(pending)} files to apply; {len(manifest["changes"])-len(pending)} already match.')
    if not args.apply or not pending:
        print('Check complete. Use --apply only after reviewing the upgrade guide and backing up your database/private media.')
        return 0
    backup_dir = within(root, '.saire-v1062-upgrade-backups')
    backup_dir.mkdir(exist_ok=True)
    label = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    backup = backup_dir/(label+'.zip')
    with ZipFile(backup, 'w', ZIP_DEFLATED) as z:
        for name, _, target in pending:
            if target.exists():
                z.write(target, name)
        z.writestr('upgrade-manifest.json', json.dumps(manifest, indent=2))
    staged = []
    try:
        # Stage every replacement before changing any existing file.
        for _, source, target in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Keep staging names short for Windows projects in deep folders.
            temporary = target.with_name('.v1062-' + uuid.uuid4().hex[:12] + '.tmp')
            temporary.write_bytes(source.read_bytes())
            staged.append((temporary, target))
        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _ in staged:
            if temporary.exists():
                temporary.unlink()
    print(f'Applied {len(pending)} source files. Previous affected files: {backup}')
    print('Next: follow docs/EXISTING_ACCOUNT_GOOGLE_CONNECTION.md and restart Django. No migration, reseeding or frontend rebuild is needed.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        sys.exit('Upgrade stopped: ' + str(exc))
