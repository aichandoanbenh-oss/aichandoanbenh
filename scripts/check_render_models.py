"""Fail deployment early when selected checkpoints are missing."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'models_catalog.json').read_text(encoding='utf-8'))
for species in ['dog','cattle','pig','chicken']:
    item=catalog[species];path=root/item.get('web_checkpoint',item['checkpoint'])
    if not path.exists() or path.stat().st_size<1024*1024:
        raise SystemExit(f'Missing checkpoint: {path.relative_to(root)}. See RENDER_PWA.md.')
    if path.read_bytes()[:40].startswith(b'version https://git-lfs'):
        raise SystemExit(f'Git LFS pointer instead of model: {path}')
    print(f'{species}: {path.stat().st_size/1024**2:.1f} MiB')
