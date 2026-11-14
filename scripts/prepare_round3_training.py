"""Prepare separate development data while preserving the locked 70-image test."""
import argparse
import concurrent.futures
from collections import Counter,defaultdict
import hashlib
import json
import random
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
from prepare_chicken_improvement import describe

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/training_round3_20261114'
SPECS={'body':('chicken_body_v1','chicken','body_checkpoint'),
       'cattle':('cattle_user_update_v1','cattle','web_checkpoint'),
       'pig':('pig_repair_v4','pig','web_checkpoint')}


def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')


def overlaps(row,others):
    for other in others:
        if row['sha224']==other['sha224']:return other['image_path']
        p=min((row['phashes'][0]^h).bit_count() for h in other['phashes'])
        d=min((row['hashes'][0]^h).bit_count() for h in other['hashes'])
        if p<=12 or (p<=16 and d<=8):return other['image_path']
    return None


def main():
    parser=argparse.ArgumentParser();parser.add_argument('branch',choices=list(SPECS));args=parser.parse_args()
    branch=args.branch;dataset,species,key=SPECS[branch]
    out=ROOT/f'data/processed/round3_{branch}'
    if (out/'manifest.json').exists():raise RuntimeError('Prepared manifest already exists')
    catalog=json.loads((ROOT/'models_catalog.json').read_text(encoding='utf-8'))
    import torch
    checkpoint=catalog[species][key]
    ck=torch.load(ROOT/checkpoint,map_location='cpu',weights_only=True);classes=ck['classes']
    original=json.loads((ROOT/f'data/processed/{dataset}/manifest.json').read_text(encoding='utf-8'))
    index=json.loads((ROOT/'reports/external_round2_20261114/existing_hash_index.json').read_text(encoding='utf-8'))
    hashes={r['image_path']:r for r in index}
    original=[{**r,**{k:v for k,v in hashes[r['image_path']].items() if k in ['sha224','hashes','phashes']}} for r in original]
    locked=json.loads((ROOT/'thaytri/test/manifest.json').read_text(encoding='utf-8'))
    protected=[r for r in original if r['split']=='test']+locked
    excluded=[]
    legacy=[]
    for row in original:
        if row['split']=='test':continue
        match=overlaps(row,locked)
        if match:excluded.append({**row,'reason':'locked_test_overlap','match':match});continue
        legacy.append({**row,'domain':'legacy','development_group':'legacy_'+str(row.get('audit_group',row.get('source_group',row.get('group',row['image_path']))))})
    new=[]
    if branch=='body':
        candidates=json.loads((REPORT/'audited_new_candidates.json').read_text(encoding='utf-8'))
        by_url={r['source_url']:r for r in candidates}
        reviews=json.loads((REPORT/'manual_training_review.json').read_text(encoding='utf-8'))
        for review in reviews:
            row={**by_url[review['source_url']],**review,'domain':'new_external_signs'}
            assert not row.get('exclude')
            # Individual named cases and condition galleries never span splits.
            row['development_group']=row['source_group']
            new.append(row)
        # Cross-linked images from a shared textbook condition are kept together.
        for row in new:
            if '/258/' in row['page_url']:row['development_group']='dinev_swollen_head'
            if '/197/' in row['page_url'] or '/196/' in row['page_url']:
                row['development_group']='dinev_swollen_head_and_laryngotracheitis'
    elif branch=='cattle':
        candidates=json.loads((ROOT/'reports/external_round2_20261114/audited_candidates.json').read_text(encoding='utf-8'))
        for row in candidates:
            if row['branch']!='Bo' or row.get('excluded_existing_duplicate'):continue
            match=overlaps(row,protected)
            if match:excluded.append({**row,'reason':'locked_or_legacy_test_overlap','match':match});continue
            new.append({**row,'domain':'mendeley_field','development_group':row['archive_member']})
    else:
        reviewed=json.loads((REPORT/'pig_manual_review.json').read_text(encoding='utf-8'))
        for row in reviewed:
            if row.get('include'):new.append({**row,'domain':'unsupported_pig_skin','class_name':'unknown','development_group':'unsupported_source_class_'+row['folder']})
    usable=[]
    for row in new:
        match=overlaps(row,protected)
        if match:excluded.append({**row,'reason':'test_overlap','match':match});continue
        if any(row['sha224']==r['sha224'] for r in usable):
            excluded.append({**row,'reason':'new_exact_duplicate'});continue
        usable.append(row)
    # Merge visibly similar new photos before assigning development splits.
    parent=list(range(len(usable)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,row in enumerate(usable):
        for j,other in enumerate(usable[:i]):
            if row['development_group']==other['development_group'] or overlaps(row,[other]):parent[find(i)]=find(j)
    grouped=defaultdict(list)
    for i,row in enumerate(usable):grouped[find(i)].append(row)
    rng=random.Random(20261114)
    # Split whole connected groups; preserve legacy validation assignments.
    group_items=list(grouped.items());rng.shuffle(group_items)
    totals=Counter(r['class_name'] for r in usable)
    targets={c:max(2,round(n*.2)) for c,n in totals.items()}
    val_groups=set();val_counts=Counter()
    for gid,members in group_items:
        labels={r['class_name'] for r in members}
        if any(val_counts[c]<targets[c] for c in labels):
            val_groups.add(gid);val_counts.update(r['class_name'] for r in members)
    for gid,members in group_items:
        for row in members:
            row['split']='val' if gid in val_groups else 'train'
            row['development_group']=f'new_group_{gid}'
    rows=legacy+[r for members in grouped.values() for r in members]
    for row in rows:row['label']=classes.index(row['class_name'])
    # No test row or hash may enter the development manifest.
    assert all(r['split'] in ['train','val'] for r in rows)
    assert not ({r['sha224'] for r in rows}&{r['sha224'] for r in protected})
    manifest=out/'manifest.json';save(manifest,rows)
    summary={'branch':branch,'initial_checkpoint':checkpoint,'classes':classes,
             'counts':{s:dict(Counter(r['class_name'] for r in rows if r['split']==s)) for s in ['train','val']},
             'new_counts':{s:dict(Counter(r['class_name'] for r in rows if r['split']==s and r['domain']!='legacy')) for s in ['train','val']},
             'new_groups':len(grouped),'excluded':len(excluded),'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
             'test_manifest_sha256':hashlib.sha256((ROOT/'thaytri/test/manifest.json').read_bytes()).hexdigest(),
             'limitations':'Source labels / visible signs, no independent clinical diagnosis; heuristic grouping cannot prove animal/farm independence.'}
    save(out/'summary.json',summary);save(out/'excluded.json',excluded)
    print(json.dumps(summary,ensure_ascii=True),flush=True)


if __name__=='__main__':main()
