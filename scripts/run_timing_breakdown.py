#!/usr/bin/env python3
"""Measure per-stage timing breakdown on a random sample of cases.
Reports median, P95, P99, max for: parse+normalize, polyhedral, egglog, total.
"""
import json, os, random, signal, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# PolyBench utilities path (set PB_UTILS env var)
PB_UTILS = Path(os.environ.get("PB_UTILS", str(REPO / "PolyBenchC-4.2.1" / "utilities")))
INCS = [PB_UTILS]


def main():
    import numpy as np
    gt = json.load(open(REPO / "datasets/single_transform_full/ground_truth.json"))
    ds = REPO / "datasets/single_transform_full"

    # Collect all correct, compilable samples
    all_tasks = []
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
                all_tasks.append((ref, s, gt[gk]))

    # Sample 500 cases (mix of correct, incorrect, compile_fail)
    random.seed(42)
    sample = random.sample(all_tasks, min(500, len(all_tasks)))
    print(f"Timing {len(sample)} samples...")

    from legvo.egraph.verify import (
        _compiles, _find_egglog, _run_egglog_check,
        _polyhedral_facts, _per_statement_egglog,
        _randomized_test,
    )
    from legvo.egraph.extract import extract_term
    from legvo.egraph.normalize import normalize_minimal, normalize_aggressive

    egglog_bin = _find_egglog()

    t_parse_norm = []
    t_polyhedral = []
    t_egglog = []
    t_total = []

    for i, (ref, cand, gt_val) in enumerate(sample):
        t0 = time.perf_counter()

        # Stage 1: Parse + Normalize
        t_s1 = time.perf_counter()
        if not _compiles(cand, include_dirs=INCS, ref_dir=ref.parent):
            t1 = time.perf_counter()
            t_parse_norm.append(t1 - t_s1)
            t_polyhedral.append(0)
            t_egglog.append(0)
            t_total.append(t1 - t0)
            continue

        try:
            ref_term = normalize_minimal(extract_term(ref, include_dirs=INCS))
            cand_term = normalize_minimal(extract_term(cand, include_dirs=INCS))
        except Exception:
            t1 = time.perf_counter()
            t_parse_norm.append(t1 - t_s1)
            t_polyhedral.append(0)
            t_egglog.append(0)
            t_total.append(t1 - t0)
            continue
        t1 = time.perf_counter()
        t_parse_norm.append(t1 - t_s1)

        if ref_term == cand_term:
            t_polyhedral.append(0)
            t_egglog.append(0)
            t_total.append(t1 - t0)
            continue

        # Stage 2: Polyhedral analysis
        t_s2 = time.perf_counter()
        poly_facts = _polyhedral_facts(ref, cand, INCS)
        t2 = time.perf_counter()
        t_polyhedral.append(t2 - t_s2)

        # Stage 3: Egglog (primary + finalization)
        t_s3 = time.perf_counter()
        checks = {}
        try:
            result = _run_egglog_check(
                ref_term, cand_term, egglog_bin, "real", poly_facts,
                15, checks, "primary"
            )
            if result.status != "equivalent":
                # Finalization pass
                try:
                    ref_raw = extract_term(ref, include_dirs=INCS)
                    cand_raw = extract_term(cand, include_dirs=INCS)
                    ref_term2 = normalize_aggressive(ref_raw)
                    cand_term2 = normalize_aggressive(cand_raw)
                    if ref_term2 != ref_term or cand_term2 != cand_term:
                        _run_egglog_check(
                            ref_term2, cand_term2, egglog_bin, "real",
                            poly_facts, 6, checks, "finalization"
                        )
                except Exception:
                    pass
        except Exception:
            pass
        t3 = time.perf_counter()
        t_egglog.append(t3 - t_s3)

        t_total.append(t3 - t0)

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(sample)} done", flush=True)

    # Stats
    def stats(arr, name):
        a = np.array(arr)
        print(f"  {name:20s}: median={np.median(a):.3f}  "
              f"P95={np.percentile(a,95):.3f}  "
              f"P99={np.percentile(a,99):.3f}  "
              f"max={np.max(a):.3f}")

    print(f"\n=== Timing Breakdown ({len(sample)} samples) ===")
    stats(t_parse_norm, "Parse + Normalize")
    stats(t_polyhedral, "Polyhedral (PET/isl)")
    stats(t_egglog, "Egglog saturation")
    stats(t_total, "Total")


if __name__ == "__main__":
    main()
