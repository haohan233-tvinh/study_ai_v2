"""Build the canonical DL corpus without duplicating root/Slides PDF copies."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import fitz

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COURSE = Path('D:/Study/Vinh/Study/semester 3/Deep Learning')
OUTPUT = ROOT / 'data' / 'deep_learning'


def build(course=DEFAULT_COURSE, output=OUTPUT):
    course, output = Path(course), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    image_dir = output / 'pages'
    image_dir.mkdir(exist_ok=True)
    sources = sorted((course / 'Slides').glob('*.pdf')) + sorted((course / 'Labworks').glob('*.pdf'))
    sources += sorted(course.glob('Exercise*.pdf'))
    result, manifest = {}, []
    for source in sources:
        name = source.relative_to(course).as_posix()
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        pages = []
        with fitz.open(source) as doc:
            for index, page in enumerate(doc):
                text = page.get_text(sort=True).strip()
                image_name = f'{digest[:12]}-{index+1:03}.png'
                image_path = image_dir / image_name
                if not image_path.exists():
                    page.get_pixmap(matrix=fitz.Matrix(960 / page.rect.width, 960 / page.rect.width),
                                    alpha=False).save(image_path)
                pages.append({'page': index + 1, 'content': source.stem + '\n' + text,
                              'native_text': text, 'visual_text': '',
                              'image': 'pages/' + image_name, 'needs_visual_review': len(text) < 80,
                              'width': page.rect.width, 'height': page.rect.height})
        result[name] = {'source': name, 'type': 'lecture_slides' if name.startswith('Slides/') else 'lab',
                        'total_pages': len(pages), 'sha256': digest, 'pages': pages}
        manifest.append({'source': str(source), 'relative_source': name, 'sha256': digest, 'pages': len(pages)})
        print(f'{name}: {len(pages)} pages', flush=True)
    for source in sorted((course / 'Codew').rglob('*.py')):
        name = source.relative_to(course).as_posix()
        text = source.read_text(encoding='utf-8-sig')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        result[name] = {'source': name, 'type': 'code', 'sha256': digest, 'full_text': text}
        manifest.append({'source': str(source), 'relative_source': name, 'sha256': digest})
    if not result:
        raise RuntimeError(f'No canonical DL sources at {course}')
    fingerprint = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    (output / 'course_knowledge.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'source_manifest.json').write_text(json.dumps({'fingerprint': fingerprint, 'sources': manifest},
                                                          ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(sources)} PDFs; {sum(d.get("total_pages", 0) for d in result.values())} pages; fingerprint {fingerprint}', flush=True)
    return result


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--course-dir', type=Path, default=DEFAULT_COURSE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    build(args.course_dir, args.output)
