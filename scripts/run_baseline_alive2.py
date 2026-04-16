#!/usr/bin/env python3
"""Baseline: run Alive2 (alive-tv) on all 28,800 samples.
Compiles ref and cand to LLVM IR with clang, then runs alive-tv.
Reports parseable rate, precision, recall, and per-category recall.
"""
import json, os, signal, subprocess, sys, tempfile, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

REPO = Path(__file__).resolve().parent.parent
# PolyBench utilities path
PB_UTILS = Path(os.environ.get("PB_UTILS", str(VEGG / "PolyBenchC-4.2.1" / "utilities")))

ALIVE_TV = Path(os.environ.get("ALIVE_TV", "alive-tv"))  # path to alive-tv binary
CLANG = Path(os.environ.get("CLANG", "clang"))  # path to clang binary


def _extract_scop_region(src: Path) -> str:
    """Extract code between #pragma scop and #pragma endscop."""
    text = src.read_text()
    start = text.find("#pragma scop")
    end = text.find("#pragma endscop")
    if start < 0 or end < 0:
        return ""
    # Include everything between the pragmas
    return text[start:end + len("#pragma endscop")]


def _compile_to_ir(src: Path, kernel_name: str) :
    """Compile C source to LLVM IR, return path to .ll file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".ll", delete=False)
    tmp.close()

    inc_dirs = [str(PB_UTILS.resolve())]
    # Find kernel header
    pb_root = PB_UTILS.resolve().parent
    for hdr in pb_root.rglob(f"{kernel_name}.h"):
        inc_dirs.append(str(hdr.parent))
        break

    cmd = [str(CLANG), "-S", "-emit-llvm", "-O0",
           "-DSMALL_DATASET", "-DDATA_TYPE_IS_DOUBLE",
           "-I", str(src.parent)]
    for d in inc_dirs:
        cmd.extend(["-I", d])
    cmd.extend([str(src), "-o", tmp.name])

    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=15)
        if proc.returncode == 0:
            return Path(tmp.name)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    Path(tmp.name).unlink(missing_ok=True)
    return None


def check_one(args):
    ref_path, sample_path, gt_correct, transform = args
    kernel_name = Path(ref_path).parent.name

    # Compile both to LLVM IR
    ref_ir = _compile_to_ir(Path(ref_path), kernel_name)
    if ref_ir is None:
        return (False, gt_correct, False, transform)

    cand_ir = _compile_to_ir(Path(sample_path), kernel_name)
    if cand_ir is None:
        ref_ir.unlink(missing_ok=True)
        return (False, gt_correct, False, transform)

    # Run alive-tv
    proved_eq = False
    parsed = True
    try:
        proc = subprocess.run(
            [str(ALIVE_TV), str(ref_ir), str(cand_ir)],
            capture_output=True, text=True, timeout=10,
        )
        output = proc.stdout + proc.stderr
        if "Transformation seems to be correct" in output:
            proved_eq = True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    ref_ir.unlink(missing_ok=True)
    cand_ir.unlink(missing_ok=True)
    return (proved_eq, gt_correct, parsed, transform)


def main():
    gt = json.load(open(REPO / "datasets/single_transform_full/ground_truth.json"))
    ds = REPO / "datasets/single_transform_full"

    cat_map = {}
    for t in ["expr_comm_add","expr_comm_mul","expr_add_zero","expr_mul_one",
              "expr_assoc_add","expr_distrib","expr_neg_distribute",
              "expr_reorder_terms","expr_self_sub","expr_strength_reduce",
              "expr_sub_cancel","expr_zero_mul"]:
        cat_map[t] = "Expression"
    for t in ["loop_fission","loop_fusion","loop_interchange","loop_init_hoist",
              "loop_peel_first","loop_peel_last","loop_shift","loop_guard_add"]:
        cat_map[t] = "Loop"
    for t in ["stmt_combine","stmt_reorder","stmt_scalar_replace","stmt_split"]:
        cat_map[t] = "Statement"
    for t in ["syn_add_braces","syn_remove_braces","syn_whitespace","syn_var_rename",
              "syn_type_cast","syn_paren_add","syn_scalar_val","syn_add_comment"]:
        cat_map[t] = "Syntactic"

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
    with ProcessPoolExecutor(max_workers=16) as pool:
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

    print(f"\n=== Alive2 Baseline Results ===")
    print(f"Completed in {elapsed:.0f}s")
    print(f"Parseable (both compile): {parsed_count}/{total} = {parseable:.1f}%")
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
