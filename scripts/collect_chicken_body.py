"""Collect a pinned Evet-Africa revision; retain external signs, exclude organs.

Dataset authors publish AGPL-3.0 and source-level clinical-sign annotations.
No pathogen diagnosis or independently verified clinical ground truth is implied.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/raw/chicken_body_evet'
REPO = 'Evet-Africa/poultry-disease-dataset'
EXTERNAL = {0, 1, 2, 3, 16, 17, 18, 21, 25}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    response = requests.get(f'https://huggingface.co/api/datasets/{REPO}', timeout=30)
    response.raise_for_status()
    source = response.json()
    revision = source['sha']
    (OUT / 'source.json').write_text(json.dumps(source, indent=2), encoding='utf-8')
    response = requests.get(f'https://huggingface.co/api/datasets/{REPO}/tree/{revision}',
                            params={'recursive': 'true', 'limit': 1000}, timeout=30)
    response.raise_for_status()
    tree = response.json()
    (OUT / 'file_inventory.json').write_text(json.dumps(tree, indent=2), encoding='utf-8')
    def fetch(item):
        path = OUT / item['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            url = f'https://huggingface.co/datasets/{REPO}/resolve/{revision}/' + quote(item['path'])
            for attempt in range(3):
                try:
                    r = requests.get(url, timeout=(15, 40))
                    r.raise_for_status()
                    payload = r.content
                    if len(payload) != item['size']:
                        raise ValueError('Unexpected file size: ' + item['path'])
                    if item.get('lfs') and hashlib.sha256(payload).hexdigest() != item['lfs']['oid']:
                        raise ValueError('Source hash mismatch')
                    path.write_bytes(payload)
                    break
                except (requests.RequestException, ValueError):
                    if attempt == 2:
                        raise
                    time.sleep(2)
        return item['path']
    labels = [d for d in tree if d['type'] == 'file' and (d['path'].startswith('labels/') or d['path'] in {'README.md', 'dataset.yaml'})]
    with ThreadPoolExecutor(8) as pool:
        for i, _ in enumerate(pool.map(fetch, labels)):
            if i % 100 == 0:
                print('LABELS', i, '/', len(labels), flush=True)
    by_stem = {Path(d['path']).stem: d for d in tree if d['type'] == 'file' and d['path'].startswith('images/')}
    included, excluded = [], []
    for item in labels:
        if not item['path'].startswith('labels/'):
            continue
        annotation = (OUT / item['path']).read_text(encoding='utf-8').strip().splitlines()
        ids = sorted({int(line.split()[0]) for line in annotation if line.strip()})
        image = by_stem.get(Path(item['path']).stem)
        if image is None:
            excluded.append({'annotation': item['path'], 'reason': 'missing_image'})
            continue
        row = {'image': image, 'annotation_path': item['path'], 'class_ids': ids,
               'source_repo': REPO, 'revision': revision, 'license': 'AGPL-3.0',
               'source_url': f'https://huggingface.co/datasets/{REPO}/blob/{revision}/' + image['path']}
        if not ids or not set(ids).issubset(EXTERNAL):
            excluded.append({**row, 'reason': 'internal_organ_or_mixed_panel_annotation'})
        else:
            included.append(row)
    with ThreadPoolExecutor(6) as pool:
        for i, _ in enumerate(pool.map(fetch, [r['image'] for r in included])):
            if i % 40 == 0:
                print('EXTERNAL_IMAGES', i, '/', len(included), flush=True)
    (OUT / 'external_candidates.json').write_text(json.dumps(included, indent=2), encoding='utf-8')
    (OUT / 'excluded.json').write_text(json.dumps(excluded, indent=2), encoding='utf-8')
    from collections import Counter
    print('COLLECTED', len(included), 'EXCLUDED', len(excluded), 'SIGNS', dict(Counter(i for r in included for i in r['class_ids'])), flush=True)


if __name__ == '__main__':
    main()
