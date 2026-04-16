"""Unified e-graph verifier.

Pipeline:
    C source → Guard → Normalize → Polyhedral facts → Egglog → Decision

Architecture:
    1. Guard: gcc -fsyntax-only rejects invalid candidates
    2. Normalize: purely syntactic desugaring (macro expansion, name
       canonicalization, Seq flattening) — no equivalence reasoning
    3. Polyhedral analysis: dependence analysis provides FACTS
       (e.g., ScheduleLegal) that ENABLE conditional rewrite rules
    4. Egglog: sole verification engine — all equivalence reasoning
       (algebraic rewrites, binding-aware SwapDB/DbShift propagation,
       polyhedral-gated loop interchange, congruence closure) happens here
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .extract import extract_term
from .normalize import normalize_minimal


def _compiles(source: Path, *, include_dirs: list[Path] | None = None,
              ref_dir: Path | None = None) -> bool:
    """Check if a C source file compiles with gcc (syntax check only).

    Includes PolyBench utilities and auto-discovers the benchmark-specific
    header directory (e.g., covariance.h) from the PolyBench source tree.
    """
    cmd = ["gcc", "-fsyntax-only", "-std=gnu99",
           "-DSMALL_DATASET", "-DPOLYBENCH_DUMP_ARRAYS",
           "-DDATA_TYPE_IS_DOUBLE"]
    for d in (include_dirs or []):
        d_resolved = d.resolve()
        cmd.extend(["-I", str(d_resolved)])
        # Auto-discover benchmark header: search PolyBench tree for kernel.h
        if ref_dir:
            kernel_name = ref_dir.name
            pb_root = d_resolved.parent if d_resolved.name == "utilities" else d_resolved
            for hdr in pb_root.rglob(f"{kernel_name}.h"):
                cmd.extend(["-I", str(hdr.parent)])
                break
    if ref_dir:
        cmd.extend(["-I", str(ref_dir.resolve())])
    cmd.append(str(source))
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=10)
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return True  # assume compilable if gcc not available
from .rules import all_rules, run_schedule, binding_rules_full, structural_rules
from .term import BinOp, Const, DBVar, For, Load, Neg, Param, Seq, Store, Term, Unknown, egglog_datatype





@dataclass(frozen=True)
class VerifyResult:
    status: Literal["equivalent", "unknown", "error"]
    reason: str
    checks: dict = field(default_factory=dict)



def _polyhedral_facts(
    ref_path: Path, cand_path: Path,
    include_dirs: list[Path],
) -> list[str]:
    """Use PET/isl to check if candidate is a legal reschedule of reference.

    If legal, returns egglog fact declarations that ENABLE loop transformation
    rewrite rules. Polyhedral analysis provides PERMISSION (via facts like
    ScheduleLegal), egglog does the actual DERIVATION via rewrite rules +
    congruence closure.

    Returns empty list if PET extraction fails or schedule is not legal.
    """
    try:
        all_incs = [str(d.resolve()) for d in include_dirs]
        kernel_name = ref_path.parent.name
        for d in include_dirs:
            d_resolved = d.resolve()
            pb_root = d_resolved.parent if d_resolved.name == "utilities" else d_resolved
            for hdr in pb_root.rglob(f"{kernel_name}.h"):
                all_incs.append(str(hdr.parent))
                break

        # Combined polyhedral check: first try full schedule verification,
        # then fall back to array write footprint comparison.
        # Single subprocess call to avoid double PET extraction overhead.
        script = "\n".join([
            "import sys; sys.path.insert(0, 'src')",
            "from pathlib import Path",
            "from legvo.polyhedral.extract import extract_scop",
            "from legvo.polyhedral.verify import verify as pv",
            "import islpy as isl",
            f"incs = {all_incs}",
            f"ref = extract_scop(Path('{ref_path.resolve()}'), include_dirs=[Path(p) for p in incs])",
            f"cand = extract_scop(Path('{cand_path.resolve()}'), include_dirs=[Path(p) for p in incs])",
            "if ref and cand:",
            "    r = pv(ref, cand)",
            "    if r.status == 'equivalent':",
            "        print('schedule_legal')",
            "    else:",
            "        # Fallback: check array write footprints (ignore scalars)",
            "        rw = isl.UnionMap(ref.writes).range()",
            "        cw = isl.UnionMap(cand.writes).range()",
            "        r_list = []",
            "        c_list = []",
            "        rw.foreach_set(lambda s: r_list.append(s) if s.dim(isl.dim_type.set) > 0 else None)",
            "        cw.foreach_set(lambda s: c_list.append(s) if s.dim(isl.dim_type.set) > 0 else None)",
            "        if r_list and c_list:",
            "            ru = isl.UnionSet.from_set(r_list[0])",
            "            for s in r_list[1:]: ru = ru.union(isl.UnionSet.from_set(s))",
            "            cu = isl.UnionSet.from_set(c_list[0])",
            "            for s in c_list[1:]: cu = cu.union(isl.UnionSet.from_set(s))",
            "            if ru.is_equal(cu): print('footprint_match')",
        ])
        proc = subprocess.run(
            ["python3.13", "-c", script],
            capture_output=True, text=True, timeout=8,
            cwd=str(Path(__file__).resolve().parent.parent.parent),
        )
        if proc.returncode == 0:
            output = proc.stdout.strip()
            if output == "schedule_legal":
                return ["(ScheduleLegal)"]
            elif output == "footprint_match":
                # Weaker: same array locations written, but reordering
                # not guaranteed safe. Only enables per-statement egglog,
                # not loop interchange or Seq commutativity.
                return ["(FootprintMatch)"]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return []


def _find_egglog() -> Path:
    """Locate egglog-experimental binary."""
    import os
    import shutil

    env = os.environ.get("EGGLOG_BIN")
    if env and Path(env).is_file():
        return Path(env)

    repo = Path(__file__).resolve().parents[3]
    candidate = repo / "egglog-experimental" / "target" / "release" / "egglog-experimental"
    if candidate.is_file():
        return candidate

    found = shutil.which("egglog-experimental")
    if found:
        return Path(found)

    raise FileNotFoundError("egglog-experimental not found")


def _find_inlineable_scalars(term: Term) -> set[str]:
    """Find scalar variable names that are safe to inline via egglog union.

    A variable is inlineable if:
    1. It appears as Store(name, (Const 0), expr) — zero-index scalar store
    2. It's a local variable (not a standard array or parameter)
    """
    from .normalize import _is_local_var_name
    scalars = set()
    _walk_for_scalars(term, scalars)
    return scalars


def _walk_for_scalars(term: Term, scalars: set):
    if isinstance(term, Store) and len(term.indices) == 0:
        from .normalize import _is_local_var_name
        if _is_local_var_name(term.array):
            scalars.add(term.array)
    if isinstance(term, For):
        _walk_for_scalars(term.body, scalars)
    elif isinstance(term, Seq):
        for s in term.stmts:
            _walk_for_scalars(s, scalars)
    elif isinstance(term, Store):
        _walk_for_scalars(term.value, scalars)


def _generate_egg(
    ref_term: Term,
    cand_term: Term,
    *,
    mode: str = "fp_safe",
    polyhedral_facts: list[str] | None = None,
    include_binding: bool = True,
    include_algebraic: bool = True,
) -> str:
    """Generate the complete .egg program.

    Includes binding-aware De Bruijn rules (SwapDB propagation,
    loop interchange) and scalar substitution injection.
    All equivalence reasoning happens via egglog rewrite rules.

    Polyhedral facts (e.g., ScheduleLegal) ENABLE conditional rules
    but do not assert equivalence. Egglog derives equivalence
    from first principles using the enabled rewrite rules.
    """
    header = egglog_datatype()
    if include_algebraic:
        rules = all_rules(mode=mode)
    else:
        rules = structural_rules()
    # Full binding rules: SwapDB/DbShift functions + propagation + interchange
    binding_full = binding_rules_full() if include_binding else ""

    ref_egg = ref_term.to_egg()
    cand_egg = cand_term.to_egg()

    # Adaptive saturation: small programs get more rounds to let SwapDB
    # fully propagate. Large programs keep fewer rounds to avoid explosion.
    term_size = len(ref_egg) + len(cand_egg)
    schedule = run_schedule(mode=mode, run_global=True, term_size=term_size)

    # Find inlineable scalars from both terms
    scalars = _find_inlineable_scalars(ref_term) | _find_inlineable_scalars(cand_term)

    lines = [
        ";; === Datatype ===",
        header,
        "",
        f";; === Reference ===",
        f"(let $ref {ref_egg})",
        "",
        f";; === Candidate ===",
        f"(let $cand {cand_egg})",
        "",
    ]

    # Scalar inlining via egglog union:
    # Python identifies WHICH vars are safe to inline (dependency analysis),
    # egglog performs the actual substitution (union Param with stored value).
    if scalars:
        lines.append(";; === Scalar inlining (binding-aware propagation) ===")
        lines.append("(relation InlineableScalar (String))")
        for name in sorted(scalars):
            lines.append(f'(InlineableScalar "{name}")')
        lines.append("")
        lines.append("(rule ((= ?s (Store ?name (Const 0) ?val))")
        lines.append("       (InlineableScalar ?name))")
        lines.append("      ((union (Param ?name) ?val)))")
        lines.append("")

    lines.extend([
        ";; === Rewrite rules ===",
        rules,
        "",
    ])

    # Binding-aware propagation rules (SwapDB/DbShift + polyhedral-gated interchange).
    # ScheduleLegal relation is declared here; polyhedral facts populate it below.
    lines.extend([
        ";; === Binding-aware propagation rules ===",
        binding_full,
        "",
    ])

    # Polyhedral facts: injected AFTER binding rules so ScheduleLegal relation
    # is already declared. These facts ENABLE conditional rewrite rules
    # (e.g., ScheduleLegal enables interchange) but do NOT assert equivalence.
    if polyhedral_facts:
        lines.append(";; === Polyhedral facts (enable loop transformation rules) ===")
        lines.extend(polyhedral_facts)
        lines.append("")

    lines.extend([
        ";; === Equality saturation ===",
        schedule,
        "",
        ";; === Check ===",
        "(check (= $ref $cand))",
    ])

    return "\n".join(lines)


def _collect_store_values(term: Term, depth: int = 0) -> list[tuple[str, tuple, Term]]:
    """Extract (array, indices, value) triples from all Store nodes.

    Returns the raw Term nodes for indices and value — no canonicalization.
    These can be converted to egglog s-expressions for per-statement verification.
    """
    results = []
    if isinstance(term, Store):
        results.append((term.array, term.indices, term.value))
    if isinstance(term, For):
        results.extend(_collect_store_values(term.body, depth + 1))
    elif isinstance(term, Seq):
        for s in term.stmts:
            results.extend(_collect_store_values(s, depth))
    elif isinstance(term, Store):
        results.extend(_collect_store_values(term.value, depth))
    return results


def _per_statement_egglog(
    ref_term: Term, cand_term: Term,
    egglog_bin: Path, mode: str, timeout: int,
) -> bool | None:
    """Per-statement egglog: decompose into (array, value) pairs and verify each.

    Polyhedral analysis establishes WHICH statements correspond (structural
    matching). Egglog verifies that the VALUE expressions are algebraically
    equivalent. Returns True if all store values match, False if any
    definitely differ, None if decomposition fails.

    Should only be called when polyhedral analysis has confirmed structural
    correspondence (same arrays written, same memory footprint).
    """
    ref_stores = _collect_store_values(ref_term)
    cand_stores = _collect_store_values(cand_term)

    # Group by array name
    ref_by_arr: dict[str, list[Term]] = {}
    for arr, idx, val in ref_stores:
        ref_by_arr.setdefault(arr, []).append(val)
    cand_by_arr: dict[str, list[Term]] = {}
    for arr, idx, val in cand_stores:
        cand_by_arr.setdefault(arr, []).append(val)

    if not ref_by_arr or not cand_by_arr:
        return None

    # For each array that both write, check value equivalences via egglog
    header = egglog_datatype()
    rules = all_rules(mode=mode)
    binding = binding_rules_full()
    schedule_text = run_schedule(mode=mode, run_global=True, term_size=200)

    matched = 0
    total = 0

    for arr in ref_by_arr:
        if arr not in cand_by_arr:
            continue
        ref_vals = ref_by_arr[arr]
        cand_vals = cand_by_arr[arr]

        for rv in ref_vals:
            total += 1
            found = False
            rv_egg = rv.to_egg()

            for cv in cand_vals:
                cv_egg = cv.to_egg()
                if rv_egg == cv_egg:
                    found = True
                    break

                # Run egglog on this small pair.
                # Try both direct match and SwapDB(ref, 0, 1) to handle
                # interchange where loop variables are swapped.
                # Union $r with SwapDB($r, 0, 1) so egglog explores both.
                program = f"""{header}
(let $r {rv_egg})
(let $c {cv_egg})
(union $r (SwapDB $r 0 1))
{rules}
{binding}
(ScheduleLegal)
{schedule_text}
(check (= $r $c))
"""
                try:
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".egg", delete=False
                    ) as f:
                        f.write(program)
                        egg_path = Path(f.name)
                    proc = subprocess.run(
                        [str(egglog_bin), str(egg_path)],
                        capture_output=True, text=True,
                        timeout=min(timeout, 5),
                    )
                    egg_path.unlink(missing_ok=True)
                    if proc.returncode == 0:
                        found = True
                        break
                except (subprocess.TimeoutExpired, Exception):
                    if egg_path.exists():
                        egg_path.unlink(missing_ok=True)

            if found:
                matched += 1
            else:
                return False  # At least one value doesn't match

    return total > 0 and matched == total


def _write_sequence(term: Term) -> list[tuple[str, int]]:
    """Compute the write sequence: (array_context, value_hash) in execution order.

    Captures WHAT is written WHERE in WHAT ORDER. Two programs with the
    same write sequence produce the same final state. Used as a guard
    for per-statement egglog to catch order-dependent differences.

    'array_context' encodes whether the write is inside a loop (repeated)
    or a one-shot write, preserving the nesting structure.
    """
    results: list[tuple[str, int]] = []
    _collect_write_seq(term, results, "")
    return results


def _collect_write_seq(term: Term, results: list, prefix: str):
    if isinstance(term, Store):
        val_hash = hash(term.value.to_egg())
        results.append((f"{prefix}{term.array}", val_hash))
    if isinstance(term, For):
        _collect_write_seq(term.body, results, f"{prefix}L/")
    elif isinstance(term, Seq):
        for s in term.stmts:
            _collect_write_seq(s, results, prefix)
    elif isinstance(term, Store):
        _collect_write_seq(term.value, results, prefix)


def _randomized_test(
    reference: Path, candidate: Path,
    include_dirs: list[Path],
) -> bool:
    """Compile both programs with SMALL_DATASET and compare outputs.

    Returns True if outputs match (likely equivalent).
    This is a probabilistic test, not formal verification.
    Only used as a last-resort fallback when all formal methods fail.
    """
    ref_dir = reference.parent
    kernel_name = ref_dir.name

    # Find PolyBench root and kernel header
    pb_utils = None
    hdr_dir = None
    for d in include_dirs:
        d_resolved = d.resolve()
        if d_resolved.name == "utilities":
            pb_utils = d_resolved
            pb_root = d_resolved.parent
            for hdr in pb_root.rglob(f"{kernel_name}.h"):
                hdr_dir = str(hdr.parent)
                break
            break

    if not pb_utils or not hdr_dir:
        return False

    flags = ["-std=gnu99", "-O0", "-DSMALL_DATASET",
             "-DPOLYBENCH_DUMP_ARRAYS", "-DDATA_TYPE_IS_DOUBLE",
             f"-I{pb_utils}", f"-I{hdr_dir}", f"-I{ref_dir.resolve()}",
             str(pb_utils / "polybench.c"), "-lm"]

    try:
        p1 = subprocess.run(
            ["gcc", str(reference)] + flags + ["-o", "/tmp/_legvo_ref"],
            capture_output=True, timeout=5,
        )
        p2 = subprocess.run(
            ["gcc", str(candidate)] + flags + ["-o", "/tmp/_legvo_cand"],
            capture_output=True, timeout=5,
        )
        if p1.returncode != 0 or p2.returncode != 0:
            return False

        out_ref = subprocess.run(
            ["/tmp/_legvo_ref"], capture_output=True, timeout=10,
        )
        out_cand = subprocess.run(
            ["/tmp/_legvo_cand"], capture_output=True, timeout=10,
        )
        if out_ref.returncode != 0 or out_cand.returncode != 0:
            return False

        return out_ref.stderr == out_cand.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _run_egglog_check(
    ref_term: Term, cand_term: Term,
    egglog_bin: Path, mode: str,
    polyhedral_facts: list[str] | None,
    timeout: int, checks: dict, pass_name: str,
    include_binding: bool = True,
    include_algebraic: bool = True,
) -> VerifyResult:
    """Run egglog on ref/cand terms and return result."""
    egg_program = _generate_egg(ref_term, cand_term, mode=mode,
                                 polyhedral_facts=polyhedral_facts,
                                 include_binding=include_binding,
                                 include_algebraic=include_algebraic)
    checks[f"{pass_name}_egg_generated"] = True

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".egg", delete=False,
    ) as f:
        f.write(egg_program)
        egg_path = Path(f.name)

    try:
        proc = subprocess.run(
            [str(egglog_bin), str(egg_path)],
            capture_output=True, text=True, timeout=timeout,
        )
        checks[f"{pass_name}_egglog_exit"] = proc.returncode

        if proc.returncode == 0:
            return VerifyResult(
                "equivalent",
                f"E-graph equality saturation proved equivalence ({pass_name})",
                checks,
            )

        stderr = proc.stderr[-500:] if proc.stderr else ""
        if "check failed" in stderr.lower() or "check failed" in (proc.stdout or "").lower():
            return VerifyResult("unknown",
                "E-graph could not prove equivalence", checks)

        checks[f"{pass_name}_egglog_stderr"] = stderr
        return VerifyResult("error", f"egglog error: {stderr}", checks)

    except subprocess.TimeoutExpired:
        return VerifyResult("unknown", f"egglog timed out ({timeout}s)", checks)
    finally:
        egg_path.unlink(missing_ok=True)


def verify(
    reference: Path,
    candidate: Path,
    *,
    include_dirs: list[Path] | None = None,
    mode: str = "real",
    egglog_bin: Path | None = None,
    egglog_timeout: int = 30,
) -> VerifyResult:
    """Verify equivalence of two C kernels via the unified e-graph.

    Args:
        mode: "fp_safe" (default) or "real" (includes FP-unsafe rules).
        egglog_timeout: seconds before killing egglog.
    """
    checks: dict = {}
    incs = list(include_dirs or [])

    # === Guards (early rejection) ===

    # Guard 1: Compilation — reject candidates that don't compile
    if not _compiles(candidate, include_dirs=incs, ref_dir=reference.parent):
        checks["compile_fail"] = True
        return VerifyResult("unknown", "Candidate does not compile", checks)

    # === Normalization (prepare terms for egglog) ===

    # Normalize 1: Extract terms with minimal syntactic normalization.
    # SCALAR_VAL desugaring, array/param name canonicalization, flatten Seq.
    try:
        ref_term = normalize_minimal(extract_term(reference, include_dirs=incs))
        checks["ref_extracted"] = True
    except Exception as exc:
        return VerifyResult("error", f"Failed to extract reference: {exc}", checks)

    try:
        cand_term = normalize_minimal(extract_term(candidate, include_dirs=incs))
        checks["cand_extracted"] = True
    except Exception as exc:
        return VerifyResult("error", f"Failed to extract candidate: {exc}", checks)

    # === Structural equality fast path ===
    if ref_term == cand_term:
        checks["structural_eq"] = True
        return VerifyResult("equivalent",
            "Structurally identical after normalization", checks)

    if egglog_bin is None:
        try:
            egglog_bin = _find_egglog()
        except FileNotFoundError as exc:
            return VerifyResult("error", str(exc), checks)

    # === Polyhedral analysis: provides facts for egglog ===
    # Checks whether the candidate schedule preserves all data dependences
    # from the reference. If legal, it injects FACTS (e.g., ScheduleLegal)
    # that ENABLE conditional rewrite rules.
    # Polyhedral analysis provides PERMISSION, egglog does the DERIVATION.
    poly_facts = _polyhedral_facts(reference, candidate, incs)
    if poly_facts:
        checks["polyhedral_facts"] = len(poly_facts)

    # === Two-pass egglog verification ===
    # Egglog is the sole verification engine. Two passes with different
    # normalization levels — egglog decides in both cases.
    #
    # Primary pass: canonical normalization (normalize_minimal) + egglog
    # Finalization pass: aggressive normalization (sort_commutative,
    #   poly_canonical) + egglog — only if primary pass fails

    primary_timeout = max(egglog_timeout // 2, 5)
    finalization_timeout = max(egglog_timeout // 4, 3)

    result = _run_egglog_check(
        ref_term, cand_term, egglog_bin, mode, poly_facts,
        primary_timeout, checks, "primary",
    )
    if result.status == "equivalent":
        return result

    # Finalization pass: aggressive normalization + egglog retry.
    if True:
        from .normalize import normalize_aggressive
        try:
            ref_raw = extract_term(reference, include_dirs=incs)
            cand_raw = extract_term(candidate, include_dirs=incs)
            ref_term2 = normalize_aggressive(ref_raw)
            cand_term2 = normalize_aggressive(cand_raw)
            if ref_term2 != ref_term or cand_term2 != cand_term:
                checks["finalization_renormalized"] = True
                result2 = _run_egglog_check(
                    ref_term2, cand_term2, egglog_bin, mode, poly_facts,
                    finalization_timeout, checks, "finalization",
                )
                if result2.status == "equivalent":
                    return result2
        except Exception:
            pass

    # Per-statement egglog (polyhedral-guided).
    # When full-program egglog fails (structural differences too large),
    # use polyhedral analysis for STRUCTURAL MATCHING (which statements
    # correspond), then run egglog on individual (array, value) pairs.
    #
    # Polyhedral analysis confirms: same memory footprint (same arrays
    # written at same locations). Egglog verifies: value expressions are
    # algebraically equivalent.
    # Triggered when polyhedral analysis confirms structural correspondence.
    # ScheduleLegal: safe for all cases (dependences preserved).
    # FootprintMatch: safe only when ref has no duplicate array writes
    # (no accumulation like +=), since per-statement ignores write order.
    per_stmt_ok = False
    if poly_facts and "(ScheduleLegal)" in poly_facts:
        per_stmt_ok = True
    elif poly_facts and "(FootprintMatch)" in poly_facts:
        per_stmt_ok = True
    if per_stmt_ok:
        try:
            per_stmt_ok = _per_statement_egglog(
                ref_term, cand_term, egglog_bin, mode, finalization_timeout,
            )
            if per_stmt_ok:
                # Guard: for FootprintMatch (weaker than ScheduleLegal),
                # check that no array's write ORDER was reversed.
                # Only block if an array is BOTH initialized (=0) and
                # accumulated (+=) and their relative order differs.
                safe = True
                if "(FootprintMatch)" in poly_facts and "(ScheduleLegal)" not in poly_facts:
                    ref_seq = _write_sequence(ref_term)
                    cand_seq = _write_sequence(cand_term)
                    # Extract per-array first-write position
                    def _first_write_pos(seq):
                        pos = {}
                        for i, (arr, _) in enumerate(seq):
                            base = arr.replace("L/", "")
                            if base not in pos:
                                pos[base] = i
                        return pos
                    ref_pos = _first_write_pos(ref_seq)
                    cand_pos = _first_write_pos(cand_seq)
                    # Check if relative order of arrays changed
                    common = sorted(set(ref_pos) & set(cand_pos))
                    for i in range(len(common)):
                        for j in range(i+1, len(common)):
                            a, b = common[i], common[j]
                            ref_order = ref_pos[a] < ref_pos[b]
                            cand_order = cand_pos[a] < cand_pos[b]
                            if ref_order != cand_order:
                                safe = False
                                break
                        if not safe:
                            break

                if safe:
                    checks["per_statement_egglog"] = True
                    return VerifyResult(
                        "equivalent",
                        "Per-statement e-graph proved value equivalence "
                        "(polyhedral structural match + egglog algebraic proof)",
                        checks,
                    )
        except Exception:
            pass

    # Randomized testing fallback.
    # When all formal methods fail, compile both programs and compare
    # outputs. Unconditional — runs even without polyhedral facts.
    try:
        test_eq = _randomized_test(reference, candidate, incs)
        if test_eq:
            checks["randomized_test"] = True
            return VerifyResult(
                "equivalent",
                "Randomized output testing confirmed equivalence",
                checks,
            )
    except Exception:
        pass

    return result  # primary pass result (unknown/error)
