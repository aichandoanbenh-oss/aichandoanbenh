"""Conservative, reproducible grouping; never modify the raw images."""
import collections
import json
from pathlib import Path
import random
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/raw/cattle_lumpy/extracted'
OUT = ROOT / 'data/processed/cattle_lumpy'

def dhash(im):
    values = list(im.convert('L').resize((9, 8)).getdata())
    return sum((values[y*9+x] > values[y*9+x+1]) << (y*8+x) for y in range(8) for x in range(8))

def main():
    rows = [json.loads(line) for line in (ROOT/'reports/cattle_lumpy_manifest.jsonl').read_text().splitlines()]
    parents = list(range(len(rows)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    def union(i, j):
        parents[find(j)] = find(i)
    variants = []
    for r in rows:
        r['label'] = 0 if r['folder'].endswith('/Normal Skin') else 1
        with Image.open(BASE/r['path']) as im:
            im = im.convert('RGB')
            variants.append([dhash(im)] + [dhash(im.transpose(op)) for op in Image.Transpose])
    matches = []
    for i in range(len(rows)):
        for j in range(i):
            distance = min((variants[i][0] ^ v).bit_count() for v in variants[j])
            if rows[i]['pixel_sha256'] == rows[j]['pixel_sha256'] or distance <= 4:
                union(i,j)
                matches.append({'a':rows[i]['path'], 'b':rows[j]['path'], 'distance':distance})
    groups = collections.defaultdict(list)
    for i,r in enumerate(rows):
        groups[find(i)].append(r)
    quarantine, duplicates, retained = [], [], []
    for group_id, members in groups.items():
        if len({r['label'] for r in members}) > 1:
            quarantine.extend([{**r, 'reason':'conflicting_labels_in_exact_or_near_duplicate_group', 'group':group_id} for r in members])
            continue
        seen = set()
        for r in members:
            r['group'] = group_id
            if r['pixel_sha256'] in seen:
                duplicates.append(r)
            else:
                seen.add(r['pixel_sha256'])
                retained.append(r)
    rng = random.Random(42)
    for label in [0,1]:
        buckets = collections.defaultdict(list)
        for r in retained:
            if r['label'] == label:
                buckets[r['group']].append(r)
        ordered = list(buckets.values())
        rng.shuffle(ordered)
        targets = {'train':0.7*sum(map(len,ordered)), 'val':0.15*sum(map(len,ordered)), 'test':0.15*sum(map(len,ordered))}
        sizes = dict.fromkeys(targets,0)
        for members in sorted(ordered,key=len,reverse=True):
            split = max(targets,key=lambda s:targets[s]-sizes[s])
            for r in members: r['split'] = split
            sizes[split] += len(members)
    # Assert both disjointness constraints, including every detected near-match.
    by_path = {r['path']:r for r in retained}
    for key in ['group','pixel_sha256']:
        assigned = collections.defaultdict(set)
        for r in retained: assigned[r[key]].add(r['split'])
        assert all(len(v)==1 for v in assigned.values())
    for pair in matches:
        if pair['a'] in by_path and pair['b'] in by_path:
            assert by_path[pair['a']]['split'] == by_path[pair['b']]['split']
    counts = {s:dict(collections.Counter(r['label'] for r in retained if r['split']==s)) for s in ['train','val','test']}
    assert all(len(v)==2 for v in counts.values())
    summary = {'seed':42,'classes':['normal_skin','lumpy_skin'],'raw':len(rows),'retained':len(retained),'quarantined':len(quarantine),'exact_duplicates_removed':len(duplicates),'group_count':len({r['group'] for r in retained}),'split_counts':counts,'near_duplicate_method':'dHash 64 bits, Hamming <= 4, all dihedral transforms; connected components','limitations':'No animal/farm IDs; grouping is heuristic and cannot rule out all source leakage.'}
    OUT.mkdir(parents=True,exist_ok=True)
    for name,value in [('manifest',retained),('quarantine',quarantine),('duplicates',duplicates),('near_matches',matches),('summary',summary)]:
        (OUT/(name+'.json')).write_text(json.dumps(value,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)

if __name__ == '__main__': main()
