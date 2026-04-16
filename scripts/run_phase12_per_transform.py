#!/usr/bin/env python3
"""Per-transform recall for primary + finalization passes."""
import json, os, signal, sys, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

REPO = Path(__file__).resolve().parent.parent
# PolyBench utilities path (set PB_UTILS env var)
PB_UTILS = Path(os.environ.get("PB_UTILS", str(REPO / "PolyBenchC-4.2.1" / "utilities")))
INCS = [PB_UTILS]

def check_one(args):
    ref_path, sample_path, gt_correct, transform = args
    def handler(signum, frame):
        raise TimeoutError()
    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(45)
    try:
        from legvo.egraph.verify import (
            _compiles, _find_egglog, _run_egglog_check,
            _polyhedral_facts,
        )
        from legvo.egraph.extract import extract_term
        from legvo.egraph.normalize import normalize_minimal, normalize_aggressive
        ref, cand = Path(ref_path), Path(sample_path)
        if not _compiles(cand, include_dirs=INCS, ref_dir=ref.parent):
            return (False, gt_correct, transform)
        ref_raw = extract_term(ref, include_dirs=INCS)
        cand_raw = extract_term(cand, include_dirs=INCS)
        ref_term = normalize_minimal(ref_raw)
        cand_term = normalize_minimal(cand_raw)
        if ref_term == cand_term:
            return (True, gt_correct, transform)
        egglog_bin = _find_egglog()
        poly_facts = _polyhedral_facts(ref, cand, INCS)
        checks = {}
        r = _run_egglog_check(ref_term, cand_term, egglog_bin, "real",
                              poly_facts, 15, checks, "primary")
        if r.status == "equivalent":
            return (True, gt_correct, transform)
        ref_t2 = normalize_aggressive(ref_raw)
        cand_t2 = normalize_aggressive(cand_raw)
        if ref_t2 != ref_term or cand_t2 != cand_term:
            r2 = _run_egglog_check(ref_t2, cand_t2, egglog_bin, "real",
                                   poly_facts, 6, checks, "finalization")
            if r2.status == "equivalent":
                return (True, gt_correct, transform)
        return (False, gt_correct, transform)
    except:
        return (False, gt_correct, transform)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)

def main():
    gt = json.load(open(REPO / "datasets/single_transform_full/ground_truth.json"))
    ds = REPO / "datasets/single_transform_full"
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
    print(f"Total: {len(tasks)}")
    tp_by = defaultdict(int)
    fp_by = defaultdict(int)
    fn_by = defaultdict(int)
    tn_by = defaultdict(int)
    done = 0
    start = time.time()
    with ProcessPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(check_one, t): t for t in tasks}
        for f in as_completed(futures):
            eq, gc, tr = f.result()
            if eq and gc: tp_by[tr] += 1
            elif eq and not gc: fp_by[tr] += 1
            elif not eq and gc: fn_by[tr] += 1
            else: tn_by[tr] += 1
            done += 1
            if done % 5000 == 0:
                print(f"  {done}/{len(tasks)} ({time.time()-start:.0f}s)", flush=True)
    # Per-category
    cat_map = {}
    for t in ["expr_comm_add","expr_comm_mul","expr_add_zero","expr_mul_one",
              "expr_assoc_add","expr_distrib","expr_neg_distribute",
              "expr_reorder_terms","expr_self_sub","expr_strength_reduce",
              "expr_sub_cancel","expr_zero_mul"]: cat_map[t] = "Expression"
    for t in ["loop_fission","loop_fusion","loop_interchange","loop_init_hoist",
              "loop_peel_first","loop_peel_last","loop_shift","loop_guard_add"]: cat_map[t] = "Loop"
    for t in ["stmt_combine","stmt_reorder","stmt_scalar_replace","stmt_split"]: cat_map[t] = "Statement"
    for t in ["syn_add_braces","syn_remove_braces","syn_whitespace","syn_var_rename",
              "syn_type_cast","syn_paren_add","syn_scalar_val","syn_add_comment"]: cat_map[t] = "Syntactic"

    print(f"\n=== PER-TRANSFORM (primary + finalization) ===")
    all_transforms = sorted(tp_by.keys() | fn_by.keys())
    for tr in all_transforms:
        tp = tp_by[tr]; tot = tp + fn_by[tr]
        rec = 100*tp/tot if tot>0 else 0
        print(f"{tr:<25s}: {tp:>4d}/{tot:<4d} = {rec:>5.1f}%  (FP={fp_by[tr]})")

    print(f"\n=== PER-CATEGORY ===")
    for cat in ["Expression","Loop","Statement","Syntactic"]:
        tp = sum(tp_by[t] for t in all_transforms if cat_map.get(t)==cat)
        tot = sum(tp_by[t]+fn_by[t] for t in all_transforms if cat_map.get(t)==cat)
        print(f"{cat:<12s}: {tp}/{tot} = {100*tp/tot:.1f}%")

    total_tp = sum(tp_by.values()); total_fn = sum(fn_by.values())
    total_fp = sum(fp_by.values()); total_tn = sum(tn_by.values())
    print(f"\nOverall: TP={total_tp} FP={total_fp} FN={total_fn} TN={total_tn}")
    print(f"Recall={100*total_tp/(total_tp+total_fn):.1f}% Prec={100*total_tp/(total_tp+total_fp):.1f}%")

if __name__ == "__main__":
    main()
