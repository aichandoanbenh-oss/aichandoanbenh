"""Experimental training on existing public labels; no clinical claims."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import random
import re
import time

import numpy as np
from PIL import Image, ImageOps
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from prepare_cattle import dhash

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {'dog':'dog_five','cattle':'cattle_health','chicken':'chicken_fecal','pig':'pig_research'}

def prepare(species):
    source=SOURCES[species]
    rows=[json.loads(s) for s in (ROOT/'reports'/f'{source}_manifest.jsonl').read_text().splitlines()]
    if species=='chicken':
        with (ROOT/'data/raw/chicken_fecal/extracted/train_data.csv').open() as f:
            labels={r['images']:r['label'] for r in csv.DictReader(f)}
    selected=[]; omitted=[]
    pig_review=json.loads((ROOT/'reports/pig_selection.json').read_text(encoding='utf-8')) if species=='pig' else None
    for r in rows:
        if pig_review and (r['folder'] not in pig_review['selected_classes'] or r['path'] in pig_review['excluded_images']):
            omitted.append({**r,'reason':pig_review['excluded_images'].get(r['path'],'class_not_selected_for_pilot')}); continue
        if species in {'dog','pig'}: label=r['folder'].split('/')[-1]
        elif species=='chicken': label=labels[Path(r['path']).name]
        else:
            folder=r['folder'].lower()
            if 'normal teats' in folder or 'healthycows' in folder: label='healthy'
            elif 'lumpycows' in folder: label='lumpy_skin'
            elif 'foot-and-mouth' in folder: label='foot_and_mouth'
            elif folder.endswith('/mastitis/mastitis'): label='mastitis'
            else: omitted.append(r); continue
        r={**r,'class_name':label,'image_path':f'data/raw/{source}/extracted/'+r['path']}
        selected.append(r)
    parents=list(range(len(selected)))
    def find(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]]; i=parents[i]
        return i
    def union(i,j): parents[find(j)]=find(i)
    buckets=collections.defaultdict(list); exact={}; names={}
    for i,r in enumerate(selected):
        h=r['pixel_sha256']
        if h in exact: union(i,exact[h])
        else: exact[h]=i
        if species=='dog':
            name=re.sub(r'\.rf\.[^.]+','',Path(r['path']).name)
            name=re.sub(r'_x\d+(?=_(?:jpg|png|jpeg))','',name)
            if name in names: union(i,names[name])
            else: names[name]=i
        with Image.open(ROOT/r['image_path']) as im:
            im=ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((256,256))
            variants=[dhash(im)]+[dhash(im.transpose(op)) for op in Image.Transpose]
        candidates=set(); h=variants[0]
        for shift,width in [(0,13),(13,13),(26,13),(39,13),(52,12)]:
            candidates.update(buckets[(shift,(h>>shift)&((1<<width)-1))])
        for j,v in candidates:
            if (h^v).bit_count()<=4: union(i,j)
        for v in set(variants):
            for shift,width in [(0,13),(13,13),(26,13),(39,13),(52,12)]:
                buckets[(shift,(v>>shift)&((1<<width)-1))].append((i,v))
        if i%1000==0: print(species,'CLEAN',i,'/',len(selected),flush=True)
    groups=collections.defaultdict(list)
    for i,r in enumerate(selected): groups[find(i)].append(r)
    clean=[]; conflicts=[]; duplicates=[]
    for gid,group in groups.items():
        if len({r['class_name'] for r in group})>1:
            conflicts.extend([{**r,'group':gid} for r in group]); continue
        clean.append({**group[0],'group':gid})
        duplicates.extend([{**r,'group':gid} for r in group[1:]])
    if species=='pig':
        counts=collections.Counter(r['class_name'] for r in clean)
        excluded={c for c,n in counts.items() if n<10}
        omitted.extend([{**r,'reason':'fewer_than_10_independent_images'} for r in clean if r['class_name'] in excluded])
        clean=[r for r in clean if r['class_name'] not in excluded]
    classes=sorted({r['class_name'] for r in clean}); rng=random.Random(42)
    for label in classes:
        subset=[r for r in clean if r['class_name']==label]; rng.shuffle(subset)
        assert len(subset)>=10, f'Too few independent groups: {label}'
        n=len(subset); a=int(.7*n); b=a+int(.15*n)
        for i,r in enumerate(subset):
            r['label']=classes.index(label); r['split']='train' if i<a else 'val' if i<b else 'test'
    assert len({r['group'] for r in clean})==len(clean)
    assert len({r['pixel_sha256'] for r in clean})==len(clean)
    out=ROOT/'data/processed'/f'{species}_experimental'; out.mkdir(parents=True,exist_ok=True)
    summary={'source':source,'classes':classes,'raw':len(rows),'retained':len(clean),'conflicts':len(conflicts),'same_group_removed':len(duplicates),'ambiguous_folder_removed':len(omitted),'split_counts':{s:dict(collections.Counter(r['class_name'] for r in clean if r['split']==s)) for s in ['train','val','test']},'grouping':'one representative per connected component: pixel hash, dHash <=4 with rotations/flips; normalized Roboflow filenames for dog','limitations':'Heuristic groups are not animal/farm IDs; no guarantee all source leakage removed.'}
    for name,obj in [('manifest',clean),('summary',summary),('conflicts',conflicts),('duplicates',duplicates),('omitted',omitted)]:
        (out/f'{name}.json').write_text(json.dumps(obj,indent=2),encoding='utf-8')
    print(species,'PREPARED',json.dumps(summary),flush=True)
    return clean,classes

class Images(Dataset):
    def __init__(self,rows,training=False):
        self.rows=rows
        self.transform=transforms.Compose([transforms.Resize((224,224)),*([transforms.RandomHorizontalFlip(),transforms.RandomRotation(10),transforms.ColorJitter(brightness=.1,contrast=.1)] if training else []),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
    def __len__(self): return len(self.rows)
    def __getitem__(self,i):
        r=self.rows[i]
        with Image.open(ROOT/r['image_path']) as im: x=self.transform(ImageOps.exif_transpose(im).convert('RGB'))
        return x,r['label']

def metrics(y,p,classes):
    cm=np.zeros((len(classes),len(classes)),dtype=int)
    for a,b in zip(y,p): cm[a,b]+=1
    per={}
    for i,c in enumerate(classes):
        precision=float(cm[i,i]/max(1,cm[:,i].sum())); recall=float(cm[i,i]/max(1,cm[i].sum()))
        per[c]={'precision':precision,'recall':recall,'f1':2*precision*recall/max(1e-12,precision+recall),'support':int(cm[i].sum())}
    return {'accuracy':float(cm.trace()/cm.sum()),'macro_f1':sum(v['f1'] for v in per.values())/len(classes),'confusion_matrix_true_rows':cm.tolist(),'per_class':per}

@torch.inference_mode()
def evaluate(model,loader,device,classes):
    model.eval(); ys=[]; ps=[]; probs=[]
    for x,y in loader:
        p=model(x.to(device)).softmax(1).cpu()
        ys.extend(y.tolist()); ps.extend(p.argmax(1).tolist()); probs.extend(p.tolist())
    return metrics(ys,ps,classes),probs

def train(species,rows,classes,epochs):
    random.seed(42); np.random.seed(42); torch.manual_seed(42); torch.set_num_threads(4)
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    split={s:[r for r in rows if r['split']==s] for s in ['train','val','test']}
    loaders={s:DataLoader(Images(rs,s=='train'),batch_size=32,shuffle=s=='train',num_workers=0) for s,rs in split.items()}
    model=models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    for p in model.parameters(): p.requires_grad=False
    model.fc=nn.Linear(model.fc.in_features,len(classes))
    for p in model.layer4.parameters(): p.requires_grad=True
    model.to(device)
    counts=collections.Counter(r['label'] for r in split['train'])
    criterion=nn.CrossEntropyLoss(weight=torch.tensor([len(split['train'])/(len(classes)*counts[i]) for i in range(len(classes))],device=device))
    optimizer=torch.optim.AdamW([{'params':model.layer4.parameters(),'lr':1e-4},{'params':model.fc.parameters(),'lr':1e-3}],weight_decay=.01)
    out=ROOT/'models'/f'{species}_experimental_resnet18'; out.mkdir(parents=True,exist_ok=True)
    best=-1; stale=0; history=[]; start=time.time()
    for epoch in range(1,epochs+1):
        model.eval(); model.fc.train(); total=0
        for x,y in loaders['train']:
            x,y=x.to(device),y.to(device); optimizer.zero_grad(set_to_none=True)
            loss=criterion(model(x),y); loss.backward(); optimizer.step(); total+=loss.item()*len(y)
        val,_=evaluate(model,loaders['val'],device,classes)
        history.append({'epoch':epoch,'train_loss':total/len(split['train']),'validation':val})
        print(species,'EPOCH',epoch,'val_f1',round(val['macro_f1'],4),flush=True)
        if val['macro_f1']>best:
            best=val['macro_f1']; stale=0
            torch.save({'state_dict':model.state_dict(),'classes':classes,'species':species,'epoch':epoch,'mean':[.485,.456,.406],'std':[.229,.224,.225],'input_size':224,'architecture':'resnet18','scope':'experimental_public_dataset_labels'},out/'best.pt')
        else: stale+=1
        if stale>=4: break
    checkpoint=torch.load(out/'best.pt',map_location=device,weights_only=True); model.load_state_dict(checkpoint['state_dict'])
    test,probs=evaluate(model,loaders['test'],device,classes)
    report={'species':species,'classes':classes,'seed':42,'device':str(device),'best_epoch':checkpoint['epoch'],'test':test,'majority_baseline':max(collections.Counter(r['label'] for r in split['test']).values())/len(split['test']),'seconds':time.time()-start,'history':history,'manifest_sha256':hashlib.sha256((ROOT/'data/processed'/f'{species}_experimental/manifest.json').read_bytes()).hexdigest(),'limitations':['Labels inherited from public data; not independently clinically verified','No Vietnamese external test set','Anatomical/background confounding and residual near duplicates possible','Dog fungal/ringworm labels overlap; Healthy controls contain known quality problems','Softmax scores uncalibrated; no out-of-domain rejection','Chicken data include non-PCR annotations; license of full Kaggle compilation unclear']}
    (out/'metrics.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (out/'test_predictions.json').write_text(json.dumps([{**r,'scores':p,'prediction':int(np.argmax(p))} for r,p in zip(split['test'],probs)],indent=2),encoding='utf-8')
    print(species,'FINAL',json.dumps(test),flush=True)
    return report

def main():
    p=argparse.ArgumentParser(); p.add_argument('--species',nargs='+',choices=list(SOURCES),default=list(SOURCES)); p.add_argument('--epochs',type=int,default=12); p.add_argument('--reuse-prepared',action='store_true'); args=p.parse_args()
    reports=[]
    for species in args.species:
        if args.reuse_prepared:
            base=ROOT/'data/processed'/f'{species}_experimental'
            rows=json.loads((base/'manifest.json').read_text()); classes=json.loads((base/'summary.json').read_text())['classes']
        else: rows,classes=prepare(species)
        reports.append(train(species,rows,classes,args.epochs))
    target=ROOT/'reports/experimental_training.json'
    previous=json.loads(target.read_text(encoding='utf-8')) if target.exists() else []
    merged={r['species']:r for r in previous}
    merged.update({r['species']:r for r in reports})
    target.write_text(json.dumps(list(merged.values()),indent=2),encoding='utf-8')

if __name__=='__main__': main()
