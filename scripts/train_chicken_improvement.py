"""Domain-balanced fine tuning; validation selects candidates, test runs once.

No catalog mutation happens here. Supports resumable evaluation of completed runs.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import numpy as np
from PIL import Image
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web.model_factory import from_checkpoint
from train_available import metrics
from prepare_chicken_improvement import CLASSES, OUT as DATA, REPORT, save


class CachedImages(Dataset):
    def __init__(self, rows):
        self.rows = rows
        def read(row):
            with Image.open(ROOT / row['image_path']) as im:
                return torch.from_numpy(np.asarray(im.convert('RGB')).copy()).permute(2, 0, 1)
        with ThreadPoolExecutor(6) as pool:
            self.images = list(pool.map(read, rows))
    def __len__(self):
        return len(self.rows)
    def __getitem__(self, index):
        return self.images[index], self.rows[index]['label'], index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=14)
    parser.add_argument('--seeds', type=int, nargs='+', default=[42, 17])
    parser.add_argument('--evaluate', action='store_true')
    args = parser.parse_args()
    torch.set_num_threads(4)
    if not torch.cuda.is_available():
        raise RuntimeError('This training run requires the available CUDA GPU.')
    device = torch.device('cuda')
    torch.backends.cudnn.benchmark = True
    manifest = DATA / 'manifest.json'
    rows = json.loads(manifest.read_text(encoding='utf-8'))
    catalog = json.loads((ROOT / 'models_catalog.json').read_text(encoding='utf-8'))
    initial_path = ROOT / catalog['chicken']['web_checkpoint']
    snapshot = REPORT / 'catalog_before_training.json'
    if not snapshot.exists():
        save(snapshot, catalog)
    else:
        initial_path = ROOT / json.loads(snapshot.read_text(encoding='utf-8'))['chicken']['web_checkpoint']
    ck = torch.load(initial_path, map_location='cpu', weights_only=True)
    assert ck['classes'] == CLASSES, ck['classes']
    mean = torch.tensor(ck['mean'], device=device).view(1, 3, 1, 1)
    std = torch.tensor(ck['std'], device=device).view(1, 3, 1, 1)
    datasets = {s: CachedImages([r for r in rows if r['split'] == s]) for s in ['train', 'val', 'test']}
    print('CACHE_READY', {s: len(d) for s, d in datasets.items()}, flush=True)
    loaders = {s: DataLoader(d, batch_size=96, num_workers=0, pin_memory=True) for s, d in datasets.items() if s != 'train'}
    def normalize(x):
        return (x.to(device, non_blocking=True).float().div_(255) - mean) / std

    @torch.inference_mode()
    def assess(model, split):
        model.eval()
        ys, probs, indices = [], [], []
        for x, y, index in loaders[split]:
            p = model(normalize(x)).softmax(1).cpu()
            ys.extend(y.tolist()); probs.extend(p.tolist()); indices.extend(index.tolist())
        domains = sorted({r['domain'] for r in datasets[split].rows})
        result = {}
        for domain in ['all'] + domains:
            chosen = [i for i, index in enumerate(indices) if domain == 'all' or datasets[split].rows[index]['domain'] == domain]
            if not chosen:
                continue
            report = metrics([ys[i] for i in chosen], [int(np.argmax(probs[i])) for i in chosen], CLASSES)
            present = [v['f1'] for v in report['per_class'].values() if v['support']]
            report['macro_f1_present_classes'] = sum(present) / len(present)
            report['n'] = len(chosen)
            result[domain] = report
        predictions = [{**datasets[split].rows[index], 'prediction': CLASSES[int(np.argmax(p))],
                        'scores': p} for index, p in zip(indices, probs)]
        return result, predictions

    baseline = from_checkpoint(ck).to(device)
    baseline_val, _ = assess(baseline, 'val')
    save(REPORT / 'baseline_validation.json', baseline_val)
    print('BASELINE_VAL', json.dumps({d: (m['accuracy'], m['macro_f1_present_classes']) for d, m in baseline_val.items()}), flush=True)
    del baseline
    torch.cuda.empty_cache()
    def objective(result):
        # Protect legacy performance, but require improvement across classes in the new domain.
        return (.55 * result['legacy']['macro_f1_present_classes']
                + .40 * result['cfid_bangladesh']['macro_f1_present_classes']
                + .05 * result.get('body_input_rejection', result['legacy'])['macro_f1_present_classes'])
    def eligible(result):
        return (result['legacy']['macro_f1_present_classes'] >= baseline_val['legacy']['macro_f1_present_classes'] - .01
                and result['cfid_bangladesh']['macro_f1_present_classes'] > baseline_val['cfid_bangladesh']['macro_f1_present_classes'] + .01)
    candidates = []
    for seed in args.seeds:
        directory = ROOT / 'models' / f'chicken_cfid_v2_seed{seed}'
        complete = directory / 'validation.json'
        if complete.exists():
            candidates.append(json.loads(complete.read_text(encoding='utf-8')))
            continue
        if args.evaluate:
            raise RuntimeError('Unfinished training: ' + str(directory))
        directory.mkdir(exist_ok=True)
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
        model = from_checkpoint(ck).to(device)
        for parameter in model.parameters():
            parameter.requires_grad = False
        for layer in [model.layer3, model.layer4, model.fc]:
            for parameter in layer.parameters():
                parameter.requires_grad = True
        optimizer = torch.optim.AdamW([
            {'params': model.layer3.parameters(), 'lr': 1e-5},
            {'params': model.layer4.parameters(), 'lr': 3e-5},
            {'params': model.fc.parameters(), 'lr': 6e-5}], weight_decay=.01)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=2e-6)
        train_rows = datasets['train'].rows
        cells = Counter((r['domain'], r['class_name']) for r in train_rows)
        # Give each source/class meaningful representation without an inverse-frequency explosion.
        source_mass = {'legacy': .65, 'cfid_bangladesh': .30, 'body_input_rejection': .05}
        class_counts = Counter(r['domain'] for r in train_rows)
        cells_per_domain = Counter(domain for domain, label in cells)
        weights = [source_mass[r['domain']] / cells_per_domain[r['domain']] / cells[r['domain'], r['class_name']]
                   for r in train_rows]
        generator = torch.Generator().manual_seed(seed)
        loader = DataLoader(datasets['train'], batch_size=64, num_workers=0, pin_memory=True,
                            sampler=WeightedRandomSampler(weights, len(train_rows), generator=generator))
        crop = transforms.RandomResizedCrop((224, 224), scale=(.78, 1), ratio=(.9, 1.1), antialias=True)
        criterion = nn.CrossEntropyLoss(label_smoothing=.03)
        scaler = torch.amp.GradScaler('cuda')
        best = -1; stale = 0; history = []
        for epoch in range(1, args.epochs + 1):
            started = time.monotonic()
            # Keep batch-normalization running statistics fixed across mixed input domains.
            model.eval()
            total = 0
            for x, y, _ in loader:
                x = x.to(device, non_blocking=True).float().div_(255)
                if random.random() < .5:
                    x = x.flip(-1)
                if random.random() < .5:
                    x = x.flip(-2)
                x = crop(x)
                brightness = torch.empty((len(x), 1, 1, 1), device=device).uniform_(.85, 1.15)
                x = ((x * brightness).clamp_(0, 1) - mean) / std
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type='cuda'):
                    loss = criterion(model(x), y.to(device))
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 5)
                scaler.step(optimizer); scaler.update()
                total += loss.item() * len(y)
            scheduler.step()
            result, _ = assess(model, 'val')
            score = objective(result)
            entry = {'epoch': epoch, 'loss': total / len(train_rows), 'objective': score,
                     'eligible': eligible(result), 'validation': result, 'seconds': time.monotonic() - started}
            history.append(entry)
            # Any eligible checkpoint outranks ineligible checkpoints; then compare the fixed objective.
            rank = score + (2 if eligible(result) else 0)
            if rank > best:
                best = rank; stale = 0
                updated = {**ck, 'state_dict': model.state_dict(), 'epoch': epoch, 'seed': seed,
                           'training_manifest': manifest.relative_to(ROOT).as_posix(),
                           'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
                           'initial_checkpoint': initial_path.relative_to(ROOT).as_posix(),
                           'scope': 'fecal_images_only_multidomain_experimental'}
                torch.save(updated, directory / 'best.pt')
            else:
                stale += 1
            save(directory / 'history.json', history)
            print('EPOCH', seed, epoch, 'loss', round(entry['loss'], 4), 'seconds', round(entry['seconds']),
                  'eligible', eligible(result), 'val', json.dumps({d: round(m['macro_f1_present_classes'], 4) for d, m in result.items()}), flush=True)
            if stale >= 5:
                break
        selected = torch.load(directory / 'best.pt', map_location='cpu', weights_only=True)
        model.load_state_dict(selected['state_dict'])
        result, predictions = assess(model, 'val')
        record = {'seed': seed, 'epoch': selected['epoch'], 'objective': objective(result),
                  'eligible': eligible(result), 'validation': result,
                  'checkpoint': (directory / 'best.pt').relative_to(ROOT).as_posix()}
        save(directory / 'validation_predictions.json', predictions)
        save(complete, record)
        candidates.append(record)
        del model
        torch.cuda.empty_cache()
    chosen = max(candidates, key=lambda r: (r['eligible'], r['objective']))
    save(REPORT / 'selection_before_test.json', {'chosen': chosen, 'candidates': candidates,
                                              'baseline_validation': baseline_val, 'test_used_for_selection': False})
    # Tests are evaluated only after checkpoint/seed selection has been recorded.
    for name, checkpoint in [('baseline', initial_path), ('candidate', ROOT / chosen['checkpoint'])]:
        model = from_checkpoint(torch.load(checkpoint, map_location='cpu', weights_only=True)).to(device)
        result, predictions = assess(model, 'test')
        save(REPORT / (name + '_test.json'), result)
        save(REPORT / (name + '_test_predictions.json'), predictions)
        print('TEST', name, json.dumps({d: (m['accuracy'], m['macro_f1_present_classes'], m['n']) for d, m in result.items()}), flush=True)
        del model
        torch.cuda.empty_cache()
    print('TRAINING_COMPLETE', chosen['checkpoint'], 'eligible', chosen['eligible'], flush=True)


if __name__ == '__main__':
    main()
