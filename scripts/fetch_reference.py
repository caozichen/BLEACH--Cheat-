"""Download pinned PPSSPP source references, preserving HTTPS certificate checks."""
import argparse
import hashlib
import json
from pathlib import Path
import ssl
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    'CwCheat-1.19.3.cpp': 'Core/CwCheat.cpp',
    'MemorySubscriber-1.19.3.cpp': 'Core/Debugger/WebSocket/MemorySubscriber.cpp',
    'GameSubscriber-1.19.3.cpp': 'Core/Debugger/WebSocket/GameSubscriber.cpp',
    'MemMap-1.19.3.cpp': 'Core/MemMap.cpp',
    'LICENSE.TXT': 'LICENSE.TXT',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proxy', help='Optional proxy URL, e.g. http://127.0.0.1:7890')
    parser.add_argument('--ca-file', help='Optional trusted PEM CA bundle')
    args = parser.parse_args()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({'https': args.proxy} if args.proxy else None),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=args.ca_file)))
    target = ROOT / 'reference/ppsspp-v1.19.3'
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / 'reference/manifest.json'
    pinned = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else []
    hashes = {item['file']: item['sha256'] for item in pinned}
    result = []
    for name, upstream in FILES.items():
        url = 'https://raw.githubusercontent.com/hrydgard/ppsspp/v1.19.3/' + upstream
        request = urllib.request.Request(url, headers={'User-Agent': 'BLEACH-Cheat-reference-fetch'})
        with opener.open(request, timeout=30) as response:
            data = response.read()
        digest = hashlib.sha256(data).hexdigest()
        relative = 'reference/ppsspp-v1.19.3/' + name
        if relative in hashes and digest != hashes[relative]:
            raise ValueError(f'Upstream source hash differs from the pinned version: {name}')
        existing = target / name
        if existing.exists() and hashlib.sha256(existing.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Local file differs from upstream; refused to overwrite: {name}')
        existing.write_bytes(data)
        result.append({'file': relative, 'url': url, 'sha256': digest})
    manifest_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
