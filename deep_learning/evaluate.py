"""Measure local warmed inference; acceptance captures stay outside training."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'fast_v2'))
from clipboard_solver import ExamSolver


def percentile(values,p):
    return sorted(values)[max(0,math.ceil(len(values)*p)-1)] if values else None


def metrics(results):
    groups={}
    for row in results:
        for category in {'overall',row['category'], 'visual' if row['image'] else 'text'}:
            groups.setdefault(category,[]).append(row)
    return {name:{'n':len(rows),'accuracy':sum(r['correct'] for r in rows)/len(rows),
                  'p50_seconds':statistics.median(r['key_to_answer_seconds'] for r in rows),
                  'p95_seconds':percentile([r['key_to_answer_seconds'] for r in rows],.95),
                  'errors':sum(bool(r['error']) for r in rows)} for name,rows in groups.items()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings',type=Path,default=ROOT/'fast_v2/settings.deep_learning.json')
    parser.add_argument('--dataset',type=Path,default=ROOT/'data/deep_learning/test.jsonl')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=0)
    parser.add_argument('--actual-captures',action='store_true')
    args=parser.parse_args()
    rows=[json.loads(line) for line in args.dataset.read_text(encoding='utf-8').splitlines() if line.strip()]
    if args.actual_captures and (not rows or any(r.get('origin')!='actual_capture' or not r.get('image') for r in rows)):
        raise ValueError('Acceptance requires labelled actual_capture images')
    if args.limit: rows=rows[:args.limit]
    settings=json.loads(args.settings.read_text(encoding='utf-8'))
    if settings.get('course')!='deep_learning': raise ValueError('A Deep Learning profile is required')
    solver=ExamSolver(settings=settings); results=[]
    try:
        started=time.perf_counter(); solver.warmup(); warm_seconds=time.perf_counter()-started
        for row in rows:
            solver.settings['expected_options']=len(row['options'])
            prepared=None
            if row.get('image'):
                with Image.open(ROOT/row['image']) as image:
                    prepared=solver.prepare_image(image.convert('RGB'))
            # Prepared OCR mirrors the old prefetch mechanism. Cache is cleared for every question.
            solver.cache.clear(); started=time.perf_counter()
            mode='multi' if row.get('multi') else 'single'
            result=solver.solve_prepared(prepared,mode) if prepared else solver.solve(row['question'],row['options'],row.get('multi',False),row.get('count'))
            seconds=time.perf_counter()-started
            item={'id':row['id'],'group_id':row['group_id'],'category':row.get('category','unknown'),
                  'image':bool(row.get('image')),'expected':row['answer'],'predicted':result.get('best_choice'),
                  'correct':result.get('best_choice')==row['answer'],'error':result.get('error'),
                  'key_to_answer_seconds':seconds,'prefetch_seconds':prepared.get('ocr_seconds',0) if prepared else 0,
                  'result':result}
            results.append(item)
            print(f'{len(results)}/{len(rows)} {item["id"]} {item["predicted"]} expected={item["expected"]} {seconds:.2f}s',flush=True)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.with_suffix('.partial.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        model=ROOT/'fast_v2'/settings['model']
        sha=hashlib.sha256()
        with model.open('rb') as file:
            for block in iter(lambda:file.read(8*2**20),b''): sha.update(block)
        report={'complete':True,'actual_captures':args.actual_captures,'dataset_sha256':hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
                'limited':bool(args.limit),'model_sha256':sha.hexdigest(),'settings':settings,
                'warm_seconds':warm_seconds,'metrics':metrics(results),'results':results,
                'criteria':{'accuracy':.90,'p95_seconds':5,'actual_capture_accuracy':1.0}}
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report['metrics'],indent=2))
    finally: solver.close()


if __name__=='__main__': main()
