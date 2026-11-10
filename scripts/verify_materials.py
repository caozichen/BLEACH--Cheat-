"""Verify bundled reference sources, RAM snapshots, and package file hashes."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent


def main():
    results = []
    material_files = set()
    package_files = set()
    for manifest in ['materials/ram/manifest.json', 'reference/manifest.json', 'evidence/package-manifest.json']:
        manifest_path = ROOT / manifest
        if not manifest_path.exists():
            raise ValueError(f'Missing manifest: {manifest}')
        for item in json.loads(manifest_path.read_text(encoding='utf-8')):
            filename = item['file']
            if manifest == 'evidence/package-manifest.json':
                package_files.add(filename)
            else:
                material_files.add(filename)
            target = (ROOT / filename).resolve()
            target.relative_to(ROOT)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if digest.lower() != item['sha256'].lower():
                raise ValueError(f'Hash mismatch: {filename}')
            if 'sizeBytes' in item and target.stat().st_size != item['sizeBytes']:
                raise ValueError(f'File size mismatch: {filename}')
            results.append(filename)
    if not material_files.issubset(package_files):
        raise ValueError('Referenced material is absent from package: ' + ', '.join(sorted(material_files - package_files)))
    print(json.dumps({'status': 'passed', 'verifiedEntries': len(results),
                      'uniqueFiles': len(set(results))}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc))
