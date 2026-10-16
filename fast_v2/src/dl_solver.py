"""Preserve visual evidence and solve code/diagrams with one local VLM request."""
from __future__ import annotations
import base64
import hashlib
import io
import json
from pathlib import Path
import time
from PIL import Image, ImageDraw, ImageFont, ImageStat
from .dl_prompt import SYSTEM, answer_values, prompt
from .layout import DomCapture, ManualCapture, group_auto
from .question_parser import infer_selection, parse_question, structured_question
from .ocr import OCR


def nonblank(image):
    if image is None or image.width < 8 or image.height < 8:
        return False
    # Ignore the card frame: a blank answer with a border is still blank.
    w, h = image.size
    inner = image.crop((int(w*.08), int(h*.08), max(int(w*.92), int(w*.08)+1),
                       max(int(h*.92), int(h*.08)+1))).convert('RGB')
    stats = ImageStat.Stat(inner)
    return max(stats.stddev) > 1.5 or min(stats.mean) < 200


def manual_image(crops):
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 20)
    except OSError:
        font = ImageFont.load_default(size=20)
    width = max(c.width for c in crops) + 32
    height = sum(c.height + 42 for c in crops) + 16
    out = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(out)
    top = 12
    for index, crop in enumerate(crops):
        draw.text((16, top), 'Q' if index == 0 else chr(64+index), fill='black', font=font)
        out.paste(crop.convert('RGB'), (16, top+28))
        top += crop.height + 42
    return out


def image_url(image):
    stream = io.BytesIO()
    image.convert('RGB').save(stream, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode('ascii')


class DeepLearningPipeline:
    def __init__(self, solver):
        self.solver = solver
        self.settings = solver.settings
        corpus = json.dumps(solver.index.chunks, sort_keys=True, ensure_ascii=False)
        self.fingerprint = hashlib.sha256((json.dumps(self.settings, sort_keys=True) + corpus).encode()).hexdigest()

    def prepare(self, capture):
        start = time.perf_counter()
        expected = self.settings['expected_options']
        boxes, lines, sections = [], [], []
        source = 'OCR + image'
        manual = isinstance(capture, ManualCapture) or (isinstance(capture, DomCapture) and capture.regions)
        if manual:
            if isinstance(capture, ManualCapture):
                crops = capture.crops
            else:
                left = min(r[0] for r in capture.regions)
                top = min(r[1] for r in capture.regions)
                crops = tuple(capture.screenshot.crop((r[0]-left, r[1]-top, r[2]-left, r[3]-top))
                              for r in capture.regions)
            if len(crops) != expected + 1:
                return {'error': 'Bộ ô chưa đủ; vẽ lại Đề và các phương án.', 'vision': True,
                        'ocr_seconds': 0, 'reread': False}
            bad = ["Đề" if i == 0 else chr(64+i) for i, crop in enumerate(crops) if not nonblank(crop)]
            if bad:
                return {'error': 'Vùng trống: ' + ', '.join(bad) + '. Hãy vẽ lại vùng chụp.',
                        'vision': True, 'ocr_seconds': 0, 'reread': False}
            visual = manual_image(crops)
            for index, crop in enumerate(crops):
                if isinstance(capture, DomCapture) and index < len(capture.sections) and capture.sections[index]:
                    section = '\n'.join(capture.sections[index]).rstrip()
                    source = 'DOM + image'
                else:
                    ocr = self.solver._ocr()
                    rows, found = ocr.read(crop)
                    if hasattr(ocr, 'refine_code'):
                        rows, found, _, _ = ocr.refine_code(crop, rows, found)
                    # The image remains authoritative when Python/code OCR loses a character.
                    section = '\n'.join(rows).rstrip()
                    boxes.extend(found)
                sections.append(section)
            q = structured_question(sections[0], {chr(65+i): sections[i+1] for i in range(expected)}, expected)
            lines = ['Q: '+sections[0]] + [f'{chr(64+i)}: {s}' for i, s in enumerate(sections[1:], 1)]
            layout_method = 'manual_regions'
        else:
            visual = capture.screenshot if isinstance(capture, DomCapture) else capture
            if not nonblank(visual):
                return {'error': 'Ảnh câu hỏi trống; hãy chọn lại vùng.', 'vision': True,
                        'ocr_seconds': 0, 'reread': False}
            if isinstance(capture, DomCapture):
                boxes = list(capture.boxes)
                lines = OCR._lines(boxes)
                source = 'DOM + image'
            else:
                lines, boxes = self.solver._ocr().read(visual)
            layout = group_auto(visual, boxes, expected)
            parsed = parse_question(lines, expected)
            q = layout['question'] if layout and not layout['question'].errors else parsed
            layout_method = layout['method'] if layout else 'image_and_labels'
        digest = hashlib.sha256(str(visual.size).encode() + visual.convert('RGB').tobytes()).hexdigest()
        return {'vision': True, 'visual_image': visual, 'image_hash': digest, 'structured': q,
                'lines': lines, 'boxes': boxes, 'sections': sections, 'capture_source': source,
                'layout_method': layout_method, 'weak_layout': bool(q.errors), 'reread': False,
                'ocr_seconds': round(time.perf_counter()-start, 3), 'validation_error': None}

    def solve_prepared(self, prepared, mode='auto'):
        if prepared.get('error'):
            return {'error': prepared['error'], 'ocr_seconds': prepared.get('ocr_seconds', 0)}
        q = prepared['structured']
        # Do not feed an incomplete OCR option map as if it were complete.
        letters = list('ABCDEFGH'[:self.settings['expected_options']])
        options = {letter: q.options.get(letter, '') for letter in letters}
        multi, count = infer_selection(q.text, mode)
        if mode == 'auto' and not q.text:
            multi = None
        return self.solve(q.text, options, multi, count, prepared['visual_image'],
                          prepared['image_hash'], prepared)

    def solve(self, question, options, multi=False, count=None, image=None, image_hash='', prepared=None):
        start = time.perf_counter()
        letters = sorted(options)
        if (not 2 <= len(letters) <= 8 or letters != list('ABCDEFGH'[:len(letters)]) or
                (count is not None and (type(count) is not int or not 1 <= count <= len(letters)))):
            return {'error': 'Nhãn hoặc số phương án không hợp lệ.'}
        answers = answer_values(letters, multi is not False, count)
        if not answers or (image is None and (not question.strip() or any(not v.strip() for v in options.values()))):
            return {'error': 'Thiếu câu hỏi hoặc phương án.'}
        if image is not None and not image_hash:
            image_hash = hashlib.sha256(str(image.size).encode() + image.convert('RGB').tobytes()).hexdigest()
        key = json.dumps([self.fingerprint, image_hash, question, options, multi, count], sort_keys=True)
        if key in self.solver.cache:
            result = dict(self.solver.cache[key], cached=True, seconds=0, inference_seconds=0, cooling_seconds=0)
            if prepared:
                result['ocr_seconds'] = prepared['ocr_seconds']
                result['total_seconds'] = prepared['ocr_seconds']
            return result
        query = question or '\n'.join((prepared or {}).get('lines', []))
        retrieved = self.solver.index.search(query, options, self.settings.get('top_k', 3))
        excerpts, remaining = [], self.settings.get('context_chars', 4000)
        for item in retrieved:
            if remaining < 100:
                break
            text = item['text'][:remaining]
            excerpts.append(dict(item, text=text))
            remaining -= len(text)
        schema = {'type': 'object', 'properties': {
            'answer': {'type': 'string', 'enum': answers + ['?']},
            'source': {'type': 'integer', 'enum': list(range(len(excerpts)+1))}},
            'required': ['answer', 'source'], 'additionalProperties': False}
        content = [{'type': 'text', 'text': prompt(question, options, excerpts, multi, count)}]
        if image is not None:
            content.append({'type': 'image_url', 'image_url': {'url': image_url(image)}})
        self.solver.last_diagnostic = {'question': question, 'options': options, 'multi': multi,
            'image_hash': image_hash, 'retrieved': excerpts, 'capture_source': (prepared or {}).get('capture_source', 'text')}
        try:
            cooling = self.solver._thermal_gate()
            infer_start = time.perf_counter()
            raw = self.solver.model.chat([{'role': 'system', 'content': SYSTEM},
                                          {'role': 'user', 'content': content}], schema)
            infer_seconds = time.perf_counter()-infer_start
            self.solver.last_inference_end = time.monotonic()
            self.solver.last_diagnostic['model_output'] = raw
            if raw.get('answer') not in answers:
                return {'error': 'Chưa đủ dữ liệu để chọn đáp án; kiểm tra ảnh/ô đã chụp.'}
            ref = raw.get('source')
            if type(ref) is not int or not 0 <= ref <= len(excerpts):
                return {'error': 'Tham chiếu không hợp lệ; không copy đáp án.'}
            matched = 'Suy luận trực tiếp từ câu hỏi/ảnh'
            if ref:
                item = excerpts[ref-1]
                matched = item['source'] + (f' (Slide {item["page"]})' if item.get('page') else ' (code)')
            result = {'best_choice': raw['answer'], 'matched_source': matched,
                'method': 'Local DL vision + course retrieval', 'multi': ',' in raw['answer'], 'cached': False,
                'seconds': round(time.perf_counter()-start, 3), 'inference_seconds': round(infer_seconds, 3),
                'cooling_seconds': round(cooling, 3), 'image_hash': image_hash}
            if prepared:
                result.update({field: prepared.get(field) for field in
                    ('ocr_seconds', 'reread', 'capture_source', 'layout_method', 'weak_layout')})
                result['total_seconds'] = round(result['seconds']+prepared['ocr_seconds'], 3)
            self.solver.cache[key] = result
            self.solver.last_diagnostic['result'] = result
            return result
        except (OSError, ValueError, KeyError, IndexError, RuntimeError) as error:
            return {'error': f'Không có đáp án: {error}'}
