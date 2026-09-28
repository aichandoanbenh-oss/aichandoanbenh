"""Verify Python dependencies without training or modifying model weights."""
import importlib,json,sys
from pathlib import Path
modules=['torch','torchvision','numpy','PIL','fastapi','uvicorn','multipart','requests','bs4','gdown','matplotlib','docx','onnx','onnxruntime','playwright.sync_api','httpx']
failed=[]
for name in modules:
    try:importlib.import_module(name);print('OK',name)
    except Exception as e:failed.append(name);print('FAIL',name,str(e))
if failed:raise SystemExit('Missing/broken dependencies: '+', '.join(failed))
import torch
from torchvision import models
model=models.resnet18(weights=None).eval()
with torch.inference_mode():assert model(torch.zeros(1,3,224,224)).shape==(1,1000)
print('PyTorch/torchvision CPU forward: OK; CUDA:',torch.cuda.is_available())
if '--require-cuda' in sys.argv:
    if not torch.cuda.is_available():raise SystemExit('CUDA unavailable. Update NVIDIA driver or run setup.bat -Device CPU')
    print('CUDA forward allocation:',torch.ones(1,device='cuda').item())
root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'models_catalog.json').read_text(encoding='utf-8'))
missing=[]
for species in ['dog','cattle','pig','chicken']:
    item=catalog[species];p=root/item.get('web_checkpoint',item['checkpoint'])
    if not p.exists():missing.append(str(p.relative_to(root)))
if missing:print('WARNING - libraries are ready but model files are missing:\n'+'\n'.join(missing))
else:print('All four web checkpoint files found.')
