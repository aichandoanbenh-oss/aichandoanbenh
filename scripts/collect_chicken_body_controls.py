"""Collect attributed Commons chicken photos as unknown controls, not healthy diagnoses."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import time

from PIL import Image
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/raw/chicken_body_controls'
REPORT = ROOT / 'reports/improvement_20261113'
HEADERS = {'User-Agent': 'VetLensResearch/1.0 (local dataset audit)'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = json.loads((REPORT / 'body_commons_categories.json').read_text(encoding='utf-8'))
    candidates = []
    for category, result in source:
        for page in result.get('query', {}).get('pages', {}).values():
            if not page['title'].lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue
            info = page['imageinfo'][0]
            meta = info.get('extmetadata', {})
            license_name = meta.get('LicenseShortName', {}).get('value', '')
            if not any(v in license_name for v in ['CC BY', 'CC0', 'Public domain']):
                continue
            candidates.append({'title': page['title'], 'url': info.get('thumburl', info['url']),
                               'source_url': info.get('descriptionurl'), 'license': license_name,
                               'license_url': meta.get('LicenseUrl', {}).get('value', ''),
                               'artist': re.sub('<[^>]+>', '', meta.get('Artist', {}).get('value', 'unknown')),
                               'description': re.sub('<[^>]+>', '', meta.get('ImageDescription', {}).get('value', '')),
                               'control_label': 'unknown_not_clinically_examined'})
    def fetch(row):
        name = hashlib.sha256(row['title'].encode()).hexdigest()[:20]
        path = OUT / (name + '.jpg')
        if not path.exists():
            for attempt in range(3):
                try:
                    r = requests.get(row['url'], headers=HEADERS, timeout=(20, 35))
                    r.raise_for_status()
                    import io
                    with Image.open(io.BytesIO(r.content)) as im:
                        im.convert('RGB').save(path, quality=96)
                    break
                except (requests.RequestException, OSError):
                    if attempt == 2:
                        return {**row, 'error': 'download_failed'}
                    time.sleep(2)
        return {**row, 'image_path': path.relative_to(ROOT).as_posix()}
    with ThreadPoolExecutor(5) as pool:
        rows = list(pool.map(fetch, candidates))
    (OUT / 'manifest.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print('CONTROLS', sum('error' not in r for r in rows), '/', len(rows), flush=True)


if __name__ == '__main__':
    main()
