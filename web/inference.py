"""CPU inference with one resident model and no PyTorch runtime dependency."""
import ctypes
import gc
import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
_cached_key = None
_session = None

def release_memory():
    gc.collect()
    if sys.platform.startswith('linux'):
        trim = getattr(ctypes.CDLL(None), 'malloc_trim', None)
        if trim is not None:
            trim(0)

def infer(species, input_type, image):
    # Caller serializes decoding and inference, including cache replacement.
    global _cached_key, _session
    key = 'chicken_body' if species == 'chicken' and input_type == 'body' else species
    metadata = json.loads((ROOT/'models/onnx/metadata.json').read_text(encoding='utf-8'))[key]
    if _cached_key != key:
        _session = None
        _cached_key = None
        release_memory()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        _session = ort.InferenceSession(str(ROOT/'models/onnx'/f'{key}.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
        _cached_key = key
    # Same Pillow bilinear resize and normalization as torchvision Resize/ToTensor.
    resized = image.resize((224,224), Image.Resampling.BILINEAR)
    array = np.asarray(resized, dtype=np.float32).transpose(2,0,1) / np.float32(255)
    array = (array - np.asarray(metadata['mean'],dtype=np.float32)[:,None,None]) / np.asarray(metadata['std'],dtype=np.float32)[:,None,None]
    logits = _session.run(None, {'image':array[None]})[0][0]
    scores = np.exp(logits-logits.max())
    scores /= scores.sum()
    return metadata['classes'], scores.tolist()
