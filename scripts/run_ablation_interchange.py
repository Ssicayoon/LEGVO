#!/usr/bin/env python3
"""Focused ablation: SwapDB contribution on structural transforms.
Runs primary + finalization passes with and without SwapDB + polyhedral analysis.
"""
import json, os, signal, sys, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO = Path(__file__).resolve().parent.parent
# PolyBench utilities path (set PB_UTILS env var)
PB_UTILS = Path(os.environ.get("PB_UTILS", str(REPO / "PolyBenchC-4.2.1" / "utilities")))
INCS = [PB_UTILS]


def check_one(args):
    ref_path, sample_path, gt_correct, use_binding, use_polyhedral = args
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
            return (False, gt_correct)

        ref_raw = extract_term(ref, include_dirs=INCS)
        cand_raw = extract_term(cand, include_dirs=INCS)
        ref_term = normalize_minimal(ref_raw)
        cand_term = normalize_minimal(cand_raw)

        if ref_term == cand_term:
            return (True, gt_correct)

        egglog_bin = _find_egglog()
        poly_facts = _polyhedral_facts(ref, cand, INCS) if use_polyhedral else []
        checks = {}

        # Primary pass
        r = _run_egglog_check(ref_term, cand_term, egglog_bin, "real",
                              poly_facts, 15, checks, "primary",
                              include_binding=use_binding)
        if r.status == "equivalent":
            return (True, gt_correct)

        # Finalization pass
        ref_t2 = normalize_aggressive(ref_raw)
        cand_t2 = normalize_aggressive(cand_raw)
        if ref_t2 != ref_term or cand_t2 != cand_term:
            r2 = _run_egglog_check(ref_t2, cand_t2, egglog_bin, "real",
                                   poly_facts, 6, checks, "finalization",
                                   include_binding=use_binding)
            if r2.status == "equivalent":
                return (True, gt_correct)

        return (False, gt_correct)
    except Exception:
        return (False, gt_correct)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def main():
    gt = json.load(open(REPO / "datasets/single_transform_full/ground_truth.json"))
    ds = REPO / "datasets/single_transform_full"

    # Only loop transforms (interchange is the key, but include all loop types)
    loop_types = ["loop_interchange", "loop_fusion", "loop_fission",
                  "loop_init_hoist", "loop_peel_first", "loop_peel_last",
                  "loop_shift", "loop_guard_add"]

    tasks_by_type = {}
    for tname in loop_types:
        td = ds / tname
        if not td.is_dir(): continue
        tasks = []
        for kd in sorted(td.iterdir()):
            if not kd.is_dir(): continue
            ref = kd / "reference.c"
            if not ref.exists(): continue
            for s in sorted(kd.glob("sample_*.c")):
                num = s.stem.replace("sample_", "")
                gk = f"{tname}/{kd.name}/s{num}"
                if gk not in gt: continue
                tasks.append((str(ref), str(s), gt[gk] == "correct"))
        tasks_by_type[tname] = tasks

    configs = [
        ("Full (SwapDB + polyhedral)",     True,  True),
        ("No SwapDB / polyhedral",         False, False),
    ]

    print(f"{'Transform':<22s}", end="")
    for name, _, _ in configs:
        print(f"  {name:>30s}", end="")
    print(f"  {'Δ':>8s}")
    print("-" * 100)

    for tname in loop_types:
        tasks = tasks_by_type.get(tname, [])
        if not tasks:
            continue
        total_correct = sum(1 for _, _, g in tasks if g)

        recalls = []
        for cname, use_bind, use_poly in configs:
            task_args = [(r, s, g, use_bind, use_poly) for r, s, g in tasks]
            tp = 0
            with ProcessPoolExecutor(max_workers=20) as pool:
                futures = [pool.submit(check_one, t) for t in task_args]
                for f in futures:
                    eq, gc = f.result()
                    if eq and gc:
                        tp += 1
            rec = 100 * tp / total_correct if total_correct > 0 else 0
            recalls.append((tp, total_correct, rec))

        delta = recalls[0][2] - recalls[1][2]
        print(f"{tname:<22s}", end="")
        for tp, tot, rec in recalls:
            print(f"  {tp:>4d}/{tot:<4d} = {rec:>5.1f}%    ", end="")
        print(f"  {delta:>+6.1f}pp")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
