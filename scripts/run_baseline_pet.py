#!/usr/bin/env python3
"""Baseline: run PET/isl polyhedral verifier on all 28,800 samples.
Uses python3.13 subprocess for correct PET/isl environment.
Reports parseable rate, precision, recall, and per-category recall.
"""
import json, os, signal, subprocess, sys, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

REPO = Path(__file__).resolve().parent.parent
# PolyBench utilities path (set PB_UTILS env var)
PB_UTILS = Path(os.environ.get("PB_UTILS", str(VEGG / "PolyBenchC-4.2.1" / "utilities")))
SRC_DIR = str(REPO / "src")


def check_one(args):
    ref_path, sample_path, gt_correct, transform = args

    # Build include dirs
    all_incs = [str(PB_UTILS.resolve())]
    kernel_name = Path(ref_path).parent.name
    pb_root = PB_UTILS.resolve().parent if PB_UTILS.resolve().name == "utilities" else PB_UTILS.resolve()
    for hdr in pb_root.rglob(f"{kernel_name}.h"):
        all_incs.append(str(hdr.parent))
        break

    script = "\n".join([
        f"import sys; sys.path.insert(0, '{SRC_DIR}')",
        "from pathlib import Path",
        "from legvo.polyhedral.extract import extract_scop",
        "from legvo.polyhedral.verify import verify as pv",
        f"incs = {all_incs}",
        f"ref = extract_scop(Path('{ref_path}'), include_dirs=[Path(p) for p in incs])",
        "if ref is None: print('PARSE_FAIL_REF'); exit(0)",
        f"cand = extract_scop(Path('{sample_path}'), include_dirs=[Path(p) for p in incs])",
        "if cand is None: print('PARSE_FAIL_CAND'); exit(0)",
        "print('PARSED')",
        "r = pv(ref, cand)",
        "if r.status == 'equivalent': print('EQUIVALENT')",
        "else: print('UNKNOWN')",
    ])

    try:
        proc = subprocess.run(
            ["python3.13", "-c", script],
            capture_output=True, text=True, timeout=15,
            cwd=str(REPO),
        )
        output = proc.stdout.strip()
        lines = output.split("\n")
        parsed = "PARSED" in lines
        proved_eq = "EQUIVALENT" in lines
    except (subprocess.TimeoutExpired, FileNotFoundError):
        parsed = False
        proved_eq = False

    return (proved_eq, gt_correct, parsed, transform)


def main():
    gt = json.load(open(REPO / "datasets/single_transform_full/ground_truth.json"))
    ds = REPO / "datasets/single_transform_full"

    # Category mapping
    cat_map = {}
    expr_types = {"expr_comm_add","expr_comm_mul","expr_add_zero","expr_mul_one",
                  "expr_assoc_add","expr_distrib","expr_neg_distribute",
                  "expr_reorder_terms","expr_self_sub","expr_strength_reduce",
                  "expr_sub_cancel","expr_zero_mul"}
    loop_types = {"loop_fission","loop_fusion","loop_interchange","loop_init_hoist",
                  "loop_peel_first","loop_peel_last","loop_shift","loop_guard_add"}
    stmt_types = {"stmt_combine","stmt_reorder","stmt_scalar_replace","stmt_split"}
    syn_types  = {"syn_add_braces","syn_remove_braces","syn_whitespace","syn_var_rename",
                  "syn_type_cast","syn_paren_add","syn_scalar_val","syn_add_comment"}
    for t in expr_types: cat_map[t] = "Expression"
    for t in loop_types: cat_map[t] = "Loop"
    for t in stmt_types: cat_map[t] = "Statement"
    for t in syn_types:  cat_map[t] = "Syntactic"

    tasks = []
    for td in sorted(ds.iterdir()):
        if not td.is_dir(): continue
        for kd in sorted(td.iterdir()):
            if not kd.is_dir(): continue
            ref = kd / "reference.c"
            if not ref.exists(): continue
            for s in sorted(kd.glob("sample_*.c")):
                num = s.stem.replace("sample_", "")
                gk = f"{td.name}/{kd.name}/s{num}"
                if gk not in gt: continue
                tasks.append((str(ref), str(s), gt[gk] == "correct", td.name))

    print(f"Total samples: {len(tasks)}")
    tp = fp = fn = tn = 0
    parsed_count = 0
    cat_tp = defaultdict(int)
    cat_total_correct = defaultdict(int)

    start = time.time()
    done = 0
    with ProcessPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(check_one, t): t for t in tasks}
        for f in as_completed(futures):
            proved_eq, gc, parsed, transform = f.result()
            cat = cat_map.get(transform, "Unknown")
            if parsed:
                parsed_count += 1
            if proved_eq and gc:
                tp += 1; cat_tp[cat] += 1
            elif proved_eq and not gc:
                fp += 1
            elif not proved_eq and gc:
                fn += 1
            else:
                tn += 1
            if gc:
                cat_total_correct[cat] += 1
            done += 1
            if done % 2000 == 0:
                elapsed = time.time() - start
                print(f"  {done}/{len(tasks)} done ({elapsed:.0f}s)", flush=True)

    elapsed = time.time() - start
    total = tp + fp + fn + tn
    acc  = 100 * (tp + tn) / total
    prec = 100 * tp / (tp + fp) if (tp + fp) > 0 else 0
    rec  = 100 * tp / (tp + fn) if (tp + fn) > 0 else 0
    parseable = 100 * parsed_count / total

    print(f"\n=== PET/isl Baseline Results ===")
    print(f"Completed in {elapsed:.0f}s")
    print(f"Parseable: {parsed_count}/{total} = {parseable:.1f}%")
    print(f"TP={tp}  TN={tn}  FP={fp}  FN={fn}")
    print(f"Accuracy={acc:.1f}%  Precision={prec:.1f}%  Recall={rec:.1f}%")
    print(f"\n=== Per-Category Recall ===")
    for cat in ["Expression", "Loop", "Statement", "Syntactic"]:
        t = cat_total_correct[cat]
        r = cat_tp[cat]
        pct = 100 * r / t if t > 0 else 0
        print(f"  {cat:12s}: {r}/{t} = {pct:.1f}%")


if __name__ == "__main__":
    main()
