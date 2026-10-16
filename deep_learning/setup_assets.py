"""Explicit online setup; inference and training never download weights implicitly."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request
from download import download

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'models' / 'deep_learning'
MANIFEST = ROOT / 'artifacts' / 'deep_learning' / 'assets.json'
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def api(repo):
    with OPENER.open('https://huggingface.co/api/models/' + repo + '?blobs=true', timeout=45) as response:
        return json.load(response)


def fetch(repo, directory, choose):
    info = api(repo)
    revision = info['sha']
    saved = []
    directory.mkdir(parents=True, exist_ok=True)
    for item in info['siblings']:
        name = item['rfilename']
        if not choose(name):
            continue
        target = directory / name
        url = f'https://huggingface.co/{repo}/resolve/{revision}/{name}'
        lfs = item.get('lfs') or {}
        expected = lfs.get('sha256')
        if expected:
            download(url + '?download=true', target, item['size'], expected)
        else:
            with OPENER.open(url, timeout=90) as response:
                content = response.read()
            if item.get('blobId'):
                blob = b'blob ' + str(len(content)).encode() + b'\0' + content
                if hashlib.sha1(blob).hexdigest() != item['blobId']:
                    raise RuntimeError(f'Git blob checksum mismatch: {name}')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            expected = hashlib.sha256(content).hexdigest()
        saved.append({'path': str(target.relative_to(ROOT)), 'bytes': target.stat().st_size,
                      'sha256': expected, 'url': url})
    if not saved:
        raise RuntimeError(f'No matching assets: {repo}')
    return {'repo': repo, 'revision': revision, 'files': saved}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--training', action='store_true')
    parser.add_argument('--inference', action='store_true')
    args = parser.parse_args()
    previous = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}
    if args.training or not args.inference:
        previous['training'] = fetch('Qwen/Qwen3.5-2B', BASE / 'qwen35-2b-hf',
            lambda n: n.endswith(('.safetensors', '.json', '.jinja', '.txt')) and '/' not in n)
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.inference or not args.training:
        previous['inference'] = fetch('unsloth/Qwen3.5-2B-GGUF', BASE / 'base',
            lambda n: n == 'Qwen3.5-2B-Q4_K_M.gguf' or n == 'mmproj-F16.gguf')
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Verified assets:', MANIFEST, flush=True)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
