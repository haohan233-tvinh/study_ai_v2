"""Offline BF16 LoRA, frozen vision encoder, assistant-only loss, complete samples."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'fast_v2'))
from src.dl_prompt import SYSTEM


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def temperature():
    try:
        value = subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu','--format=csv,noheader,nounits'],
            text=True,timeout=3,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        return float(value.splitlines()[0])
    except (OSError,ValueError,subprocess.SubprocessError):
        return None


class Samples:
    def __init__(self, data): self.data = data
    def __len__(self): return len(self.data)
    def __getitem__(self, index): return self.data[index]


class CompletionCollator:
    def __init__(self, processor, context, image_pixels):
        self.processor, self.context, self.image_pixels = processor,context,image_pixels

    def __call__(self, batch):
        if len(batch) != 1: raise ValueError('This low-VRAM recipe requires batch_size=1')
        from PIL import Image
        row = batch[0]
        user = [{'type':'text','text':row['prompt']}]
        if row.get('image'):
            with Image.open(ROOT/row['image']) as raw:
                image = raw.convert('RGB')
            scale = min(1, math.sqrt(self.image_pixels/(image.width*image.height)))
            if scale < 1:
                image = image.resize((max(32,int(image.width*scale)),max(32,int(image.height*scale))),Image.Resampling.LANCZOS)
            user.append({'type':'image','image':image})
        messages = [{'role':'system','content':SYSTEM}, {'role':'user','content':user}]
        prefix = self.processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,
            return_dict=True,return_tensors='pt',enable_thinking=False)
        full = self.processor.apply_chat_template(messages+[{'role':'assistant','content':row['target']}],
            tokenize=True,add_generation_prompt=False,return_dict=True,return_tensors='pt',enable_thinking=False)
        length = full['input_ids'].shape[1]
        if length > self.context:
            raise ValueError(f'{row["id"]}: {length} tokens exceed {self.context}; sample was NOT truncated')
        prefix_length = prefix['input_ids'].shape[1]
        import torch
        if not torch.equal(full['input_ids'][:,:prefix_length], prefix['input_ids']):
            raise ValueError('Chat-template assistant prefix differs; refusing an incorrect loss mask')
        labels = full['input_ids'].clone(); labels[:,:prefix_length] = -100
        if not (labels != -100).any(): raise ValueError('No supervised assistant tokens')
        full['labels'] = labels
        return full


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=['unsloth','transformers'],default='unsloth')
    parser.add_argument('--model',type=Path,default=ROOT/'models/deep_learning/qwen35-2b-hf')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/deep_learning/lora')
    parser.add_argument('--context',type=int,choices=[1024,1536],default=1536)
    parser.add_argument('--image-pixels',type=int,default=262144)
    parser.add_argument('--max-steps',type=int,default=-1,help='20 for a smoke run; -1 for two epochs')
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--preflight-only',action='store_true')
    args = parser.parse_args()
    import torch
    if not torch.cuda.is_available(): raise RuntimeError('CUDA Torch is required; CPU-only training is not this recipe')
    if not torch.cuda.is_bf16_supported(): raise RuntimeError('GPU must support BF16')
    if not list(args.model.glob('*.safetensors')): raise RuntimeError('Verified local HF weights are missing. Run setup_assets.py --training')
    args.output.mkdir(parents=True,exist_ok=True)
    if args.backend == 'unsloth':
        from unsloth import FastVisionModel
        model, processor = FastVisionModel.from_pretrained(model_name=str(args.model),
            load_in_4bit=False,dtype=torch.bfloat16,use_gradient_checkpointing='unsloth',max_seq_length=args.context)
        model = FastVisionModel.get_peft_model(model, fine_tune_vision_layers=False,
            fine_tune_language_layers=True,fine_tune_attention_modules=True,fine_tune_mlp_modules=True,
            r=8,lora_alpha=16,lora_dropout=0,bias='none',random_state=42,use_rslora=False)
        FastVisionModel.for_training(model)
    else:
        from transformers import AutoModelForImageTextToText, AutoProcessor
        from peft import LoraConfig, get_peft_model
        processor = AutoProcessor.from_pretrained(str(args.model),local_files_only=True)
        model = AutoModelForImageTextToText.from_pretrained(str(args.model),local_files_only=True,
            dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'})
        suffixes = {'q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj',
                    'in_proj_qkv','in_proj_z','in_proj_b','in_proj_a','out_proj'}
        targets = [name for name,module in model.named_modules() if isinstance(module,torch.nn.Linear)
                   and 'language_model' in name and name.rsplit('.',1)[-1] in suffixes]
        if not targets: raise RuntimeError('No language-only LoRA modules found in this model architecture')
        model = get_peft_model(model,LoraConfig(r=8,lora_alpha=16,lora_dropout=0,bias='none',
            target_modules=targets,task_type='CAUSAL_LM'))
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        model.enable_input_require_grads()
    model.config.use_cache = False
    trained = [(name,p.numel()) for name,p in model.named_parameters() if p.requires_grad]
    if not trained or any('visual' in name or 'vision' in name for name,_ in trained):
        raise RuntimeError('Vision encoder freeze check failed')
    train, validation, test = (rows(ROOT/f'data/deep_learning/{split}.jsonl') for split in ('train','validation','test'))
    groups = [{r['group_id'] for r in split} for split in (train,validation,test)]
    if any(groups[i]&groups[j] for i,j in ((0,1),(0,2),(1,2))): raise RuntimeError('Data leakage: overlapping original-question groups')
    if any(r['origin'] != 'generated_practice' for r in train):
        raise RuntimeError('Actual captures are acceptance-only in this initial recipe')
    collator = CompletionCollator(processor,args.context,args.image_pixels)
    rejected, usable, usable_validation = [], [], []
    for row in train:
        try: collator([row]); usable.append(row)
        except ValueError as error: rejected.append({'id':row['id'],'error':str(error)})
    for row in validation:
        try: collator([row]); usable_validation.append(row)
        except ValueError as error: rejected.append({'id':row['id'],'split':'validation','error':str(error)})
    # A short smoke run may use fewer rows, but full training must retain >=300 complete samples.
    if args.max_steps < 0 and len(usable) < 300:
        raise RuntimeError(f'Only {len(usable)} complete samples fit; need >=300. No truncation was applied')
    if args.max_steps < 0 and len(usable_validation) < 60:
        raise RuntimeError(f'Only {len(usable_validation)} complete validation samples fit; need >=60')
    config = {'backend':args.backend,'model':str(args.model),'dtype':'bfloat16','vision_frozen':True,
              'r':8,'alpha':16,'batch':1,'gradient_accumulation':8,'learning_rate':1e-4,'epochs':2,
              'context':args.context,'image_pixels':args.image_pixels,'max_steps':args.max_steps,
              'samples':len(usable),'validation_samples':len(usable_validation),'rejected':rejected,'trainable_parameters':sum(n for _,n in trained),
              'dataset_sha256':hashlib.sha256((ROOT/'data/deep_learning/train.jsonl').read_bytes()).hexdigest()}
    (args.output/'recipe.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in config.items() if k!='rejected'},indent=2),flush=True)
    if args.preflight_only: return
    from transformers import Trainer, TrainingArguments, TrainerCallback

    class ThermalGuard(TrainerCallback):
        def on_step_begin(self, args, state, control, **kwargs):
            deadline = time.monotonic()+20
            while (temp:=temperature()) is not None and temp >= 85:
                if time.monotonic() >= deadline: raise RuntimeError(f'GPU {temp} C: thermal gate stopped training')
                time.sleep(1)

    training_args = TrainingArguments(output_dir=str(args.output),per_device_train_batch_size=1,
        per_device_eval_batch_size=1,gradient_accumulation_steps=8,learning_rate=1e-4,
        num_train_epochs=2,max_steps=args.max_steps,bf16=True,fp16=False,optim='adamw_torch',
        gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},
        logging_steps=1,save_steps=10 if args.max_steps>0 else 40,save_total_limit=2,
        eval_strategy='no' if args.max_steps>0 else 'steps',eval_steps=40,prediction_loss_only=True,
        remove_unused_columns=False,dataloader_num_workers=0,
        report_to='none',seed=42,weight_decay=0.01,warmup_ratio=0.05)
    trainer = Trainer(model=model,args=training_args,train_dataset=Samples(usable),eval_dataset=Samples(usable_validation),
                      data_collator=collator,callbacks=[ThermalGuard()])
    torch.cuda.reset_peak_memory_stats()
    started=time.perf_counter()
    try:
        outcome = trainer.train(resume_from_checkpoint=str(args.resume) if args.resume else None)
        trainer.save_model(str(args.output)); processor.save_pretrained(str(args.output))
        report = {'complete':True,'global_steps':trainer.state.global_step,'metrics':outcome.metrics,
                  'seconds':time.perf_counter()-started,'peak_vram_mib':torch.cuda.max_memory_allocated()/2**20,
                  'smoke_only':args.max_steps>0,'promoted':False}
        (args.output/'training_result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2),flush=True)
    except torch.OutOfMemoryError:
        (args.output/'failure.json').write_text(json.dumps({'error':'CUDA OOM','context':args.context,
            'image_pixels':args.image_pixels,'fallback':'Retry --image-pixels 131072 --context 1024; only complete fitting samples are retained'}),encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
