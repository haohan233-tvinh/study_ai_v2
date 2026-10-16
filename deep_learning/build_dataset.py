"""Deterministic, auditable practice data. This is NOT real-exam acceptance data."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'fast_v2'))
from src.retrieval import CourseIndex
from src.dl_prompt import SYSTEM, prompt

DATA = ROOT / 'data' / 'deep_learning'


def number(x):
    return str(int(x)) if abs(x-round(x)) < 1e-8 else f'{x:.4f}'


def example(family, n):
    """Answers are derived from explicit arithmetic/rules, never a model answer bank."""
    a, b = n+2, n%5+2
    category = 'theory'
    if family == 0:
        q, value = f'Linear regression y_hat = {b}*x + 3. What is y_hat at x={a}?', b*a+3
        proof = f'{b}*{a}+3={value}'
    elif family == 1:
        q, value = f'Targets are [{a}, {a+2}], predictions [{a-1}, {a-1}]. What is the mean squared error?', 5
        proof = '(1^2+3^2)/2=5'
    elif family == 2:
        z = (n-12)/4
        q, value = f'For sigmoid(z)=1/(1+exp(-z)), evaluate sigmoid({z}) to 4 decimals.', 1/(1+math.exp(-z))
        proof = f'1/(1+exp(-{z}))={value:.8f}'
    elif family == 3:
        s = (n+1)/26
        q, value = f'A sigmoid unit output is s={s:.6f}. Using the unrounded s={n+1}/26, what is ds/dz to 4 decimals?', s*(1-s)
        proof = f's*(1-s)={value:.8f}'
    elif family == 4:
        p = (n+1)/26
        q, value = f'Binary target y=1 and probability p={n+1}/26. What is binary cross entropy with natural log?', -math.log(p)
        proof = f'-log(p)={value:.8f}'
    elif family == 5:
        q, value = f'A fully connected layer has {a} inputs and {b} outputs, with one bias per output. How many trainable parameters?', a*b+b
        proof = f'{a}*{b}+{b}={value}'
    elif family == 6:
        q, value = f'x={a}; z={b}*x; L=z^2. Compute dL/dx.', 2*b*b*a
        proof = f'(dL/dz)*(dz/dx)=2*z*{b}={value}'
    elif family == 7:
        q, value = f'Let x={n-12}. What is ReLU(x)?', max(0,n-12)
        proof = 'ReLU(x)=max(0,x)'
    elif family == 8:
        q, value = f'SGD: weight w={a}, gradient g={b}, learning rate 0.1. What is the updated weight?', a-.1*b
        proof = f'w-lr*g={value}'
    elif family == 9:
        q, value = f'A softmax classifier has {a} logits, all equal to {b}. What probability is assigned to each class?', 1/a
        proof = f'exp({b})/({a}*exp({b}))=1/{a}'
    elif family == 10:
        size, k, pad, stride = 16+n, 3, n%2, 2
        q, value = f'Conv2d input spatial size {size}x{size}, kernel {k}, padding {pad}, stride {stride}, dilation 1. What is one output spatial dimension?', (size+2*pad-k)//stride+1
        proof = f'floor(({size}+2*{pad}-{k})/{stride})+1={value}'
    elif family == 11:
        q, value = f'Conv2d has {b} input channels, {a} output channels, a 3x3 kernel and a bias. How many trainable parameters?', a*(b*9+1)
        proof = f'{a}*({b}*3*3+1)={value}'
    elif family == 12:
        size = 20+n
        q, value = f'MaxPool2d(kernel_size=2,stride=2,padding=0,ceil_mode=False) receives a {size}x{size} image. What is one output spatial dimension?', size//2
        proof = f'floor(({size}-2)/2)+1={value}'
    elif family == 13:
        q, value = f'An activation tensor has shape (8,{b},{a},3). After flatten(start_dim=1), how many features are there per sample?', b*a*3
        proof = f'{b}*{a}*3={value}'
    elif family == 14:
        q, value = f'Dropout probability is 0.25 during training. For {a*4} activations, what is the expected count retained before rescaling?', a*3
        proof = f'{a*4}*(1-0.25)={value}'
    elif family == 15:
        q, value = f'BatchNorm1d(num_features={a},affine=True). How many trainable affine parameters, excluding running statistics?', a*2
        proof = f'gamma and beta each have {a} parameters'
    elif family == 16:
        category = 'code'
        q = f'Which code correctly reshapes a tensor with {a*b} elements into ({a},{b})? Select ONE.'
        choices = [f'x.reshape({a}, {b})', f'x.reshape({a+1}, {b})', f'x.reshape({a}, {b+1})', f'x.reshape({a*b+1})']
        return q, choices, [0], f'Only {a}*{b} preserves numel={a*b}', category
    elif family == 17:
        category = 'code'
        q = f'PyTorch classification: logits shape ({a},{b}); target is long tensor shape ({a},) with class indices. Select ALL snippets giving the standard cross-entropy loss on these logits.'
        choices = ['loss = torch.nn.CrossEntropyLoss()(logits, target)',
                   'loss = torch.nn.functional.cross_entropy(logits, target)',
                   'loss = torch.nn.CrossEntropyLoss()(logits.softmax(dim=1), target)',
                   'loss = torch.nn.CrossEntropyLoss()(target, logits)']
        return q, choices, [0,1], 'CrossEntropyLoss expects unnormalized logits, and input before target', category
    elif family == 18:
        category = 'image'
        q, value = f'One attention head has sequence length {a} and query/key dimension d_k={b*b}. What denominator scales QK^T before softmax?', b
        proof = f'sqrt(d_k)=sqrt({b*b})={b}'
    elif family == 19:
        category = 'image'
        q, value = f'Object detection: two boxes have areas {a*4} and {a*6}; intersection area is {a*2}. What is intersection over union?', .25
        proof = f'IoU={a*2}/({a*4}+{a*6}-{a*2})=0.25'
    elif family == 20:
        category = 'image'
        q, value = 'Read the computational graph. What is the scalar output after the last operation?', max(0,(n-10)*b+3)**2
        proof = f'x={n-10}; w={b}; bias=3; output=ReLU(x*w+3)^2={value}'
    elif family == 21:
        category = 'image'
        q, value = 'Đọc ma trận trong ảnh. Max pooling 2x2, stride 2, padding 0 cho phần tử trên bên trái bằng bao nhiêu?', max(a,b,a-1,b+4)
        proof = f'max({a},{b},{a-1},{b+4})={value}'
    elif family == 22:
        category = 'image'
        q, value = 'For the two axis-aligned boxes in the diagram, compute IoU from the labelled coordinates. Round to 4 decimals.', a/(3*a+4)
        proof = f'Intersection width={a}, height=2; areas=4*({a}+1), 4*({a}+1); IoU=2*{a}/(8*({a}+1)-2*{a})={value}'
    elif family == 23:
        category = 'code'
        q = f'Given x=torch.tensor({float(a)}, requires_grad=True), which snippet computes d(x**2)/dx into x.grad?'
        choices=['y = x ** 2\ny.backward()', 'y = x.detach() ** 2\ny.backward()',
                 'with torch.no_grad():\n    y = x ** 2\ny.backward()', 'y = x ** 2\nx.zero_()']
        return q,choices,[0],f'y=x^2 retains autograd; y.backward() gives x.grad={2*a}',category
    elif family == 24:
        category = 'code'
        q = f'A PyTorch model processes {a} minibatches. Choose the loop that clears old gradients, computes current gradients, then updates parameters once per batch.'
        choices=['for x, y in loader:\n    optimizer.zero_grad()\n    loss = criterion(model(x), y)\n    loss.backward()\n    optimizer.step()',
                 'for x, y in loader:\n    loss = criterion(model(x), y)\n    loss.backward()\n    optimizer.zero_grad()\n    optimizer.step()',
                 'for x, y in loader:\n    optimizer.zero_grad()\n    loss = criterion(model(x), y)\n    optimizer.step()\n    loss.backward()',
                 'for x, y in loader:\n    optimizer.zero_grad()\n    loss = criterion(model(x), y)\n    loss.backward()\noptimizer.step()']
        return q,choices,[0],'zero_grad before backward; step after backward and inside the loop',category
    elif family == 25:
        category = 'code'
        q = f'x has shape ({a},{b},5). Which PyTorch expression swaps the last two dimensions, producing ({a},5,{b})?'
        choices=['x.transpose(1, 2)','x.transpose(0, 1)','x.reshape(-1)','x.unsqueeze(0)']
        return q,choices,[0],'transpose swaps dimensions without combining values',category
    elif family == 26:
        category = 'code'
        q = f'Q and K have shape (1,{a},{b}); V has shape (1,{a},7). Select the correct scaled dot-product attention output.'
        choices=[f'torch.softmax(Q @ K.transpose(-2, -1) / ({b} ** 0.5), dim=-1) @ V',
                 f'torch.softmax(Q @ K.transpose(-2, -1) / ({a} ** 0.5), dim=0) @ V',
                 'torch.softmax(Q @ K, dim=-1) @ V',
                 'torch.softmax(V, dim=-1) @ Q']
        return q,choices,[0],'Scale by sqrt(d_k), normalize over key positions, multiply by V',category
    elif family == 27:
        category = 'code'
        q = f'Cho tensor x=torch.arange({a*b}).reshape({a},{b}). Đoạn code nào trả về tổng riêng từng hàng, shape ({a},)?'
        choices=['x.sum(dim=1)','x.sum(dim=0)','x.sum()','x.mean(dim=0)']
        return q,choices,[0],'Reduce dimension 1 (columns), keeping one sum for each row',category
    elif family == 28:
        q, value = f'An image classifier correctly predicts {a} of {a+b} samples. What is accuracy as a fraction (not percent), rounded to 4 decimals?', a/(a+b)
        proof = f'accuracy=correct/total={a}/({a}+{b})={value}'
    else:
        q, value = f'Binary classification has TP={a}, FP={b}, FN=3. What is recall, rounded to 4 decimals?', a/(a+3)
        proof = f'recall=TP/(TP+FN)={a}/({a}+3)={value}'
    correct = number(value)
    wrong = []
    for shift in (1, -1, 2, 3, -2):
        candidate = number(value+shift)
        if candidate != correct and candidate not in wrong:
            wrong.append(candidate)
    return q, [correct, *wrong[:3]], [0], proof, category


def render(row, path):
    font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 21)
    small = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 18)
    question = textwrap.wrap(row['question'], 68)
    option_lines = {k: [part for line in v.splitlines() for part in
                       (textwrap.wrap(line, 62, replace_whitespace=False, drop_whitespace=False) or [''])]
                    for k,v in row['options'].items()}
    height = 60+len(question)*28+sum(len(lines)*26+30 for lines in option_lines.values())
    diagram = row['category'] == 'image'
    diagram_height = 160 if row['family'] in (21,22) else 90
    if diagram:
        height += diagram_height
    canvas = Image.new('RGB', (920, height), 'white')
    draw = ImageDraw.Draw(canvas)
    y = 20
    for line in question:
        draw.text((24,y),line,font=font,fill='black'); y += 28
    if diagram:
        n=row['variant']; a,b=n+2,n%5+2
        if row['family'] in (18,20):
            labels=('QK^T','scale','softmax','multiply V') if row['family']==18 else (f'x = {n-10}',f'* {b} + 3','ReLU','square')
            for i,label in enumerate(labels):
                x = 26+i*219
                draw.rectangle((x,y+10,x+185,y+60),outline='#204090',width=2)
                draw.text((x+8,y+24),label,font=small,fill='#204090')
                if i < 3:
                    draw.line((x+185,y+35,x+215,y+35),fill='black',width=2)
                    draw.polygon([(x+215,y+35),(x+207,y+30),(x+207,y+40)],fill='black')
        elif row['family'] == 21:
            grid=((a,b,0,1),(a-1,b+4,2,3),(0,1,2,3),(4,5,6,7))
            for r,values in enumerate(grid):
                for c,value in enumerate(values):
                    x,top=30+c*55,y+r*35
                    draw.rectangle((x,top,x+55,top+35),outline='black')
                    draw.text((x+12,top+5),str(value),font=small,fill='black')
        elif row['family'] == 22:
            draw.rectangle((30,y+5,250,y+105),outline='#204090',width=3)
            draw.rectangle((90,y+55,310,y+155),outline='#a03020',width=3)
            draw.text((335,y+15),f'Blue: (0,0) to ({a+1},4)',font=small,fill='#204090')
            draw.text((335,y+55),f'Red: (1,2) to ({a+2},6)',font=small,fill='#a03020')
            draw.text((335,y+95),'Coordinates define areas.',font=small,fill='black')
        else:
            draw.rectangle((30,y+5,160,y+65),outline='#204090',width=3)
            draw.rectangle((115,y+25,310,y+80),outline='#a03020',width=3)
        y += diagram_height
    two_cols = row['layout'] == 'two_columns' and all(len(v)<=26 for v in row['options'].values())
    for i,(label,lines) in enumerate(option_lines.items()):
        x = 25+(i%2)*450 if two_cols else 25
        top = y+(i//2)*68 if two_cols else y
        bottom = top+max(48,len(lines)*26+16)
        draw.rectangle((x,top,x+(425 if two_cols else 870),bottom),outline='#c2c2c2',width=2)
        draw.text((x+10,top+8),label+')',font=font,fill='black')
        for j,line in enumerate(lines):
            draw.text((x+52,top+8+j*26),line,font=font,fill='black')
        if not two_cols:
            y = bottom+12
    path.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(path)


def build():
    index = CourseIndex(json.loads((DATA/'course_knowledge.json').read_text(encoding='utf-8')))
    result = {'train': [], 'validation': [], 'test': []}
    for family in range(30):
        sequence = list(range(24)); random.Random(1400+family).shuffle(sequence)
        membership = {n:'train' if i<16 else 'validation' if i<19 else 'test' for i,n in enumerate(sequence)}
        for n in range(24):
            q, choices, correct, proof, category = example(family,n)
            evidence = {'family':family,'variant':n} if family in (20,21,22) else None
            original = json.dumps([q,sorted(choices),evidence],sort_keys=True)
            group = hashlib.sha256(original.encode()).hexdigest()[:20]
            rng = random.Random(int(group[:8],16))
            order = list(range(len(choices))); rng.shuffle(order)
            options = {chr(65+i):choices[j] for i,j in enumerate(order)}
            answer = ', '.join(chr(65+i) for i,j in enumerate(order) if j in correct)
            visual = category in ('image','code') or n%2 == 0
            row = {'id':group, 'group_id':group, 'origin':'generated_practice', 'family':family, 'variant':n,
                   'question':q, 'options':options, 'answer':answer, 'multi':len(correct)>1,
                   'count':None, 'category':category, 'proof':proof,
                   'layout':'two_columns' if n%3==0 else 'stacked', 'image':None}
            excerpts = index.search(q,options,2)
            # Limit complete supporting passages before training, without cutting a question/option.
            remaining = 1800; selected=[]
            for item in excerpts:
                passage = item['text'][:remaining]
                selected.append(dict(item,text=passage)); remaining -= len(passage)
                if remaining < 100: break
            row['excerpts'] = selected
            row['source'] = 0  # all generated questions have explicit rule/arithmetic evidence
            if visual:
                path = DATA/'dataset_images'/f'{group}.png'
                render(row,path); row['image'] = str(path.relative_to(ROOT)).replace('\\','/')
            # A subset has no OCR text, to train the same fallback used for diagrams/code.
            hide_ocr = visual and n%3==0
            row['input_question'] = '' if hide_ocr else q
            row['input_options'] = {k:'' for k in options} if hide_ocr else options
            row['prompt'] = prompt(row['input_question'],row['input_options'],selected,row['multi'])
            row['target'] = json.dumps({'answer':answer,'source':0},separators=(',',':'))
            result[membership[n]].append(row)
    groups = {split:{r['group_id'] for r in rows} for split,rows in result.items()}
    assert not (groups['train'] & groups['validation'] or groups['train'] & groups['test'] or groups['validation'] & groups['test'])
    for split,rows in result.items():
        (DATA/f'{split}.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
    manifest = {'seed':1400,'system':SYSTEM,'counts':{k:len(v) for k,v in result.items()},
                'images':{k:sum(bool(r['image']) for r in v) for k,v in result.items()},
                'group_overlap':False, 'actual_capture_count':0,
                'scope':'Generated practice only. Template families recur across splits; this is not an estimate of accuracy on real captures.',
                'files':{k:hashlib.sha256((DATA/f'{k}.jsonl').read_bytes()).hexdigest() for k in result}}
    (DATA/'dataset_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    build()
