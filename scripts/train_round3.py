"""Train development candidates; select using validation only, never the 70 tests."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import random
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
import torch
from torch import nn
from torch.utils.data import Dataset,DataLoader,WeightedRandomSampler
from torchvision import models,transforms

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from web.model_factory import from_checkpoint
from train_available import metrics


def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')


class Cached(Dataset):
    def __init__(self,rows):
        self.rows=rows
        def read(row):
            with Image.open(ROOT/row['image_path']) as im:
                return torch.from_numpy(np.asarray(ImageOps.exif_transpose(im).convert('RGB').resize((224,224),Image.Resampling.BILINEAR)).copy()).permute(2,0,1)
        with ThreadPoolExecutor(6) as pool:self.images=list(pool.map(read,rows))
    def __len__(self):return len(self.rows)
    def __getitem__(self,i):return self.images[i],self.rows[i]['label'],i


def main():
    parser=argparse.ArgumentParser();parser.add_argument('branch',choices=['body','cattle','pig']);parser.add_argument('--epochs',type=int,default=28);args=parser.parse_args()
    branch=args.branch
    torch.set_num_threads(4)
    assert torch.cuda.is_available()
    torch.backends.cudnn.benchmark=True
    device=torch.device('cuda')
    out=ROOT/f'reports/training_round3_20261114/{branch}'
    if (out/'selection_before_test.json').exists():
        if branch!='body':raise RuntimeError('Training selection already complete')
        # Additional validation-only configurations; keep the first selection as an audit record.
        first=out/'selection_first_validation_pass.json'
        if not first.exists():first.write_bytes((out/'selection_before_test.json').read_bytes())
    directory=ROOT/f'data/processed/round3_{branch}'
    manifest=directory/'manifest.json'
    rows=json.loads(manifest.read_text(encoding='utf-8'))
    prepared=json.loads((directory/'summary.json').read_text(encoding='utf-8'))
    initial=torch.load(ROOT/prepared['initial_checkpoint'],map_location='cpu',weights_only=True)
    classes=initial['classes']
    datasets={s:Cached([r for r in rows if r['split']==s]) for s in ['train','val']}
    mean=torch.tensor(initial['mean'],device=device).view(1,3,1,1)
    std=torch.tensor(initial['std'],device=device).view(1,3,1,1)
    val_loader=DataLoader(datasets['val'],batch_size=48,num_workers=0)
    @torch.inference_mode()
    def evaluate(model):
        model.eval();ys=[];probs=[]
        for x,y,_ in val_loader:
            p=model((x.to(device).float()/255-mean)/std).softmax(1).cpu().tolist()
            probs+=p;ys+=y.tolist()
        ps=np.argmax(probs,axis=1).tolist()
        result={}
        for domain in ['all','legacy','new']:
            ix=[i for i,r in enumerate(datasets['val'].rows) if domain=='all' or (r['domain']=='legacy')==(domain=='legacy')]
            if not ix:continue
            m=metrics([ys[i] for i in ix],[ps[i] for i in ix],classes)
            m['n']=len(ix);m['correct']=sum(ys[i]==ps[i] for i in ix)
            m['macro_f1_present']=float(np.mean([v['f1'] for v in m['per_class'].values() if v['support']]))
            result[domain]=m
        return result,[{**r,'prediction':classes[p],'scores':s} for r,p,s in zip(datasets['val'].rows,ps,probs)]
    model=from_checkpoint(initial).to(device)
    baseline,_=evaluate(model);save(out/'baseline_validation.json',baseline)
    del model
    print('BASELINE',branch,json.dumps({d:[m['correct'],m['n']] for d,m in baseline.items()}),flush=True)
    candidates=[('current',17),('efficientnet_imagenet',42),('current',42),('efficientnet_imagenet',17)] if branch=='body' else [('current',17),('current',42)]
    results=[]
    for mode,seed in candidates:
        dest=ROOT/f'models/round3_{branch}_{mode}_seed{seed}'
        if (dest/'validation.json').exists():results.append(json.loads((dest/'validation.json').read_text(encoding='utf-8')));continue
        random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
        if mode=='efficientnet_imagenet':
            model=models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
            model.classifier[1]=nn.Linear(model.classifier[1].in_features,len(classes));architecture='efficientnet_b0'
        else:model=from_checkpoint(initial);architecture=initial.get('architecture','resnet18')
        model=model.to(device)
        for p in model.parameters():p.requires_grad=False
        parts=[model.layer3,model.layer4,model.fc] if architecture=='resnet18' else [model.features[-3:],model.classifier]
        tuned=branch=='body' and ((mode=='current' and seed==42) or (mode=='efficientnet_imagenet' and seed==17))
        if tuned:parts=[model]  # Adapt the full feature hierarchy for the new photographic domain.
        for part in parts:
            for p in part.parameters():p.requires_grad=True
        lr=8e-5 if branch=='body' else 1.5e-5 if branch=='cattle' else 3e-5
        if tuned:
            head=model.fc if architecture=='resnet18' else model.classifier
            head_ids={id(p) for p in head.parameters()}
            groups=[{'params':[p for p in model.parameters() if p.requires_grad and id(p) not in head_ids],'lr':2e-5},
                    {'params':head.parameters(),'lr':1e-3 if mode=='efficientnet_imagenet' else 3e-4}]
            optimizer=torch.optim.AdamW(groups,weight_decay=.02)
        else:optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=lr,weight_decay=.02)
        scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,args.epochs,eta_min=lr*.1)
        train_rows=datasets['train'].rows
        counts=Counter((r['class_name'],r['domain']!='legacy') for r in train_rows)
        weights=[]
        for r in train_rows:
            c=r['class_name'];fresh=r['domain']!='legacy';hasnew=counts[(c,True)]>0
            share=(.65 if branch=='body' else .45) if hasnew else 0
            weights.append((share if fresh else 1-share)/counts[(c,fresh)])
        loader=DataLoader(datasets['train'],batch_size=32,num_workers=0,
                          sampler=WeightedRandomSampler(weights,max(768,len(train_rows)),generator=torch.Generator().manual_seed(seed)))
        scaler=torch.amp.GradScaler('cuda');criterion=nn.CrossEntropyLoss(label_smoothing=.03)
        crop=transforms.RandomResizedCrop((224,224),scale=(.78,1),ratio=(.9,1.1),antialias=True)
        best=-1;stale=0;history=[]
        def rank(val):
            # Frozen validation objective and regression gates, declared before tests.
            guard=val['legacy']['accuracy']>=baseline['legacy']['accuracy']-(.07 if branch=='body' else .03)
            guard=guard and val['legacy']['per_class']['unknown']['recall']>=.8
            score=.45*val['legacy']['macro_f1_present']+.55*val.get('new',val['legacy'])['macro_f1_present']
            return score+(2 if guard else 0),guard
        for epoch in range(1,args.epochs+1):
            started=time.monotonic();model.eval();total=0
            for x,y,_ in loader:
                x=x.to(device).float()/255
                if random.random()<.5:x=x.flip(-1)
                if random.random()<.65:x=crop(x)
                gain=torch.empty((len(x),1,1,1),device=device).uniform_(.85,1.15)
                x=(torch.clamp(x*gain,0,1)-mean)/std
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type='cuda'):loss=criterion(model(x),y.to(device))
                scaler.scale(loss).backward();scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],5)
                scaler.step(optimizer);scaler.update();total+=loss.item()*len(y)
            scheduler.step();val,_=evaluate(model);score,guard=rank(val)
            history.append({'epoch':epoch,'loss':total/max(768,len(train_rows)),'rank':score,'guard':guard,'validation':val,'seconds':time.monotonic()-started})
            if score>best:
                best=score;stale=0
                updated={**initial,'architecture':architecture,'state_dict':model.state_dict(),'epoch':epoch,'seed':seed,
                         'training_manifest':manifest.relative_to(ROOT).as_posix(),'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
                         'initial_checkpoint':prepared['initial_checkpoint'],'scope':'external_signs_only' if branch=='body' else initial.get('scope','experimental_image_classification')}
                dest.mkdir(parents=True,exist_ok=True);torch.save(updated,dest/'best.pt')
            else:stale+=1
            save(dest/'history.json',history)
            print('EPOCH',branch,mode,seed,epoch,'guard',guard,'val',json.dumps({d:[m['correct'],m['n'],round(m['macro_f1_present'],3)] for d,m in val.items()}),'seconds',round(time.monotonic()-started,1),flush=True)
            if epoch>=12 and stale>=7:break
        ck=torch.load(dest/'best.pt',map_location='cpu',weights_only=True);model.load_state_dict(ck['state_dict'])
        val,predictions=evaluate(model);score,guard=rank(val)
        record={'checkpoint':(dest/'best.pt').relative_to(ROOT).as_posix(),'epoch':ck['epoch'],'seed':seed,'mode':mode,'rank':score,'regression_guard':guard,'validation':val}
        save(dest/'validation.json',record);save(dest/'validation_predictions.json',predictions);results.append(record)
        del model;torch.cuda.empty_cache()
    chosen=max(results,key=lambda r:r['rank'])
    save(out/'selection_before_test.json',{'chosen':chosen,'candidates':results,'test_used_for_selection':False,
                                          'test_manifest_sha256':prepared['test_manifest_sha256']})
    print('SELECTED',branch,chosen['checkpoint'],flush=True)


if __name__=='__main__':main()
