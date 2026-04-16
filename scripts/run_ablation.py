#!/usr/bin/env python3
"""Cumulative ablation: progressively strip components from back to front.

Each row removes one more component from the pipeline.
The delta between consecutive rows shows that component's contribution.
"""
import json, os, signal, sys, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO = Path(__file__).resolve().parent.parent
# PolyBench utilities path (set PB_UTILS env var)
PB_UTILS = Path(os.environ.get("PB_UTILS", str(REPO / "PolyBenchC-4.2.1" / "utilities")))
INCS = [PB_UTILS]


def check_one(args):
    ref_path, sample_path, gt_correct, config = args

    def handler(signum, frame):
        raise TimeoutError()
    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(45)
    try:
        proved_eq = _run_config(config, Path(ref_path), Path(sample_path))
    except Exception:
        proved_eq = False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
    return (proved_eq, gt_correct)


def _run_config(config, ref, cand):
    from legvo.egraph.verify import (
        _compiles, _find_egglog, _run_egglog_check,
        _polyhedral_facts, _per_statement_egglog,
        _randomized_test,
    )
    from legvo.egraph.extract import extract_term
    from legvo.egraph.normalize import normalize_minimal, normalize_aggressive

    # Cumulative flags — each level includes all removals above it
    #   0: full
    #   1: − random testing
    #   2: − random testing − per-stmt egglog
    #   3: − random testing − per-stmt egglog − finalization pass
    #   4: − ... − polyhedral analysis
    #   5: − ... − SwapDB/DbShift
    #   6: − ... − algebraic rules
    #   7: − ... − normalization
    level = config

    use_random_test = level < 1
    use_per_stmt = level < 2
    use_finalization = level < 3
    use_polyhedral = level < 4
    use_binding = level < 5
    use_algebraic = level < 6
    use_normalize = level < 7

    # Guard: compile check
    if not _compiles(cand, include_dirs=INCS, ref_dir=ref.parent):
        return False

    # Extract
    try:
        ref_raw = extract_term(ref, include_dirs=INCS)
        cand_raw = extract_term(cand, include_dirs=INCS)
    except Exception:
        return False

    # Normalize
    if use_normalize:
        ref_term = normalize_minimal(ref_raw)
        cand_term = normalize_minimal(cand_raw)
    else:
        ref_term = ref_raw
        cand_term = cand_raw

    # Structural equality
    if ref_term == cand_term:
        return True

    egglog_bin = _find_egglog()

    # Polyhedral analysis
    poly_facts = []
    if use_polyhedral:
        poly_facts = _polyhedral_facts(ref, cand, INCS)

    checks = {}

    # Primary pass: egglog with configured rules
    result = _run_egglog_check(
        ref_term, cand_term, egglog_bin, "real", poly_facts, 15, checks, "primary",
        include_binding=use_binding, include_algebraic=use_algebraic,
    )
    if result.status == "equivalent":
        return True

    # Finalization pass: aggressive normalization + egglog retry
    if use_finalization:
        try:
            ref_term2 = normalize_aggressive(ref_raw)
            cand_term2 = normalize_aggressive(cand_raw)
            if ref_term2 != ref_term or cand_term2 != cand_term:
                result2 = _run_egglog_check(
                    ref_term2, cand_term2, egglog_bin, "real", poly_facts,
                    6, checks, "finalization",
                    include_binding=use_binding, include_algebraic=use_algebraic,
                )
                if result2.status == "equivalent":
                    return True
        except Exception:
            pass

    # Per-statement egglog
    if use_per_stmt and poly_facts:
        per_stmt_ok = ("(ScheduleLegal)" in poly_facts or
                       "(FootprintMatch)" in poly_facts)
        if per_stmt_ok:
            try:
                if _per_statement_egglog(ref_term, cand_term, egglog_bin, "real", 6):
                    return True
            except Exception:
                pass

    # Randomized testing
    if use_random_test:
        try:
            if _randomized_test(ref, cand, INCS):
                return True
        except Exception:
            pass

    return False


def main():
    gt = json.load(open(REPO / "datasets/single_transform_full/ground_truth.json"))
    ds = REPO / "datasets/single_transform_full"

    tasks_base = []
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
                tasks_base.append((str(ref), str(s), gt[gk] == "correct"))

    print(f"Total samples: {len(tasks_base)}")
    print()
    print(f"{'Configuration':45s} {'Acc':>6s} {'Prec':>6s} {'Rec':>6s} "
          f"{'TP':>6s} {'FP':>4s} {'FN':>5s} {'TN':>6s} {'Time':>6s}")
    print("-" * 105)

    configs = [
        ("Full pipeline",                              0),
        ("− Random testing",                           1),
        ("− Per-statement egglog",                     2),
        ("− Finalization pass",                        3),
        ("− Polyhedral analysis",                      4),
        ("− SwapDB/DbShift rules",                     5),
        ("− Algebraic rules",                          6),
        ("− Normalization (raw extract only)",          7),
    ]

    for name, level in configs:
        tasks = [(r, s, g, level) for r, s, g in tasks_base]
        start = time.time()
        tp = fp = fn = tn = 0
        done = 0
        with ProcessPoolExecutor(max_workers=20) as pool:
            futures = {pool.submit(check_one, t): t for t in tasks}
            for f in as_completed(futures):
                eq, gc = f.result()
                if eq and gc: tp += 1
                elif eq and not gc: fp += 1
                elif not eq and gc: fn += 1
                else: tn += 1
                done += 1
                if done % 5000 == 0:
                    print(f"    [{name}] {done}/{len(tasks)}...", flush=True)
        elapsed = time.time() - start
        total = tp + fp + fn + tn
        acc = 100 * (tp + tn) / total
        prec = 100 * tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = 100 * tp / (tp + fn) if (tp + fn) > 0 else 0
        print(f"{name:45s} {acc:6.1f} {prec:6.1f} {rec:6.1f} "
              f"{tp:6d} {fp:4d} {fn:5d} {tn:6d} {elapsed:5.0f}s")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
