"""Fail deployment early when selected checkpoints are missing."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'models_catalog.json').read_text(encoding='utf-8'))
metadata=json.loads((root/'models/onnx/metadata.json').read_text(encoding='utf-8'))
for key in ['cattle','pig','chicken','chicken_body']:
    path=root/'models/onnx'/f'{key}.onnx'
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=metadata[key]['model_sha256']:
        raise SystemExit(f'Missing or incorrect ONNX model: {key}')
    print(f'{key} ONNX verified')
for species in [s for s,v in catalog.items() if isinstance(v,dict) and 'checkpoint' in v]:
    item=catalog[species]
    entries=[(species,item.get('web_checkpoint',item['checkpoint']))]
    if item.get('body_checkpoint'):entries.append((species+'_body',item['body_checkpoint']))
    for name,relative in entries:
        path=(root/relative).resolve()
        if not path.is_relative_to(root.resolve()):raise SystemExit(f'Invalid checkpoint path: {relative}')
        if not path.exists() or path.stat().st_size<1024*1024:
            raise SystemExit(f'Missing checkpoint: {relative}. See RENDER_PWA.md.')
        with path.open('rb') as handle:prefix=handle.read(40)
        if prefix.startswith(b'version https://git-lfs'):
            raise SystemExit(f'Git LFS pointer instead of model: {path}')
        print(f'{name}: {path.stat().st_size/1024**2:.1f} MiB')
