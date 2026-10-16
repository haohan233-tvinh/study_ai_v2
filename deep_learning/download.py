"""Resumable verified range downloads through Windows curl; setup only."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*2**20),b''): h.update(block)
    return h.hexdigest()


def download(url,target,size,digest,workers=16,chunk_size=4*2**20):
    target=Path(target); target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_file() and target.stat().st_size==size and sha256(target)==digest:
        print('Verified existing:',target.name,flush=True); return
    executable=shutil.which('curl.exe') or shutil.which('curl')
    if not executable: raise RuntimeError('curl is needed for the range downloader')
    pieces=target.with_name(target.name+'.ranges'); pieces.mkdir(exist_ok=True)
    count=(size+chunk_size-1)//chunk_size
    partial=target.with_name(target.name+'.part')
    if partial.is_file() and partial.stat().st_size<=size:
        with partial.open('rb') as seed:
            for i in range(min(count,partial.stat().st_size//chunk_size)):
                file=pieces/f'{i:05}.bin'
                if not file.exists():
                    seed.seek(i*chunk_size); file.write_bytes(seed.read(chunk_size))

    def part(index):
        start=index*chunk_size; end=min(size-1,start+chunk_size-1); length=end-start+1
        file=pieces/f'{index:05}.bin'; header=pieces/f'{index:05}.headers'
        if file.is_file() and file.stat().st_size==length: return index
        temporary=file.with_suffix('.tmp')
        progress=file.with_suffix('.progress')
        # Recover a previously interrupted, range-validated response.
        if temporary.is_file() and not progress.exists():
            headers=header.read_text(encoding='latin1') if header.exists() else ''
            previous=re.findall(r'(?im)^content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)\s*$',headers)
            if previous and tuple(map(int,previous[-1]))==(start,end,size) and temporary.stat().st_size<=length:
                progress.write_text(str(temporary.stat().st_size))
            else:
                temporary.unlink()
        failures=0
        while True:
            received=temporary.stat().st_size if temporary.is_file() and progress.exists() else 0
            if received==length:
                os.replace(temporary,file); progress.unlink(missing_ok=True); return index
            request_start=start+received
            request_end=min(end,request_start+1024*1024-1)
            tail=file.with_suffix('.tail')
            result=subprocess.run([executable,'--fail','--location','--silent','--show-error',
                '--connect-timeout','10','--max-time','45','--range',f'{request_start}-{request_end}',
                '--dump-header',str(header),'--output',str(tail),url],
                capture_output=True,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            headers=header.read_text(encoding='latin1') if header.exists() else ''
            ranges=re.findall(r'(?im)^content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)\s*$',headers)
            valid=(ranges and tuple(map(int,ranges[-1]))==(request_start,request_end,size)
                   and tail.is_file() and 0<tail.stat().st_size<=request_end-request_start+1)
            if valid:
                with temporary.open('ab') as output,tail.open('rb') as source:
                    shutil.copyfileobj(source,output)
                progress.write_text(str(temporary.stat().st_size))
                failures=0
            else:
                failures+=1
                if failures>=5: raise RuntimeError(f'{target.name} range {index} failed: {result.stderr[-400:]}')
                time.sleep(failures)
            tail.unlink(missing_ok=True)

    started=time.perf_counter(); completed=0
    pool=ThreadPoolExecutor(max_workers=workers)
    try:
        futures=[pool.submit(part,i) for i in range(count)]
        for future in as_completed(futures):
            future.result(); completed+=1
            if completed%10==0 or completed==count:
                print(f'{target.name}: {completed}/{count} ranges ({completed*100/count:.1f}%), {time.perf_counter()-started:.0f}s',flush=True)
    finally:
        pool.shutdown(wait=True,cancel_futures=True)
    assembled=target.with_name(target.name+'.assembled')
    with assembled.open('wb') as output:
        for i in range(count):
            with (pieces/f'{i:05}.bin').open('rb') as source: shutil.copyfileobj(source,output,8*2**20)
    if assembled.stat().st_size!=size or sha256(assembled)!=digest:
        raise RuntimeError('SHA256 mismatch; nothing was activated: '+target.name)
    os.replace(assembled,target)
    # Delete only the exact files this downloader created, after full checksum validation.
    for i in range(count):
        for suffix in ('.bin','.tmp','.headers','.progress','.tail'): (pieces/f'{i:05}{suffix}').unlink(missing_ok=True)
    pieces.rmdir()
    target.with_name(target.name+'.part').unlink(missing_ok=True)
    print('Verified:',target.name,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',required=True); p.add_argument('--target',type=Path,required=True)
    p.add_argument('--size',type=int,required=True); p.add_argument('--sha256',required=True)
    p.add_argument('--workers',type=int,default=16)
    a=p.parse_args(); download(a.url,a.target,a.size,a.sha256,a.workers)
