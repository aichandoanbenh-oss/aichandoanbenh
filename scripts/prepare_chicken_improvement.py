"""Audit originals across sources before splitting a new CFID domain cohort.

Old split assignments are retained. Conflicting labels and groups spanning old
splits are quarantined; no augmented export of CFID is used.
"""
import hashlib
import json
import random
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/chicken_cfid_v2'
REPORT = ROOT / 'reports/improvement_20261113'
CLASSES = ['Coccidiosis', 'Healthy', 'New Castle Disease', 'Salmonella', 'unknown']


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def dhash(im):
    a = np.asarray(im.convert('L').resize((9, 8)), dtype=np.int16)
    return int.from_bytes(np.packbits((a[:, 1:] > a[:, :-1]).ravel()).tobytes(), 'big')


def describe(row):
    try:
        with Image.open(ROOT / row['image_path']) as source:
            source.load()
            im = ImageOps.exif_transpose(source).convert('RGB')
        if min(im.size) < 32 or im.width * im.height > 30_000_000:
            raise ValueError('image_size_out_of_range')
        row['width'], row['height'] = im.size
        row['sha224'] = hashlib.sha256(im.resize((224, 224)).tobytes()).hexdigest()
        im.thumbnail((320, 320))
        views = [im] + [im.transpose(op) for op in Image.Transpose]
        row['hashes'] = [dhash(v) for v in views]
        # DCT-based pHash verifies the cheap dHash candidates; it is not a label check.
        coords = np.arange(32)
        dct = np.cos(np.pi * (2 * coords[None, :] + 1) * coords[:, None] / 64)
        phashes = []
        for v in views:
            a = np.asarray(v.convert('L').resize((32, 32)), dtype=float)
            low = (dct @ a @ dct.T)[:8, :8].ravel()[1:]
            phashes.append(int.from_bytes(np.packbits(low > np.median(low)).tobytes(), 'big'))
        row['phashes'] = phashes
        return row
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        return {**row, 'error': str(exc)}


def main():
    if (OUT / 'manifest.json').exists():
        raise RuntimeError('Prepared version already exists; use a new output version.')
    rows = json.loads((ROOT / 'data/processed/chicken_user_update_v1/manifest.json').read_text(encoding='utf-8'))
    for row in rows:
        row['domain'] = 'legacy'
        name = Path(row['image_path']).name
        row['annotation'] = 'source_reported_PCR' if name.startswith('pcr') else 'inherited_public_label'
        if row.get('origin') == 'user_added':
            # Only input suitability is supervised here, not unverified body-image disease labels.
            row['original_class_name'] = row['class_name']
            row['class_name'] = 'unknown'
            row['domain'] = 'body_input_rejection'
            row['annotation'] = 'outside_fecal_input_scope_not_disease_relabel'
    originals = ROOT / 'data/raw/chicken_cfid_2026/OriginalDataset'
    if not originals.exists():
        raise RuntimeError('Download CFID originals first.')
    for path in sorted(originals.rglob('*')):
        if path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
            continue
        parts = '/'.join(path.relative_to(originals).parts).lower()
        label = ('Coccidiosis' if 'cocci' in parts else 'New Castle Disease' if 'newcastle' in parts or 'new castle' in parts
                 else 'Salmonella' if 'salmo' in parts else 'Healthy' if 'healthy' in parts else None)
        if label is None:
            raise ValueError('Unknown CFID class: ' + str(path))
        rows.append({'image_path': path.relative_to(ROOT).as_posix(), 'class_name': label,
                     'domain': 'cfid_bangladesh', 'split': 'unassigned',
                     'annotation': 'veterinarian_review_as_reported_by_CFID_authors',
                     'source_doi': '10.5281/zenodo.21416675', 'license': 'CC-BY-4.0'})
    raw_counts = Counter((r['domain'], r['class_name']) for r in rows)
    described = []
    with ThreadPoolExecutor(6) as pool:
        for i, row in enumerate(pool.map(describe, rows)):
            described.append(row)
            if i % 1000 == 0:
                print('AUDIT', i, '/', len(rows), flush=True)
    invalid = [r for r in described if 'error' in r]
    rows = [r for r in described if 'error' not in r]
    parent = list(range(len(rows)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        parent[find(j)] = find(i)
    pixels, groups, buckets = {}, {}, defaultdict(list)
    for i, row in enumerate(rows):
        h = row['sha224']
        if h in pixels:
            union(i, pixels[h])
        else:
            pixels[h] = i
        if row.get('source_group'):
            key = row['source_group']
            if key in groups:
                union(i, groups[key])
            groups[key] = i
        candidates = set()
        h = row['hashes'][0]
        for shift, width in [(0, 13), (13, 13), (26, 13), (39, 13), (52, 12)]:
            candidates.update(buckets[(shift, (h >> shift) & ((1 << width) - 1))])
        for j, view in candidates:
            if (h ^ rows[j]['hashes'][view]).bit_count() <= 4 and (row['phashes'][0] ^ rows[j]['phashes'][view]).bit_count() <= 8:
                union(i, j)
        for view, h in enumerate(row['hashes']):
            for shift, width in [(0, 13), (13, 13), (26, 13), (39, 13), (52, 12)]:
                buckets[(shift, (h >> shift) & ((1 << width) - 1))].append((i, view))
    components = defaultdict(list)
    for i, row in enumerate(rows):
        components[find(i)].append(row)
    kept, quarantine, duplicates = [], [], []
    for gid, members in components.items():
        labels = {r['class_name'] for r in members}
        splits = {r['split'] for r in members} - {'unassigned'}
        reason = 'conflicting_source_labels' if len(labels) > 1 else 'preexisting_cross_split_group' if len(splits) > 1 else None
        if reason:
            quarantine.extend({**r, 'reason': reason, 'audit_group': gid} for r in members)
            continue
        representative = members[0]  # Old images precede new ones: preserve existing split membership.
        representative['audit_group'] = gid
        kept.append(representative)
        duplicates.extend({**r, 'reason': 'same_visual_group', 'audit_group': gid,
                           'retained_path': representative['image_path']} for r in members[1:])
    rng = random.Random(20261113)
    for label in CLASSES:
        subset = [r for r in kept if r['domain'] == 'cfid_bangladesh' and r['class_name'] == label]
        rng.shuffle(subset)
        n = len(subset)
        if n and n < 5:
            quarantine.extend({**r, 'reason': 'too_few_new_domain_groups'} for r in subset)
            kept = [r for r in kept if r not in subset]
            continue
        nv = max(1, int(n * .2)) if n else 0
        nt = max(1, int(n * .2)) if n else 0
        for i, row in enumerate(subset):
            row['split'] = 'val' if i < nv else 'test' if i < nv + nt else 'train'
    for row in kept:
        row['label'] = CLASSES.index(row['class_name'])
        # Cache a deterministic resized copy for training speed; normalization remains in the loader.
        dest = OUT / 'images' / (str(row['audit_group']) + '.jpg')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(ROOT / row['image_path']) as im:
            ImageOps.exif_transpose(im).convert('RGB').resize((224, 224)).save(dest, quality=96)
        row['original_path'] = row['image_path']
        row['image_path'] = dest.relative_to(ROOT).as_posix()
    assert len({r['audit_group'] for r in kept}) == len(kept)
    summary = {'classes': CLASSES, 'raw_images': sum(raw_counts.values()), 'retained': len(kept),
               'invalid': len(invalid), 'quarantined': len(quarantine), 'duplicates_removed': len(duplicates),
               'raw_counts': {f'{d}/{c}': n for (d, c), n in raw_counts.items()},
               'split_counts': {f'{domain}/{split}': dict(Counter(r['class_name'] for r in kept if r['domain'] == domain and r['split'] == split))
                                for domain in sorted({r['domain'] for r in kept}) for split in ['train', 'val', 'test']},
               'quarantine_reasons': dict(Counter(r['reason'] for r in quarantine)),
               'new_domain_is_independent': False,
               'limitations': ['CFID includes 41 Kaggle benchmark photos; visual matching is heuristic and residual overlap is possible.',
                               'No farm/animal IDs supplied; visual groups do not establish biological independence.',
                               'CFID labels are veterinarian reviewed as reported by authors, not independently clinically verified here.',
                               'Legacy tests were used in prior development; new-domain test is locked until candidate selection.',
                               'Full-body photos are outside this fecal disease classifier scope.']}
    for name, value in [('manifest', kept), ('summary', summary), ('quarantine', quarantine), ('duplicates', duplicates), ('invalid', invalid)]:
        save(OUT / (name + '.json'), value)
    save(REPORT / 'data_audit.json', summary)
    # Reproducible contact sheets include filenames for human review.
    for label in CLASSES[:-1]:
        samples = [r for r in kept if r['domain'] == 'cfid_bangladesh' and r['class_name'] == label]
        samples = random.Random(9).sample(samples, min(24, len(samples)))
        sheet = Image.new('RGB', (960, 720), 'white')
        draw = ImageDraw.Draw(sheet)
        for i, row in enumerate(samples):
            with Image.open(ROOT / row['image_path']) as im:
                sheet.paste(ImageOps.contain(im, (154, 145)), ((i % 6) * 160, (i // 6) * 180))
            draw.text(((i % 6) * 160, (i // 6) * 180 + 148), str(row['audit_group']), fill='black')
        sheet.save(REPORT / ('cfid_' + label.replace(' ', '_') + '.jpg'))
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
