"""Activate a trained profile only after independent local comparison and actual captures."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]


def file_hash(path):
    digest=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(8*2**20),b''): digest.update(block)
    return digest.hexdigest()


def check(base,trained,actual):
    problems=[]
    for name,report in [('base',base),('trained',trained),('actual',actual)]:
        if not report.get('complete') or report.get('limited'): problems.append(f'{name}: incomplete/limited evaluation')
    if base.get('actual_captures') or trained.get('actual_captures'): problems.append('Comparison must use the held-out practice test')
    if base.get('dataset_sha256')!=trained.get('dataset_sha256'): problems.append('Different test sets')
    skip={'model','mmproj','lora'}
    if {k:v for k,v in base.get('settings',{}).items() if k not in skip}!={k:v for k,v in trained.get('settings',{}).items() if k not in skip}:
        problems.append('Different runtime conditions')
    bm,tm=base.get('metrics',{}),trained.get('metrics',{})
    for category in ('overall','code','visual'):
        if category not in bm or category not in tm: problems.append(f'Missing {category} evaluation'); continue
        if tm[category]['accuracy'] < bm[category]['accuracy']: problems.append(f'{category} regressed')
        if tm[category]['accuracy'] < .9: problems.append(f'{category} accuracy below 90%')
        if tm[category]['p95_seconds'] > 5: problems.append(f'{category} P95 exceeds 5 seconds')
    if tm.get('overall',{}).get('n',0)<100: problems.append('Need at least 100 held-out test questions')
    if tm.get('overall',{}).get('accuracy',0)<=bm.get('overall',{}).get('accuracy',1): problems.append('No overall improvement')
    am=actual.get('metrics',{}).get('overall',{})
    if not actual.get('actual_captures') or am.get('n',0)==0 or am.get('accuracy',0)!=1:
        problems.append('Labelled actual captures have not all passed')
    if am.get('p95_seconds',float('inf'))>5: problems.append('Actual captures exceed 5-second P95')
    if actual.get('model_sha256')!=trained.get('model_sha256'): problems.append('Actual captures evaluated on a different model')
    return problems


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','trained','actual','profile'): p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    reports=[json.loads(getattr(args,name).read_text(encoding='utf-8')) for name in ('base','trained','actual')]
    problems=check(*reports)
    if problems: raise RuntimeError('Promotion refused:\n'+'\n'.join(problems))
    profile=json.loads(args.profile.read_text(encoding='utf-8'))
    if profile!=reports[1]['settings']: raise RuntimeError('Profile differs from evaluated configuration')
    for key in ('model','mmproj'):
        path=(ROOT/'fast_v2'/profile[key]).resolve()
        if not path.is_file(): raise FileNotFoundError(path)
        if key=='model' and file_hash(path)!=reports[1]['model_sha256']:
            raise RuntimeError('Model checksum changed after evaluation')
    destination=ROOT/'fast_v2/settings.json'
    backup=ROOT/'backups'/('dl-promote-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True); shutil.copy2(destination,backup/'settings.json')
    temp=destination.with_suffix('.json.tmp'); temp.write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temp,destination)
    print('Activated:',destination,'rollback:',backup/'settings.json')


if __name__=='__main__': main()
