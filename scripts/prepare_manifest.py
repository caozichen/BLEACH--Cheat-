"""Update the source package manifest from Git's non-ignored file list."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--git', default='git', help='Git executable path if it is not in PATH')
    args = parser.parse_args()
    raw = subprocess.check_output([args.git, 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT)
    names = sorted(set(name for name in raw.decode('utf-8').split('\0')
                       if name and name != 'evidence/package-manifest.json'))
    result = []
    for name in names:
        target = ROOT / name
        if not target.is_file():
            raise ValueError(f'Listed file is missing: {name}')
        if target.suffix.lower() in {'.exe', '.dll', '.iso', '.cso', '.msi', '.pem', '.key'}:
            raise ValueError(f'Unexpected application, image or credential file: {name}')
        result.append({'file': name, 'sizeBytes': target.stat().st_size,
                       'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    destination = ROOT / 'evidence/package-manifest.json'
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'files': len(result), 'totalBytes': sum(item['sizeBytes'] for item in result)}, indent=2))


if __name__ == '__main__':
    main()
