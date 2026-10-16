"""Merge a completed local LoRA and export Q4_K_M using the pinned local converter."""
from __future__ import annotations
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
ROOT=Path(__file__).resolve().parents[1]
LLAMA_COMMIT='6b790a9c291b5d7af3312bbf9f0c558aa023b13e'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(8*2**20),b''): h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adapter',type=Path,default=ROOT/'artifacts/deep_learning/lora')
    p.add_argument('--base',type=Path,default=ROOT/'models/deep_learning/qwen35-2b-hf')
    p.add_argument('--converter',type=Path,default=ROOT/'runtime/llama-conversion')
    p.add_argument('--output',type=Path,default=ROOT/'models/deep_learning/trained')
    a=p.parse_args()
    result=json.loads((a.adapter/'training_result.json').read_text(encoding='utf-8'))
    recipe=json.loads((a.adapter/'recipe.json').read_text(encoding='utf-8'))
    if not result.get('complete') or result.get('smoke_only'):
        raise RuntimeError('A completed full training run is required for deployment export')
    if not recipe.get('vision_frozen'): raise RuntimeError('Projector reuse requires the frozen vision encoder')
    actual_commit=subprocess.check_output(['git','-C',str(a.converter),'rev-parse','HEAD'],text=True).strip()
    if actual_commit!=LLAMA_COMMIT: raise RuntimeError('Converter must match the installed b11159 runtime')
    converter=a.converter/'convert_hf_to_gguf.py'
    quantizer=ROOT/'runtime/cuda/llama-quantize.exe'
    projector=ROOT/'models/deep_learning/base/mmproj-F16.gguf'
    for path in (converter,quantizer,projector):
        if not path.is_file(): raise FileNotFoundError(path)
    if shutil.disk_usage(ROOT).free<12*2**30: raise RuntimeError('Need 12 GiB free for merge and GGUF intermediates')
    a.output.mkdir(parents=True,exist_ok=True)
    merged=a.output/'merged-hf'
    from transformers import AutoModelForImageTextToText,AutoProcessor
    from peft import PeftModel
    import torch
    base=AutoModelForImageTextToText.from_pretrained(str(a.base),dtype=torch.bfloat16,
        device_map={'':'cpu'},local_files_only=True,low_cpu_mem_usage=True)
    tuned=PeftModel.from_pretrained(base,str(a.adapter),local_files_only=True)
    merged_model=tuned.merge_and_unload(safe_merge=True)
    merged_model.save_pretrained(str(merged),safe_serialization=True,max_shard_size='1GB')
    AutoProcessor.from_pretrained(str(a.base),local_files_only=True).save_pretrained(str(merged))
    del merged_model,tuned,base; gc.collect()
    f16=a.output/'deep-learning-2b-F16.gguf'
    q4=a.output/'deep-learning-2b-Q4_K_M.gguf'
    subprocess.run([sys.executable,str(converter),str(merged),'--outfile',str(f16),'--outtype','f16','--use-temp-file'],check=True)
    subprocess.run([str(quantizer),str(f16),str(q4),'Q4_K_M','2'],check=True,
                   creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    target_projector=a.output/'mmproj-F16.gguf'; shutil.copy2(projector,target_projector)
    profile=json.loads((ROOT/'fast_v2/settings.deep_learning.json').read_text(encoding='utf-8'))
    profile['model']=os.path.relpath(q4,ROOT/'fast_v2').replace('\\','/')
    profile['mmproj']=os.path.relpath(target_projector,ROOT/'fast_v2').replace('\\','/')
    profile_path=ROOT/'fast_v2/settings.deep_learning.trained.json'
    profile_path.write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
    report={'complete':True,'promoted':False,'converter_commit':actual_commit,
            'adapter_sha256':digest(a.adapter/'adapter_model.safetensors'),
            'model_sha256':digest(q4),'projector_sha256':digest(target_projector),
            'profile':str(profile_path),'training_result':result}
    (a.output/'export.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
