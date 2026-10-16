"""Read-only, offline check of a standalone V2 profile and local assets."""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'fast_v2'
PACKAGES = ('Pillow', 'rapidocr-onnxruntime', 'onnxruntime', 'numpy', 'PyMuPDF',
            'beautifulsoup4', 'psutil', 'PyQt6', 'keyboard', 'pywin32')


def inspect(profile, check_hash=False):
    settings = json.loads((APP / profile).read_text(encoding='utf-8'))
    result = {'python': sys.executable, 'course': settings.get('course', 'web'),
              'profile': str((APP / profile).resolve()), 'packages': {}, 'files': {}}
    for package in PACKAGES:
        try:
            result['packages'][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result['packages'][package] = 'MISSING'
    expected = {}
    for name in ('artifacts/download-manifest.json', 'artifacts/deep_learning/assets.json'):
        manifest = ROOT / name
        if not manifest.is_file():
            continue
        data = json.loads(manifest.read_text(encoding='utf-8'))
        rows = data.get('models', []) + data.get('inference', {}).get('files', [])
        for item in rows:
            if item.get('sha256'):
                expected[(ROOT / item.get('path', item.get('file'))).resolve()] = item['sha256']
    for key in ('model', 'mmproj', 'server', 'knowledge'):
        if not settings.get(key):
            continue
        path = (APP / settings[key]).resolve()
        row = {'path': str(path), 'exists': path.is_file(),
               'inside_workspace': path.is_relative_to(ROOT),
               'bytes': path.stat().st_size if path.is_file() else 0}
        if check_hash and key in ('model', 'mmproj') and path.is_file():
            with path.open('rb') as source:
                row['sha256'] = hashlib.file_digest(source, 'sha256').hexdigest()
            row['sha256_matches'] = row['sha256'] == expected.get(path)
        result['files'][key] = row
    if importlib.util.find_spec('rapidocr_onnxruntime'):
        import rapidocr_onnxruntime
        ocr = Path(rapidocr_onnxruntime.__file__).parent / 'models'
        result['ocr_models'] = [p.name for p in ocr.glob('*.onnx')]
    else:
        result['ocr_models'] = []
    if result['packages']['psutil'] != 'MISSING':
        import psutil
        result['available_ram_mib'] = round(psutil.virtual_memory().available / 2**20)
        result['enough_ram_to_start'] = result['available_ram_mib'] >= settings.get('min_available_ram_mib', 1536)
    try:
        proc = subprocess.run([str(APP / settings['server']), '--list-devices'],
                              capture_output=True, text=True, timeout=20,
                              creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        result['devices'] = proc.stdout.strip()
        result['runtime_ok'] = proc.returncode == 0
    except (OSError, subprocess.SubprocessError) as error:
        result['runtime_ok'] = False
        result['devices'] = str(error)
    result['ready'] = (all(v != 'MISSING' for v in result['packages'].values())
                       and len(result['ocr_models']) >= 3 and result['runtime_ok']
                       and result.get('enough_ram_to_start', False)
                       and all(v['exists'] and v['inside_workspace']
                               and v.get('sha256_matches', True) for v in result['files'].values()))
    return result


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='settings.json')
    parser.add_argument('--hash', action='store_true')
    args = parser.parse_args()
    result = inspect(args.profile, args.hash)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ready'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
