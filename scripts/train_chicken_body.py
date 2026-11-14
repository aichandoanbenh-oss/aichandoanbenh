"""Research classifier of external chicken signs, not pathogen diagnoses.

Evet-Africa source data are AGPL-3.0. This derived training component and its
weights are provided under AGPL-3.0; see reports/improvement_20261113/BODY_NOTICE.md.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import sys

import numpy as np
from PIL import Image, ImageOps, ImageDraw
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import models, transforms

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prepare_chicken_improvement import describe, save, REPORT
from train_available import metrics

OUT = ROOT / 'data/processed/chicken_body_v1'
CLASSES = ['chicken_skin_lesions', 'chicken_head_neuro_signs', 'unknown']
NAMES = {'chicken_skin_lesions': 'Tổn thương da/đóng vảy vùng đầu cần khám',
         'chicken_head_neuro_signs': 'Dấu hiệu vùng đầu, mắt hoặc tư thế bất thường',
         'unknown': 'Ngoài phạm vi / chưa nhận diện được'}
# Recorded against body_review_0..3.jpg, before training or splitting.
EXCLUDE = {0: 'human_skin_wrong_species', 2: 'diagnosis_text_overlay', 8: 'dissected_head',
           11: 'forced_open_mouth', 13: 'promotional_text', 18: 'multi_panel', 21: 'diagnosis_text_overlay',
           28: 'multi_panel', 35: 'diagnosis_text_overlay', 38: 'multi_panel_diagnosis_text',
           41: 'histology_and_dissection_panel', 47: 'multi_panel', 52: 'dissected_head',
           66: 'dissected_head', 70: 'dissected_head', 79: 'dissected_head', 88: 'dissected_head',
           95: 'diagnosis_text_overlay', 98: 'dissected_head', 100: 'diagnosis_text_overlay',
           110: 'forced_open_mouth', 111: 'multi_panel', 115: 'forced_open_mouth',
           121: 'diagnosis_text_overlay', 129: 'forced_open_mouth', 130: 'forced_open_mouth',
           134: 'large_branding_overlay', 135: 'diagnosis_text_overlay', 139: 'multi_panel',
           145: 'forced_open_mouth', 148: 'diagnosis_text_overlay', 154: 'apparently_postmortem_head',
           157: 'internal_organs_mislabeled_torticollis', 159: 'apparently_postmortem_head',
           166: 'dissected_head', 167: 'multi_panel', 170: 'apparently_dead_bird',
           171: 'apparently_postmortem_head', 172: 'dissected_head', 174: 'dissected_head',
           175: 'apparently_dead_bird', 178: 'experiment_multi_panel', 182: 'dissected_head',
           183: 'apparently_postmortem_head', 187: 'multi_panel'}
MANUAL_GROUPS = [[15,26,83,90], [7,22,102], [12,116], [14,54,89], [16,152], [24,118],
                 [27,108], [37,91], [45,128], [61,71,72,101], [65,86], [67,105],
                 [73,124,149], [77,85], [87,97], [94,104,127], [96,144], [109,126],
                 [112,114], [113,132], [106,119], [158,190], [160,173], [161,181],
                 [163,189], [165,179], [177,193]]


def prepare():
    if (OUT / 'manifest.json').exists():
        return json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    source = json.loads((ROOT / 'data/raw/chicken_body_evet/external_candidates.json').read_text())
    rows, excluded = [], []
    manual_group = {i: f'visual_case_{g}' for g, members in enumerate(MANUAL_GROUPS) for i in members}
    for i, row in enumerate(source):
        if i in EXCLUDE or 18 in row['class_ids']:
            excluded.append({**row, 'review_index': i, 'reason': EXCLUDE.get(i, 'oral_or_dissection_outside_external_scope')})
            continue
        ids = set(row['class_ids'])
        label = 'chicken_skin_lesions' if 21 in ids or 16 in ids else 'chicken_head_neuro_signs'
        rows.append({'image_path': 'data/raw/chicken_body_evet/' + row['image']['path'],
                     'class_name': label, 'domain': 'external_signs', 'review_index': i,
                     'source_group': manual_group.get(i, 'case_' + str(i)),
                     'source_url': row['source_url'], 'source_repo_revision': row['revision'],
                     'clinical_sign_ids': row['class_ids'], 'license': 'AGPL-3.0',
                     'diagnosis_verified': False, 'split': 'unassigned'})
    controls = json.loads((ROOT / 'data/raw/chicken_body_controls/manifest.json').read_text(encoding='utf-8'))
    for row in controls:
        if 'error' in row:
            continue
        rows.append({**row, 'class_name': 'unknown', 'domain': 'commons_chicken_controls',
                     'source_group': 'commons_artist_' + row['artist'], 'split': 'unassigned'})
    # Existing negatives keep their old splits; fecal images teach input-domain rejection.
    old = json.loads((ROOT / 'data/processed/chicken_web_experimental/manifest.json').read_text())
    for split in ['train', 'val', 'test']:
        pool = [r for r in old if r['split'] == split]
        unknown = [r for r in pool if r['class_name'] == 'unknown'][:60 if split == 'train' else 12]
        fecal = random.Random(21).sample([r for r in pool if r['class_name'] != 'unknown'], 24 if split == 'train' else 8)
        for row in unknown + fecal:
            rows.append({'image_path': row['image_path'], 'class_name': 'unknown',
                         'domain': 'other_input_controls', 'split': split,
                         'source_group': 'legacy_control_' + str(row['source_group'])})
    rows = [describe(dict(r)) for r in rows]
    invalid = [r for r in rows if 'error' in r]
    rows = [r for r in rows if 'error' not in r]
    parent = list(range(len(rows)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i,j):
        parent[find(j)] = find(i)
    for i, row in enumerate(rows):
        for j, previous in enumerate(rows[:i]):
            near = (row['sha224'] == previous['sha224'] or row['source_group'] == previous['source_group']
                    or any((row['hashes'][0] ^ h).bit_count() <= 6 and (row['phashes'][0] ^ p).bit_count() <= 10
                           for h,p in zip(previous['hashes'], previous['phashes'])))
            if near:
                union(i,j)
    groups = defaultdict(list)
    for i,r in enumerate(rows):
        groups[find(i)].append(r)
    usable = []
    for gid, members in groups.items():
        old_splits = {r['split'] for r in members} - {'unassigned'}
        if len({r['class_name'] for r in members}) != 1 or len(old_splits) > 1:
            excluded.extend({**r, 'reason': 'conflicting_label_or_preserved_split_group'} for r in members)
            continue
        # Retain all distinct controls by the same author but keep them in one split.
        seen = set()
        for row in members:
            if row['sha224'] in seen:
                excluded.append({**row, 'reason': 'exact_duplicate'})
                continue
            seen.add(row['sha224'])
            row['audit_group'] = gid
            usable.append(row)
    rng = random.Random(20261114)
    for label in CLASSES:
        gids = sorted({r['audit_group'] for r in usable if r['class_name'] == label and r['split'] == 'unassigned'})
        rng.shuffle(gids)
        n = len(gids)
        nv = max(1, int(n * .2)) if n >= 5 else 0
        nt = max(1, int(n * .2)) if n >= 5 else 0
        splits = {g: ('val' if i < nv else 'test' if i < nv + nt else 'train') for i,g in enumerate(gids)}
        for row in usable:
            if row['class_name'] == label and row['split'] == 'unassigned':
                row['split'] = splits[row['audit_group']]
    for row in usable:
        row['label'] = CLASSES.index(row['class_name'])
    for gid in {r['audit_group'] for r in usable}:
        assert len({r['split'] for r in usable if r['audit_group'] == gid}) == 1
    summary = {'classes': CLASSES, 'retained': len(usable), 'visual_groups': len({r['audit_group'] for r in usable}),
               'excluded': len(excluded), 'invalid': len(invalid),
               'counts': {s: dict(Counter(r['class_name'] for r in usable if r['split'] == s)) for s in ['train','val','test']},
               'group_counts': {s: dict(Counter(r['class_name'] for r in {r['audit_group']: r for r in usable if r['split'] == s}.values())) for s in ['train','val','test']},
               'scope': 'Visible external signs only; labels are not confirmed pathogen diagnoses.',
               'limitations': ['Small internet-sourced cohort; no farm or subject identities.',
                              'Manual visual grouping reduces obvious overlaps but cannot exclude all same-case images.',
                              'Commons controls are not clinically verified healthy birds.',
                              'Scab/nodule images are heavily overrepresented; unknown is not exhaustive.',
                              'Dataset annotation mistakes were found and quarantined; remaining labels are unverified.']}
    save(OUT / 'manifest.json', usable); save(OUT / 'summary.json', summary)
    save(OUT / 'excluded.json', excluded); save(OUT / 'invalid.json', invalid)
    save(REPORT / 'body_data_audit.json', summary)
    print('BODY_DATA', json.dumps(summary), flush=True)
    return usable


class Images(Dataset):
    def __init__(self, rows, training=False):
        self.rows = rows
        self.transform = transforms.Compose([transforms.Resize((224,224)),
            *([transforms.RandomHorizontalFlip(), transforms.RandomRotation(8),
               transforms.ColorJitter(brightness=.12, contrast=.12)] if training else []),
            transforms.ToTensor(), transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
    def __len__(self): return len(self.rows)
    def __getitem__(self, i):
        r = self.rows[i]
        with Image.open(ROOT/r['image_path']) as source:
            x = self.transform(ImageOps.exif_transpose(source).convert('RGB'))
        return x, r['label']


def train(rows):
    torch.set_num_threads(4)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    validation = [r for r in rows if r['split']=='val']
    test = [r for r in rows if r['split']=='test']
    training = [r for r in rows if r['split']=='train']
    @torch.inference_mode()
    def evaluate(model, subset):
        model.eval(); ys=[]; probabilities=[]
        for x,y in DataLoader(Images(subset),batch_size=48):
            ys.extend(y.tolist()); probabilities.extend(model(x.to(device)).softmax(1).cpu().tolist())
        ps = np.argmax(probabilities,axis=1).tolist()
        m = metrics(ys,ps,CLASSES)
        m['correct'] = sum(a==b for a,b in zip(ys,ps)); m['n']=len(ys)
        return m,[{**r,'prediction':CLASSES[p],'scores':v} for r,p,v in zip(subset,ps,probabilities)]
    records=[]
    for seed in [42,17]:
        directory=ROOT/'models'/f'chicken_body_v1_seed{seed}'
        if (directory/'validation.json').exists():
            records.append(json.loads((directory/'validation.json').read_text()));continue
        directory.mkdir(exist_ok=True)
        random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
        model=models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        model.fc=nn.Linear(model.fc.in_features,len(CLASSES));model.to(device)
        for p in model.parameters():p.requires_grad=False
        for layer in [model.layer4,model.fc]:
            for p in layer.parameters():p.requires_grad=True
        optimizer=torch.optim.AdamW([{'params':model.layer4.parameters(),'lr':1e-4},
                                     {'params':model.fc.parameters(),'lr':4e-4}],weight_decay=.02)
        counts=Counter(r['class_name'] for r in training)
        sampler=WeightedRandomSampler([1/counts[r['class_name']] for r in training],max(240,len(training)),replacement=True)
        loader=DataLoader(Images(training,True),batch_size=24,sampler=sampler)
        criterion=nn.CrossEntropyLoss(label_smoothing=.06)
        history=[];best=-1;stale=0
        for epoch in range(1,41):
            model.eval();loss_sum=0
            for x,y in loader:
                optimizer.zero_grad(set_to_none=True);loss=criterion(model(x.to(device)),y.to(device))
                loss.backward();optimizer.step();loss_sum+=loss.item()*len(y)
            val,_=evaluate(model,validation);score=val['macro_f1']
            history.append({'epoch':epoch,'loss':loss_sum/len(sampler),'validation':val})
            if score>best:
                best=score;stale=0
                torch.save({'architecture':'resnet18','state_dict':model.state_dict(),'classes':CLASSES,
                            'mean':[.485,.456,.406],'std':[.229,.224,.225],'epoch':epoch,'seed':seed,
                            'species':'chicken','input_type':'body','scope':'external_signs_not_pathogen_diagnosis',
                            'training_manifest':(OUT/'manifest.json').relative_to(ROOT).as_posix(),
                            'manifest_sha256':hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest(),
                            'license':'AGPL-3.0'},directory/'best.pt')
            else:stale+=1
            print('BODY_EPOCH',seed,epoch,'F1',round(score,4),'recall',json.dumps({k:round(v['recall'],3) for k,v in val['per_class'].items()}),flush=True)
            if stale>=8:break
        ck=torch.load(directory/'best.pt',map_location=device,weights_only=True);model.load_state_dict(ck['state_dict'])
        val,p=evaluate(model,validation)
        record={'seed':seed,'epoch':ck['epoch'],'validation':val,'checkpoint':(directory/'best.pt').relative_to(ROOT).as_posix()}
        save(directory/'history.json',history);save(directory/'validation_predictions.json',p);save(directory/'validation.json',record)
        records.append(record);del model
    chosen=max(records,key=lambda r:r['validation']['macro_f1'])
    save(REPORT/'body_selection_before_test.json',{'chosen':chosen,'candidates':records,'test_used_for_selection':False})
    from web.model_factory import from_checkpoint
    ck=torch.load(ROOT/chosen['checkpoint'],map_location='cpu',weights_only=True)
    model=from_checkpoint(ck).to(device)
    m,p=evaluate(model,test)
    val=chosen['validation']
    eligible=bool(val['macro_f1']>=.7 and all(v['recall']>=.5 and v['support']>=2 for v in val['per_class'].values())
                  and val['per_class']['unknown']['recall']>=.75)
    # The single held-out check may reject a release; no test-driven training retries.
    guard=bool(m['macro_f1']>=.65 and m['per_class']['unknown']['recall']>=.7)
    report={'classes':CLASSES,'names':NAMES,'validation':val,'test':m,'checkpoint':chosen['checkpoint'],
            'validation_gate':eligible,'final_regression_guard':guard,'eligible_for_web':eligible and guard,
            'scope':'external_signs_only_not_disease_diagnosis','test_used_for_tuning':False,
            'limitations':json.loads((OUT/'summary.json').read_text())['limitations']}
    save(REPORT/'body_training.json',report);save((ROOT/chosen['checkpoint']).parent/'metrics.json',report)
    save((ROOT/chosen['checkpoint']).parent/'test_predictions.json',p)
    print('BODY_COMPLETE',json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    rows=prepare()
    if not args.prepare_only:train(rows)
