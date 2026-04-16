#!/bin/bash
# Verify command for autoresearch: outputs accuracy % as a single number
# Uses multiprocessing for speed (~20 workers), 30s timeout per case
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"
# Default: PolyBenchC at ../vegg/PolyBenchC-4.2.1 (sibling workspace)
# PolyBench path from environment
if [ -z "$PB_UTILS" ]; then echo "Error: set PB_UTILS=/path/to/PolyBenchC-4.2.1/utilities"; exit 1; fi
PYTHONPATH=src python3 -u -c "
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
import json, signal

dataset = Path('datasets/single_transform_full')
with open(dataset / 'ground_truth.json') as f:
    gt = json.load(f)

INCS = [Path(os.environ['PB_UTILS'])]
PER_CASE_TIMEOUT = 45  # seconds

def check_one(args):
    ref_path, sample_path, gt_is_correct = args
    # Per-process timeout via alarm
    def handler(signum, frame):
        raise TimeoutError('case timeout')
    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(PER_CASE_TIMEOUT)
    try:
        from legvo.egraph.verify import verify
        result = verify(Path(ref_path), Path(sample_path), include_dirs=INCS)
        proved_eq = result.status == 'equivalent'
    except:
        proved_eq = False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
    return 1 if (proved_eq == gt_is_correct) else 0

# Build task list
tasks = []
for transform_dir in sorted(dataset.iterdir()):
    if not transform_dir.is_dir(): continue
    for kernel_dir in sorted(transform_dir.iterdir()):
        if not kernel_dir.is_dir(): continue
        ref = kernel_dir / 'reference.c'
        if not ref.exists(): continue
        for sample in sorted(kernel_dir.glob('sample_*.c')):
            num = sample.stem.replace('sample_', '')
            gt_key = f'{transform_dir.name}/{kernel_dir.name}/s{num}'
            if gt_key not in gt: continue
            gt_is_correct = (gt[gt_key] == 'correct')
            tasks.append((str(ref), str(sample), gt_is_correct))

correct = 0
total = len(tasks)
timed_out = 0
with ProcessPoolExecutor(max_workers=20) as pool:
    futures = {pool.submit(check_one, t): t for t in tasks}
    for f in as_completed(futures, timeout=600):
        try:
            correct += f.result(timeout=60)
        except:
            timed_out += 1

accuracy = 100 * correct / total if total else 0
import sys
if timed_out:
    print(f'{accuracy:.1f} ({timed_out} timed out)', file=sys.stderr)
print(f'{accuracy:.1f}')
" 2>&1 | tail -1
