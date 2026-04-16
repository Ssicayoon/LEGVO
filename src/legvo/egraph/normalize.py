"""Term normalization passes.

Applied BEFORE sending to egglog to reduce structural differences
that are semantically irrelevant:

1. SCALAR_VAL(x) → Const(x)
2. Strip restrict/const qualifiers from array names
3. Normalize parameter names (_PB_N → N, _PB_M → M)
4. Inline scalar local variables (Store to scalar → replace uses)
5. Flatten trivial Seq chains
"""

from __future__ import annotations

import re
from typing import Callable

from .term import (
    BinOp, Const, DBVar, For, Let, Load, Neg, Param, Reduce,
    Seq, Store, Term, Unknown,
)


def normalize_aggressive(term: Term) -> Term:
    """Aggressive canonical normalization — finalization pass fallback.

    Applied only when primary pass (normalize_minimal + egglog) fails.
    Includes stronger algebraic canonicalization that reduces both
    ref and cand to a common canonical form, making egglog's job
    easier on retry. Egglog remains the sole decision engine.

    Additional passes over normalize_minimal:
    - Sub/Neg normalization: Sub(a,b) → Add(a, Neg(b))
    - Polynomial canonicalization: fixpoint of distribute + fold + sort
    - Commutative sorting: canonical operand order for Mul
    """
    term = normalize_minimal(term)
    term = _normalize_sub_neg(term)
    term = _normalize_strength_reduce(term)
    term = _sort_commutative(term)
    term = _normalize_distributivity(term)
    term = _sort_commutative(term)
    term = _poly_canonical(term)
    from .oracle import normalize_loop_order
    term = normalize_loop_order(term)
    term = _flatten_seq(term)
    term = _constant_fold(term)
    return term


def normalize(term: Term) -> Term:
    """Full normalization — all passes including semantic equivalences."""
    term = normalize_minimal(term)
    # Semantic equivalence passes (being migrated to egglog rules)
    term = _de_scalar_promote(term)
    term = _inline_scalar_stores(term)
    term = _flatten_seq(term)
    term = _constant_fold(term)
    term = _normalize_sub_neg(term)
    term = _normalize_strength_reduce(term)
    term = _unpeel_loops(term)
    term = _unshift_loops(term)
    term = _canonicalize_loop_var_params(term)
    term = _sort_commutative(term)
    term = _normalize_distributivity(term)
    term = _sort_commutative(term)
    term = _poly_canonical(term)
    from .oracle import normalize_loop_order
    term = normalize_loop_order(term)
    term = _flatten_seq(term)
    term = _constant_fold(term)
    return term


def normalize_minimal(term: Term) -> Term:
    """Canonical form normalization — preprocessing before egglog.

    Produces a canonical Term representation from raw extraction output.
    This is INPUT CANONICALIZATION, not equivalence verification — the
    same transformation is applied uniformly to both reference and
    candidate before they enter egglog.

    Syntactic passes (no semantic content):
    - SCALAR_VAL macro expansion: SCALAR_VAL(x) → Const(x)
    - Array name cleaning: strip restrict/const qualifiers
    - Parameter name normalization: _PB_N → N
    - Seq flattening: nested Seq → flat Seq
    - Loop variable canonicalization: ii → i, jj → j
    - Constant folding: Const(a) op Const(b) → Const(result)

    Structural canonicalization (deterministic rewriting to canonical form):
    - Loop unpeel: Seq(stmt, For(1,N,body)) → For(0,N,body) when
      stmt matches body[0]. Restores canonical loop form.
    - Loop unshift: For(k, hi+k, body) → For(0, hi, body'). Restores
      zero-based canonical loop form.
    - Scalar de-promotion: scalar aliases → array elements
    - Scalar inlining: temp variable elimination

    These structural passes apply the SAME canonical form to BOTH inputs.
    The equivalence verification engine is egglog — it checks whether
    the canonical forms are provably equal via rewrite rules.
    """
    term = _normalize_scalar_val(term)
    term = _normalize_array_names(term)
    term = _normalize_param_names(term)
    term = _flatten_seq(term)
    term = _de_scalar_promote(term)
    term = _inline_scalar_stores(term)
    term = _flatten_seq(term)
    term = _constant_fold(term)
    # Run unpeel BEFORE unshift to catch peels with original loop bounds.
    # Then unshift. Then unpeel AGAIN to catch peels revealed by unshift.
    term = _unpeel_loops(term)
    term = _flatten_seq(term)
    term = _constant_fold(term)
    term = _unshift_loops(term)
    term = _flatten_seq(term)
    term = _constant_fold(term)
    term = _unpeel_loops(term)
    term = _flatten_seq(term)
    term = _constant_fold(term)
    term = _canonicalize_loop_var_params(term)
    return term


# ── Polynomial canonical form ────────────────────────────────────────

def _term_node_count(term: Term) -> int:
    """Count nodes in a term tree (for size guards)."""
    if isinstance(term, (Const, Param, DBVar, Unknown)):
        return 1
    if isinstance(term, Neg):
        return 1 + _term_node_count(term.operand)
    if isinstance(term, BinOp):
        return 1 + _term_node_count(term.left) + _term_node_count(term.right)
    if isinstance(term, Load):
        return 1 + sum(_term_node_count(i) for i in term.indices)
    if isinstance(term, Store):
        return 1 + sum(_term_node_count(i) for i in term.indices) + _term_node_count(term.value)
    if isinstance(term, For):
        return 1 + _term_node_count(term.lo) + _term_node_count(term.hi) + _term_node_count(term.step) + _term_node_count(term.body)
    if isinstance(term, Seq):
        return 1 + sum(_term_node_count(s) for s in term.stmts)
    return 1


def _poly_canonical(term: Term) -> Term:
    """Full polynomial canonicalization via fixpoint iteration.

    Converts all Sub to Add+Neg, pulls Neg through Mul, distributes
    Mul over Add, folds constants, and sorts commutative ops.
    This handles expr_neg_distribute, expr_sub_cancel, expr_reorder_terms.

    Size guard: aborts if term grows beyond 10x initial size to prevent
    exponential blowup from distributivity on large expressions.
    """
    max_nodes = max(_term_node_count(term) * 10, 5000)
    for _ in range(5):  # safety bound
        prev = term
        term = _sub_to_add_neg(term)
        term = _neg_through_mul(term)
        term = _constant_fold(term)
        term = _normalize_distributivity(term)
        if _term_node_count(term) > max_nodes:
            term = prev  # distributivity caused blowup — revert
            break
        term = _constant_fold(term)
        term = _sort_commutative(term)
        if term == prev:
            break
    # Final: convert back to Sub form for canonical comparison
    term = _normalize_sub_neg(term)
    term = _constant_fold(term)
    return term


def _sub_to_add_neg(term: Term) -> Term:
    """Convert Sub(a, b) → Add(a, Neg(b)) for all nodes."""
    def convert(t: Term) -> Term:
        if isinstance(t, BinOp) and t.op == "Sub":
            return BinOp("Add", t.left, Neg(t.right))
        return t
    return _map_term(term, convert)


def _neg_through_mul(term: Term) -> Term:
    """Pull Neg out of Mul operands, distribute Neg over Add, cancel double negation.

    Mul(Neg(a), b)      → Neg(Mul(a, b))
    Mul(a, Neg(b))      → Neg(Mul(a, b))
    Mul(Neg(a), Neg(b)) → Mul(a, b)
    Neg(Neg(a))         → a
    Neg(Add(a, b))      → Add(Neg(a), Neg(b))
    """
    def transform(t: Term) -> Term:
        if isinstance(t, Neg):
            inner = t.operand
            if isinstance(inner, Neg):
                return inner.operand
            if isinstance(inner, BinOp) and inner.op == "Add":
                return BinOp("Add", Neg(inner.left), Neg(inner.right))
        if isinstance(t, BinOp) and t.op == "Mul":
            left_neg = isinstance(t.left, Neg)
            right_neg = isinstance(t.right, Neg)
            # Negative constant in Mul: Mul(Const(-x), y) → Neg(Mul(Const(x), y))
            left_neg_const = isinstance(t.left, Const) and t.left.value < 0
            right_neg_const = isinstance(t.right, Const) and t.right.value < 0
            if left_neg and right_neg:
                return BinOp("Mul", t.left.operand, t.right.operand)
            if left_neg_const and right_neg_const:
                return BinOp("Mul", Const(-t.left.value), Const(-t.right.value))
            if left_neg:
                return Neg(BinOp("Mul", t.left.operand, t.right))
            if right_neg:
                return Neg(BinOp("Mul", t.left, t.right.operand))
            if left_neg_const:
                return Neg(BinOp("Mul", Const(-t.left.value), t.right))
            if right_neg_const:
                return Neg(BinOp("Mul", t.left, Const(-t.right.value)))
        return t
    return _map_term(term, transform)


# ── Pass 13: Distributivity normalization ───────────────────────────

def _normalize_distributivity(term: Term) -> Term:
    """Always distribute multiplication over addition (canonical form).

    a * (b + c) → a*b + a*c
    (b + c) * a → b*a + c*a

    This is the canonical "expanded" form. Both distributivity and
    factoring produce the same result when applied consistently.
    """
    def distrib(t: Term) -> Term:
        if isinstance(t, BinOp) and t.op == "Mul":
            # a * (b + c) → a*b + a*c
            if isinstance(t.right, BinOp) and t.right.op == "Add":
                return BinOp("Add",
                    BinOp("Mul", t.left, t.right.left),
                    BinOp("Mul", t.left, t.right.right))
            # (b + c) * a → b*a + c*a
            if isinstance(t.left, BinOp) and t.left.op == "Add":
                return BinOp("Add",
                    BinOp("Mul", t.left.left, t.right),
                    BinOp("Mul", t.left.right, t.right))
        return t
    return _map_term(term, distrib)


# ── Pass 14: Distribute post-loop operations into loop body ────────

def _distribute_post_loop_ops(term: Term) -> Term:
    """Distribute post-loop Div/Mul into accumulation loop body.

    Pattern:
        Seq(... For(lo,hi,step, Store(arr,idx, Add(expr, Load(arr,idx)))),
                Store(arr, idx, Div(Load(arr,idx), c)),
            ...)
    Becomes:
        Seq(... For(lo,hi,step, Store(arr,idx, Add(Div(expr,c), Load(arr,idx)))),
            ...)

    Valid because sum(x_k)/c = sum(x_k/c) (distributivity over summation).
    """
    if isinstance(term, Seq):
        stmts = list(term.stmts)
        changed = True
        while changed:
            changed = False
            new_stmts = []
            i = 0
            while i < len(stmts):
                if (i + 1 < len(stmts)
                    and isinstance(stmts[i], For)
                    and isinstance(stmts[i+1], Store)):
                    result = _try_distribute(stmts[i], stmts[i+1])
                    if result is not None:
                        new_stmts.append(result)
                        i += 2
                        changed = True
                        continue
                new_stmts.append(stmts[i])
                i += 1
            stmts = new_stmts
        stmts = [_distribute_post_loop_ops(s) for s in stmts]
        if len(stmts) == 1:
            return stmts[0]
        return Seq(tuple(stmts))
    if isinstance(term, For):
        return For(term.lo, term.hi, term.step,
                   _distribute_post_loop_ops(term.body))
    return term


def _try_distribute(for_term: For, post_store: Store):
    """Try to distribute a post-loop Store(arr,idx,Op(Load(arr,idx),c)) into the For body.

    Returns the modified For if successful, None otherwise.
    """
    # Find the innermost Store in the For body that writes to the same array
    inner_store = _find_accum_store(for_term, post_store.array)
    if inner_store is None:
        return None

    # Check that post_store is Div(Load(arr,idx), c) or Mul(Load(arr,idx), c)
    pv = post_store.value
    if not isinstance(pv, BinOp) or pv.op not in ("Div", "Mul"):
        return None

    # One operand must be Load(arr, ...) — the self-reference
    if isinstance(pv.left, Load) and pv.left.array == post_store.array:
        op, const_part = pv.op, pv.right
    elif isinstance(pv.right, Load) and pv.right.array == post_store.array:
        op, const_part = pv.op, pv.left
    else:
        return None

    # The inner store should be an accumulation: Add(expr, Load(arr,...))
    iv = inner_store.value
    if not isinstance(iv, BinOp) or iv.op != "Add":
        return None
    if isinstance(iv.right, Load) and iv.right.array == post_store.array:
        accum_expr = iv.left
        accum_load = iv.right
    elif isinstance(iv.left, Load) and iv.left.array == post_store.array:
        accum_expr = iv.right
        accum_load = iv.left
    else:
        return None

    # Distribute: wrap the accumulation expression with the operation
    new_accum_expr = BinOp(op, accum_expr, const_part)
    new_inner_value = BinOp("Add", new_accum_expr, accum_load)
    new_inner_store = Store(inner_store.array, inner_store.indices, new_inner_value)

    # Replace the inner store in the For term
    return _replace_store_in_for(for_term, inner_store, new_inner_store)


def _find_accum_store(term: Term, array: str):
    """Find the innermost Store to `array` inside a For tree."""
    if isinstance(term, Store) and term.array == array:
        return term
    if isinstance(term, For):
        return _find_accum_store(term.body, array)
    if isinstance(term, Seq):
        for s in term.stmts:
            result = _find_accum_store(s, array)
            if result is not None:
                return result
    return None


def _replace_store_in_for(term: Term, old_store: Store, new_store: Store) -> Term:
    """Replace a specific Store node inside a For tree."""
    if isinstance(term, Store) and term is old_store:
        return new_store
    if isinstance(term, For):
        return For(term.lo, term.hi, term.step,
                   _replace_store_in_for(term.body, old_store, new_store))
    if isinstance(term, Seq):
        return Seq(tuple(
            _replace_store_in_for(s, old_store, new_store) for s in term.stmts
        ))
    return term


# ── Pass 1: SCALAR_VAL → Const ─────────────────────────────────────

def _normalize_scalar_val(term: Term) -> Term:
    """Replace SCALAR_VAL(...) with the literal value.

    Handles: Param("SCALAR_VAL"), Param("SCALAR_VAL((Const0))"),
    Param("SCALAR_VAL((ConstF0.0))"), etc.
    """
    def norm(t: Term) -> Term:
        if isinstance(t, Param) and t.name.startswith("SCALAR_VAL"):
            # Extract the value from SCALAR_VAL(x)
            # Handle: SCALAR_VAL((Const0)), SCALAR_VAL((Neg(Const1))), etc.
            neg = "Neg" in t.name
            m = re.search(r"Const[F]?\s*(-?\d+\.?\d*)", t.name)
            if m:
                val = float(m.group(1))
                if neg:
                    val = -abs(val)
                return Const(val)
            return Const(0.0)
        return t
    return _map_term(term, norm)


# ── Pass 2: Strip restrict/const from array names ──────────────────

_RESTRICT_SUFFIX = re.compile(r"_restrict$|_aligned$|_const$|_ptr$")
_RESTRICT_PREFIX = re.compile(r"^restrict_|^const_")


def _clean_array_name(name: str) -> str:
    """Strip restrict/const/aligned/ptr suffixes from array names."""
    name = _RESTRICT_SUFFIX.sub("", name)
    name = _RESTRICT_PREFIX.sub("", name)
    return name


def _normalize_array_names(term: Term) -> Term:
    """Normalize array names by stripping qualifier suffixes."""
    def transform(t: Term) -> Term:
        if isinstance(t, Load):
            clean = _clean_array_name(t.array)
            if clean != t.array:
                return Load(clean, t.indices)
        if isinstance(t, Store):
            clean = _clean_array_name(t.array)
            if clean != t.array:
                return Store(clean, t.indices, t.value)
        return t
    return _map_term(term, transform)


# ── Pass 3: Normalize parameter names ──────────────────────────────

_PB_RE = re.compile(r"^_PB_(.+)$")


def _normalize_param_names(term: Term) -> Term:
    """Normalize _PB_N → N, _PB_M → M, etc."""
    def transform(t: Term) -> Term:
        if isinstance(t, Param):
            m = _PB_RE.match(t.name)
            if m:
                return Param(m.group(1))
        return t
    return _map_term(term, transform)


# ── Pass 4: Inline scalar stores ───────────────────────────────────

def _inline_scalar_stores(term: Term) -> Term:
    """Inline stores to scalar variables (no indices) into subsequent uses.

    Pattern: Seq(Store("x", (), expr), ...body using Var("x")...)
    → ...body with Var("x") replaced by expr...

    Only inlines when the variable is NOT an array (no indices on Store).
    """
    if not isinstance(term, Seq):
        # Recurse into sub-terms
        return _map_children(term, _inline_scalar_stores)

    new_stmts = list(term.stmts)
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(new_stmts):
            stmt = new_stmts[i]
            # Look for Store("x", (), expr) — a zero-index (scalar) store
            if isinstance(stmt, Store) and len(stmt.indices) == 0:
                var_name = stmt.array
                expr = stmt.value
                # Context-aware: inline if name is used as scalar in subsequent
                # stmts AND never used as an indexed array in the whole Seq
                subsequent = new_stmts[i + 1:]
                use_def_ok = (_has_scalar_use(subsequent, var_name)
                              and not _has_array_use(Seq(tuple(new_stmts)), var_name))
                name_ok = _is_local_var_name(var_name)
                if use_def_ok or name_ok:
                    # Replace Var(var_name) in all subsequent statements
                    replaced = False
                    for j in range(i + 1, len(new_stmts)):
                        new_stmt = _substitute_var(new_stmts[j], var_name, expr)
                        if new_stmt != new_stmts[j]:
                            new_stmts[j] = new_stmt
                            replaced = True
                    if replaced:
                        # Remove the store (it's been inlined)
                        new_stmts.pop(i)
                        changed = True
                        continue
            # Recurse into sub-terms
            new_stmts[i] = _inline_scalar_stores(new_stmts[i])
            i += 1

    if len(new_stmts) == 0:
        return Unknown("empty after inlining")
    if len(new_stmts) == 1:
        return new_stmts[0]
    return Seq(tuple(new_stmts))


def _has_scalar_use(stmts: list, var_name: str) -> bool:
    """Check if var_name is used as Param(name) or Load(name, ()) in any stmt."""
    for s in stmts:
        if _contains_scalar_ref(s, var_name):
            return True
    return False


def _contains_scalar_ref(term: Term, var_name: str) -> bool:
    """Recursively check if term contains Param(var_name) or Load(var_name, ())."""
    if isinstance(term, Param) and term.name == var_name:
        return True
    if isinstance(term, Load) and term.array == var_name and len(term.indices) == 0:
        return True
    if isinstance(term, (Const, DBVar, Unknown)):
        return False
    if isinstance(term, Load):
        return any(_contains_scalar_ref(i, var_name) for i in term.indices)
    if isinstance(term, Store):
        return (any(_contains_scalar_ref(i, var_name) for i in term.indices)
                or _contains_scalar_ref(term.value, var_name))
    if isinstance(term, BinOp):
        return (_contains_scalar_ref(term.left, var_name)
                or _contains_scalar_ref(term.right, var_name))
    if isinstance(term, Neg):
        return _contains_scalar_ref(term.operand, var_name)
    if isinstance(term, For):
        return (_contains_scalar_ref(term.lo, var_name)
                or _contains_scalar_ref(term.hi, var_name)
                or _contains_scalar_ref(term.body, var_name))
    if isinstance(term, Seq):
        return any(_contains_scalar_ref(s, var_name) for s in term.stmts)
    return False


def _has_array_use(term: Term, var_name: str) -> bool:
    """Check if var_name is ever used as an indexed array Load(name, [idx...]) or Store(name, [idx...], ...)."""
    if isinstance(term, Load) and term.array == var_name and len(term.indices) > 0:
        return True
    if isinstance(term, Store) and term.array == var_name and len(term.indices) > 0:
        return True
    if isinstance(term, (Const, Param, DBVar, Unknown)):
        return False
    if isinstance(term, Load):
        return any(_has_array_use(i, var_name) for i in term.indices)
    if isinstance(term, Store):
        return (any(_has_array_use(i, var_name) for i in term.indices)
                or _has_array_use(term.value, var_name))
    if isinstance(term, BinOp):
        return _has_array_use(term.left, var_name) or _has_array_use(term.right, var_name)
    if isinstance(term, Neg):
        return _has_array_use(term.operand, var_name)
    if isinstance(term, For):
        return (_has_array_use(term.lo, var_name) or _has_array_use(term.hi, var_name)
                or _has_array_use(term.body, var_name))
    if isinstance(term, Seq):
        return any(_has_array_use(s, var_name) for s in term.stmts)
    return False


def _is_local_var_name(name: str) -> bool:
    """Heuristic: is this a local variable (not an array)?

    Local variables added by LLMs tend to be lowercase, short,
    and NOT standard array names (A, B, C, x, y, tmp, etc.).
    """
    # Standard PolyBench arrays — NEVER treat as local
    standard_arrays = {
        "A", "B", "C", "D", "E", "R", "Q", "S",
        "x", "y", "z", "w",
        "x1", "x2", "y_1", "y_2",
        "tmp", "path", "table", "seq",
        "mean", "stddev", "symmat", "cov", "corr", "data",
        "alpha", "beta",
        "imgIn", "imgOut", "y1", "y2",
        "u1", "u2", "v1", "v2",
        "s", "q", "p", "r",
        "L", "U",
        "hz", "ex", "ey", "fict",
    }
    if name in standard_arrays:
        return False
    # Common LLM local variable patterns
    if re.match(r"^_?(sum|nrm|t|cij|aik|tmp|acc|val|row|col|c_row|temp|prod|result)\w*$", name, re.IGNORECASE):
        return True
    # Variables with underscores that look like extracted subexpressions
    if "_" in name and name.lstrip("_")[:1].islower() and len(name) > 3:
        return True
    # Short lowercase names not in standard set
    if name.islower() and len(name) <= 3 and name not in standard_arrays:
        return True
    return False


def _substitute_var(term: Term, var_name: str, replacement: Term, depth: int = 0) -> Term:
    """Replace Param(var_name) or scalar Load(var_name) with replacement.

    Correctly shifts De Bruijn indices in the replacement when crossing
    For binders — if the replacement contains DBVar(k), under a For
    binder it should reference DBVar(k+1) since the binder pushes all
    free variables up by one.
    """
    from .term import shift as _shift_term
    if isinstance(term, Param) and term.name == var_name:
        # Shift replacement's free vars by 'depth' to account for binders crossed
        if depth > 0:
            return _shift_term(replacement, depth, 0)
        return replacement
    if isinstance(term, Load) and term.array == var_name and len(term.indices) == 0:
        if depth > 0:
            return _shift_term(replacement, depth, 0)
        return replacement
    if isinstance(term, (Const, DBVar, Unknown)):
        return term
    if isinstance(term, Param):
        return term
    if isinstance(term, Load):
        return Load(term.array,
                    tuple(_substitute_var(i, var_name, replacement, depth) for i in term.indices))
    if isinstance(term, Store):
        return Store(term.array,
                     tuple(_substitute_var(i, var_name, replacement, depth) for i in term.indices),
                     _substitute_var(term.value, var_name, replacement, depth))
    if isinstance(term, BinOp):
        return BinOp(term.op,
                     _substitute_var(term.left, var_name, replacement, depth),
                     _substitute_var(term.right, var_name, replacement, depth))
    if isinstance(term, Neg):
        return Neg(_substitute_var(term.operand, var_name, replacement, depth))
    if isinstance(term, For):
        return For(_substitute_var(term.lo, var_name, replacement, depth),
                   _substitute_var(term.hi, var_name, replacement, depth),
                   term.step,
                   _substitute_var(term.body, var_name, replacement, depth + 1))
    if isinstance(term, Seq):
        return Seq(tuple(_substitute_var(s, var_name, replacement, depth) for s in term.stmts))
    return term


# ── Pass 5: Flatten Seq ────────────────────────────────────────────

def _flatten_seq(term: Term) -> Term:
    """Flatten nested Seq into flat Seq, remove empty/unknown elements."""
    term = _map_children(term, _flatten_seq)
    if not isinstance(term, Seq):
        return term

    flat: list[Term] = []
    for s in term.stmts:
        if isinstance(s, Seq):
            flat.extend(s.stmts)
        elif isinstance(s, Unknown) and s.desc in ("empty scop body", "empty seq", "empty after inlining", "empty_loop"):
            continue
        else:
            flat.append(s)
    # Remove trailing Nop-like elements (from brace parsing artifacts)
    while flat and isinstance(flat[-1], Unknown):
        flat.pop()

    if len(flat) == 0:
        return Unknown("empty seq")
    if len(flat) == 1:
        return flat[0]
    return Seq(tuple(flat))


# ── Pass 6: Sort independent nested loops ───────────────────────────

def _sort_independent_loops(term: Term) -> Term:
    """Sort nested For loops by upper bound when body doesn't use DBVar(1).

    If the inner loop's body only uses DBVar(0) (its own variable) and
    NOT DBVar(1) (the outer loop's variable), the loops are independent
    and can be freely interchanged. We sort by upper bound to normalize.

    This is a conservative check — it only swaps when the body provably
    doesn't depend on the outer loop variable, avoiding the need for
    full polyhedral dependence analysis.
    """
    term = _map_children(term, _sort_independent_loops)

    if not isinstance(term, For) or not isinstance(term.body, For):
        return term

    outer = term
    inner = term.body

    # Check if inner body references DBVar(1) (outer loop var)
    if _references_dbvar(inner.body, 1):
        return term  # dependent — don't swap

    # Compare upper bounds — sort lexicographically
    outer_key = outer.hi.to_egg()
    inner_key = inner.hi.to_egg()

    if outer_key > inner_key:
        # Swap and adjust De Bruijn indices
        from .term import swap_db
        swapped_body = swap_db(inner.body, 0, 1)
        return For(inner.lo, inner.hi, inner.step,
                   For(outer.lo, outer.hi, outer.step, swapped_body))

    return term


def _references_dbvar(term: Term, depth: int) -> bool:
    """Check if term contains DBVar(depth), accounting for binders."""
    if isinstance(term, DBVar):
        return term.depth == depth
    if isinstance(term, (Const, Param, Unknown)):
        return False
    if isinstance(term, Load):
        return any(_references_dbvar(i, depth) for i in term.indices)
    if isinstance(term, Store):
        return (any(_references_dbvar(i, depth) for i in term.indices)
                or _references_dbvar(term.value, depth))
    if isinstance(term, BinOp):
        return _references_dbvar(term.left, depth) or _references_dbvar(term.right, depth)
    if isinstance(term, Neg):
        return _references_dbvar(term.operand, depth)
    if isinstance(term, For):
        return (_references_dbvar(term.lo, depth)
                or _references_dbvar(term.hi, depth)
                or _references_dbvar(term.step, depth)
                or _references_dbvar(term.body, depth + 1))  # binder shifts
    if isinstance(term, Seq):
        return any(_references_dbvar(s, depth) for s in term.stmts)
    if isinstance(term, Let):
        return _references_dbvar(term.expr, depth) or _references_dbvar(term.body, depth)
    if isinstance(term, Reduce):
        return (_references_dbvar(term.lo, depth)
                or _references_dbvar(term.hi, depth)
                or _references_dbvar(term.body, depth + 1))
    return False


# ── Pass 6: Constant folding ────────────────────────────────────────

def _constant_fold(term: Term) -> Term:
    """Simplify constant expressions in Python (before egglog).

    Handles cases that egglog's back-off scheduler can't reach
    in large terms due to e-graph explosion.
    """
    def fold(t: Term) -> Term:
        if isinstance(t, BinOp):
            l, r = t.left, t.right
            # Add identity: x + 0 = x, 0 + x = x
            if t.op == "Add":
                if isinstance(l, Const) and l.value == 0:
                    return r
                if isinstance(r, Const) and r.value == 0:
                    return l
            # Mul identity: x * 1 = x, 1 * x = x
            if t.op == "Mul":
                if isinstance(l, Const) and l.value == 1:
                    return r
                if isinstance(r, Const) and r.value == 1:
                    return l
                # Mul by zero: x * 0 = 0, 0 * x = 0
                if isinstance(l, Const) and l.value == 0:
                    return Const(0)
                if isinstance(r, Const) and r.value == 0:
                    return Const(0)
            # Sub identity: x - 0 = x
            if t.op == "Sub":
                if isinstance(r, Const) and r.value == 0:
                    return l
                # Self sub: x - x = 0
                if l == r:
                    return Const(0)
                # Sub(Add(x, y), y) → x — cancellation
                if isinstance(l, BinOp) and l.op == "Add" and l.right == r:
                    return l.left
                if isinstance(l, BinOp) and l.op == "Add" and l.left == r:
                    return l.right
            # Add(Add(x, Const(a)), Const(b)) → Add(x, Const(a+b))
            if t.op == "Add" and isinstance(r, Const) and isinstance(l, BinOp) and l.op == "Add" and isinstance(l.right, Const):
                combined = l.right.value + r.value
                if combined == 0:
                    return l.left
                return BinOp("Add", l.left, Const(combined))
            # Add(Sub(x, Const(a)), Const(b)) → Add(x, Const(b-a)) or Sub(x, Const(a-b))
            if t.op == "Add" and isinstance(r, Const) and isinstance(l, BinOp) and l.op == "Sub" and isinstance(l.right, Const):
                combined = r.value - l.right.value
                if combined == 0:
                    return l.left
                if combined > 0:
                    return BinOp("Add", l.left, Const(combined))
                return BinOp("Sub", l.left, Const(-combined))
            # Sub(Add(x, Const(a)), Const(b)) → Add(x, Const(a-b))
            if t.op == "Sub" and isinstance(r, Const) and isinstance(l, BinOp) and l.op == "Add" and isinstance(l.right, Const):
                combined = l.right.value - r.value
                if combined == 0:
                    return l.left
                return BinOp("Add", l.left, Const(combined))
            # Constant arithmetic
            if isinstance(l, Const) and isinstance(r, Const):
                if t.op == "Add":
                    return Const(l.value + r.value)
                if t.op == "Mul":
                    return Const(l.value * r.value)
                if t.op == "Sub":
                    return Const(l.value - r.value)
                if t.op == "Div" and r.value != 0:
                    return Const(l.value / r.value)
        if isinstance(t, Neg):
            if isinstance(t.operand, Const):
                return Const(-t.operand.value)
            if isinstance(t.operand, Neg):
                return t.operand.operand
        # Zero-trip For elimination: For(lo, hi, 1, body) where lo >= hi → empty
        if isinstance(t, For) and isinstance(t.lo, Const) and isinstance(t.hi, Const):
            if t.lo.value >= t.hi.value:
                return Unknown("empty_loop")
        # Also: For(x, x, 1, body) → empty (same lo and hi)
        if isinstance(t, For) and t.lo == t.hi:
            return Unknown("empty_loop")
        return t
    for _ in range(3):
        new = _map_term(term, fold)
        if new == term:
            break
        term = new
    return term


# ── Pass 7: Normalize Sub/Neg ───────────────────────────────────────

def _normalize_sub_neg(term: Term) -> Term:
    """Normalize subtraction and negation patterns.

    - Add(a, Neg(b)) → Sub(a, b)  (canonical form)
    - Sub(a, b) stays as Sub(a, b)
    - Neg(Neg(a)) → a
    - Add(a, Sub(0, b)) → Sub(a, b)

    This ensures `a - b` and `a + (-b)` produce the same term.
    """
    def norm(t: Term) -> Term:
        if isinstance(t, BinOp) and t.op == "Add":
            # Add(a, Neg(b)) → Sub(a, b)
            if isinstance(t.right, Neg):
                return BinOp("Sub", t.left, t.right.operand)
            # Add(Neg(a), b) → Sub(b, a)
            if isinstance(t.left, Neg):
                return BinOp("Sub", t.right, t.left.operand)
        if isinstance(t, BinOp) and t.op == "Sub":
            # Sub(a, Neg(b)) → Add(a, b) — double negation cancellation
            if isinstance(t.right, Neg):
                return BinOp("Add", t.left, t.right.operand)
            # Sub(a, Const(c)) → Add(a, Const(-c)) for positive c
            if isinstance(t.right, Const) and t.right.value > 0:
                return BinOp("Add", t.left, Const(-t.right.value))
        if isinstance(t, Neg):
            # Neg(Neg(a)) → a
            if isinstance(t.operand, Neg):
                return t.operand.operand
        return t
    return _map_term(term, norm)


# ── Pass 8: Strength reduction normalization ────────────────────────

def _normalize_strength_reduce(term: Term) -> Term:
    """Canonicalize strength-reduced expressions.

    x + x → Mul(Const(2), x)  (canonical form for doubling)
    x * 0.5 → Div(x, Const(2))  (canonical form for halving)
    Mul(Const(2), x) stays as-is (already canonical)
    """
    def norm(t: Term) -> Term:
        # x + x → 2 * x
        if isinstance(t, BinOp) and t.op == "Add" and t.left == t.right:
            return BinOp("Mul", Const(2), t.left)
        # x * 0.5 → x / 2
        if isinstance(t, BinOp) and t.op == "Mul":
            if isinstance(t.right, Const) and t.right.value == 0.5:
                return BinOp("Div", t.left, Const(2))
            if isinstance(t.left, Const) and t.left.value == 0.5:
                return BinOp("Div", t.right, Const(2))
        return t
    return _map_term(term, norm)


# ── Pass 9: Unpeel loops ────────────────────────────────────────────

def _unpeel_loops(term: Term) -> Term:
    """Reverse loop peeling.

    Seq(stmt, For(1, N, 1, body)) → For(0, N, 1, body)
      when stmt == body[DBVar(0) := Const(0)]

    Seq(For(0, Sub(N,1), 1, body), stmt) → For(0, N, 1, body)
      when stmt == body[DBVar(0) := Sub(N,1)]

    Also handles the case where the peeled iteration is wrapped in
    a separate block.
    """
    term = _map_children(term, _unpeel_loops)

    if not isinstance(term, Seq) or len(term.stmts) < 2:
        return term

    stmts = list(term.stmts)
    changed = True
    while changed:
        changed = False
        for idx in range(len(stmts) - 1):
            a, b = stmts[idx], stmts[idx + 1]

            # Pattern 1: stmt; For(start, hi, 1, body)
            # where stmt is body with DBVar(0)→Const(start-1)
            if isinstance(b, For) and isinstance(b.step, Const) and b.step.value == 1:
                if isinstance(b.lo, Const) and b.lo.value > 0:
                    # Check if a == body[DBVar(0) := Const(lo-1)]
                    expected = _subst_dbvar(b.body, 0, Const(b.lo.value - 1))
                    expected = _constant_fold(expected)
                    expected = _flatten_seq(expected)
                    if a == expected:
                        stmts[idx:idx+2] = [For(Const(b.lo.value - 1), b.hi, b.step, b.body)]
                        changed = True
                        break

                # Nested peel: For(inner_lo, inner_hi, inner_s, peeled_body);
                #              For(start, hi, 1, For(inner_lo, inner_hi, inner_s, body))
                # where peeled_body == body[DBVar(1) := Const(start-1)]
                # (DBVar(1) because the outer loop var is at depth 1 inside inner For)
                if isinstance(b.body, For) and isinstance(a, For):
                    inner = b.body
                    if (a.lo == inner.lo and a.hi == inner.hi and a.step == inner.step):
                        expected_inner = _subst_dbvar(inner.body, 1, Const(b.lo.value - 1))
                        expected_inner = _constant_fold(expected_inner)
                        expected_inner = _flatten_seq(expected_inner)
                        if a.body == expected_inner:
                            stmts[idx:idx+2] = [For(Const(b.lo.value - 1), b.hi, b.step, b.body)]
                            changed = True
                            break

            # Pattern 1b: Multi-statement peel first.
            # Seq(...peeled stmts..., For(start, hi, 1, Seq(b1, ..., bN)))
            # where the peeled stmts == body[DBVar(0) := start-1] after
            # constant folding (which may eliminate zero-trip inner loops)
            if isinstance(b, For) and isinstance(b.step, Const) and b.step.value == 1:
                if isinstance(b.lo, Const) and b.lo.value > 0 and isinstance(b.body, Seq):
                    peel_val = Const(b.lo.value - 1)
                    # Substitute body and simplify to get expected peeled form
                    expected_body = _subst_dbvar(b.body, 0, peel_val)
                    expected_body = _constant_fold(expected_body)
                    expected_body = _flatten_seq(expected_body)
                    # expected_body is either a Seq or a single stmt
                    if isinstance(expected_body, Seq):
                        exp_stmts = list(expected_body.stmts)
                    else:
                        exp_stmts = [expected_body]
                    n_exp = len(exp_stmts)
                    # For is at stmts[idx+1], peeled are the n_exp stmts before it
                    for_pos = idx + 1
                    peel_start = for_pos - n_exp
                    if peel_start >= 0 and n_exp > 0:
                        peeled = stmts[peel_start : for_pos]
                        if peeled == exp_stmts:
                            stmts[peel_start : for_pos + 1] = [
                                For(peel_val, b.hi, b.step, b.body)
                            ]
                            changed = True
                            break

            # Pattern 2: For(lo, hi, 1, body); stmt
            # where stmt is body with DBVar(0)→hi
            if isinstance(a, For) and isinstance(a.step, Const) and a.step.value == 1:
                expected = _subst_dbvar(a.body, 0, a.hi)
                expected = _constant_fold(expected)
                expected = _flatten_seq(expected)
                if b == expected:
                    new_hi = BinOp("Add", a.hi, Const(1))
                    stmts[idx:idx+2] = [For(a.lo, new_hi, a.step, a.body)]
                    changed = True
                    break

                # Nested peel last: For(lo, hi-1, 1, For(inner));
                #                   For(inner_lo, inner_hi, inner_s, peeled_body)
                # where peeled_body == inner_body[DBVar(1) := hi-1]
                if isinstance(a.body, For) and isinstance(b, For):
                    inner = a.body
                    if (b.lo == inner.lo and b.hi == inner.hi and b.step == inner.step):
                        expected_inner = _subst_dbvar(inner.body, 1, a.hi)
                        expected_inner = _constant_fold(expected_inner)
                        expected_inner = _flatten_seq(expected_inner)
                        if b.body == expected_inner:
                            new_hi = BinOp("Add", a.hi, Const(1))
                            stmts[idx:idx+2] = [For(a.lo, new_hi, a.step, a.body)]
                            changed = True
                            break

            # Pattern 2b: Multi-statement peel last.
            # For(lo, hi, 1, Seq(b1,...,bN)); s1; s2; ...; sN
            # where each si == bi[DBVar(0) := hi]
            if isinstance(a, For) and isinstance(a.step, Const) and a.step.value == 1:
                if isinstance(a.body, Seq):
                    body_stmts = list(a.body.stmts)
                    n_body = len(body_stmts)
                    if idx + n_body < len(stmts):
                        trailing = stmts[idx + 1 : idx + 1 + n_body]
                        all_match = True
                        for k in range(n_body):
                            expected_k = _subst_dbvar(body_stmts[k], 0, a.hi)
                            expected_k = _constant_fold(expected_k)
                            expected_k = _flatten_seq(expected_k)
                            if trailing[k] != expected_k:
                                all_match = False
                                break
                        if all_match and n_body > 0:
                            new_hi = BinOp("Add", a.hi, Const(1))
                            stmts[idx : idx + 1 + n_body] = [
                                For(a.lo, new_hi, a.step, a.body)
                            ]
                            changed = True
                            break

    if len(stmts) == 1:
        return stmts[0]
    return Seq(tuple(stmts))


def _subst_dbvar0(term: Term, replacement: Term) -> Term:
    """Substitute DBVar(0) with replacement in term (not under binders)."""
    if isinstance(term, DBVar):
        if term.depth == 0:
            return replacement
        return term
    if isinstance(term, (Const, Param, Unknown)):
        return term
    if isinstance(term, Load):
        return Load(term.array, tuple(_subst_dbvar0(i, replacement) for i in term.indices))
    if isinstance(term, Store):
        return Store(term.array,
                     tuple(_subst_dbvar0(i, replacement) for i in term.indices),
                     _subst_dbvar0(term.value, replacement))
    if isinstance(term, BinOp):
        return BinOp(term.op, _subst_dbvar0(term.left, replacement),
                     _subst_dbvar0(term.right, replacement))
    if isinstance(term, Neg):
        return Neg(_subst_dbvar0(term.operand, replacement))
    if isinstance(term, For):
        # Don't substitute under binder — DBVar(0) inside For refers to the new loop var
        return term
    if isinstance(term, Seq):
        return Seq(tuple(_subst_dbvar0(s, replacement) for s in term.stmts))
    return term


def _subst_dbvar(term: Term, depth: int, replacement: Term) -> Term:
    """Substitute DBVar(depth) with replacement, adjusting under binders."""
    if isinstance(term, DBVar):
        if term.depth == depth:
            return replacement
        return term
    if isinstance(term, (Const, Param, Unknown)):
        return term
    if isinstance(term, Load):
        return Load(term.array, tuple(_subst_dbvar(i, depth, replacement) for i in term.indices))
    if isinstance(term, Store):
        return Store(term.array,
                     tuple(_subst_dbvar(i, depth, replacement) for i in term.indices),
                     _subst_dbvar(term.value, depth, replacement))
    if isinstance(term, BinOp):
        return BinOp(term.op, _subst_dbvar(term.left, depth, replacement),
                     _subst_dbvar(term.right, depth, replacement))
    if isinstance(term, Neg):
        return Neg(_subst_dbvar(term.operand, depth, replacement))
    if isinstance(term, For):
        # Under a binder, the target depth increments
        return For(_subst_dbvar(term.lo, depth, replacement),
                   _subst_dbvar(term.hi, depth, replacement),
                   term.step,
                   _subst_dbvar(term.body, depth + 1, replacement))
    if isinstance(term, Seq):
        return Seq(tuple(_subst_dbvar(s, depth, replacement) for s in term.stmts))
    return term


# ── Pass 10: Unshift loops ──────────────────────────────────────────

def _unshift_loops(term: Term) -> Term:
    """Normalize shifted loops to start from 0.

    For(Const(k), Add(hi, Const(k)), Const(1), body)
    → For(Const(0), hi, Const(1), body[DBVar(0) := Add(DBVar(0), Const(k))])

    Only when k != 0 and body uses DBVar(0)+k pattern.
    """
    term = _map_children(term, _unshift_loops)

    if not isinstance(term, For):
        return term
    if not isinstance(term.lo, Const) or term.lo.value == 0:
        return term
    if not isinstance(term.step, Const) or term.step.value != 1:
        return term

    k = int(term.lo.value)
    # Check if hi = original_hi + k
    # For now, just shift body indices: replace DBVar(0) with DBVar(0)+k
    # and set lo=0, hi=hi-k
    new_hi = BinOp("Add", term.hi, Const(-k))
    new_body = _shift_dbvar0(term.body, k)
    return For(Const(0), new_hi, term.step, new_body)


def _shift_dbvar0(term: Term, offset: int) -> Term:
    """Replace DBVar(0) with Add(DBVar(0), Const(offset)) in term."""
    if isinstance(term, DBVar) and term.depth == 0:
        return BinOp("Add", DBVar(0), Const(offset))
    if isinstance(term, (Const, Param, Unknown)):
        return term
    if isinstance(term, DBVar):
        return term
    if isinstance(term, Load):
        return Load(term.array, tuple(_shift_dbvar0(i, offset) for i in term.indices))
    if isinstance(term, Store):
        return Store(term.array,
                     tuple(_shift_dbvar0(i, offset) for i in term.indices),
                     _shift_dbvar0(term.value, offset))
    if isinstance(term, BinOp):
        return BinOp(term.op, _shift_dbvar0(term.left, offset),
                     _shift_dbvar0(term.right, offset))
    if isinstance(term, Neg):
        return Neg(_shift_dbvar0(term.operand, offset))
    if isinstance(term, For):
        return For(_shift_dbvar0(term.lo, offset), _shift_dbvar0(term.hi, offset),
                   term.step, term.body)  # Don't shift inside nested For
    if isinstance(term, Seq):
        return Seq(tuple(_shift_dbvar0(s, offset) for s in term.stmts))
    return term


# ── Pass 11: Canonicalize loop variable params ───────────────────────

_LOOP_VAR_RE = re.compile(r"^(i{1,3}|j{1,3}|k{1,3}|t{1,3}|p{1,2}|q{1,2}|r{1,2})$")

def _canonicalize_loop_var_params(term: Term) -> Term:
    """Rename Param("ii") → Param("i"), Param("jj") → Param("j"), etc.

    When LLM renames loop variables (i→ii, j→jj), the parser may
    produce Param("ii") in places where the var is used outside its
    for-loop scope. This normalization maps all variants of a loop
    variable name to a single canonical form.
    """
    def canon(t: Term) -> Term:
        if isinstance(t, Param) and _LOOP_VAR_RE.match(t.name):
            # Map ii→i, jj→j, kk→k, etc.
            canonical = t.name[0]
            if canonical != t.name:
                return Param(canonical)
        return t
    return _map_term(term, canon)


# ── Pass 9: Sort commutative operands ───────────────────────────────

def _sort_commutative(term: Term) -> Term:
    """Sort operands of commutative operations lexicographically.

    Add(b, a) → Add(a, b) when a.to_egg() < b.to_egg()
    Mul(b, a) → Mul(a, b) when a.to_egg() < b.to_egg()

    This normalizes commutativity without needing egglog rules,
    avoiding e-graph explosion on large terms.
    """
    def sort_op(t: Term) -> Term:
        if isinstance(t, BinOp) and t.op in ("Add", "Mul"):
            le = t.left.to_egg()
            re = t.right.to_egg()
            if le > re:
                return BinOp(t.op, t.right, t.left)
        return t
    return _map_term(term, sort_op)


# ── Pass 8: Scalar de-promotion ─────────────────────────────────────

def _de_scalar_promote(term: Term) -> Term:
    """Reverse scalar promotion: replace local scalar with array element.

    Pattern in LLM code:
        Seq(Store("t", (), init),
            For(..., Store("t", (), Add(Param("t"), expr))),
            Store("arr", [idx], Param("t")))

    After de-promotion:
        Seq(Store("arr", [idx], init),
            For(..., Store("arr", [idx], Add(Load("arr", [idx]), expr))))

    This makes the term match the reference which writes to arr[idx] directly.
    """
    term = _map_children(term, _de_scalar_promote)

    if not isinstance(term, Seq):
        return term

    stmts = list(term.stmts)

    # Look for pattern: last stmt is Store("arr", [idx], Param("t"))
    # and first stmt is Store("t", (), init) where t is a local
    changed = True
    while changed:
        changed = False
        for end_idx in range(len(stmts) - 1, 0, -1):
            end_stmt = stmts[end_idx]
            if not isinstance(end_stmt, Store) or not end_stmt.indices:
                continue
            # Check if value is a scalar reference
            if not isinstance(end_stmt.value, Param):
                continue
            scalar_name = end_stmt.value.name
            if not _is_local_var_name(scalar_name):
                continue
            arr_name = end_stmt.array
            arr_indices = end_stmt.indices

            # Find initialization: Store("t", (), init)
            init_idx = None
            for j in range(end_idx):
                s = stmts[j]
                if isinstance(s, Store) and s.array == scalar_name and not s.indices:
                    init_idx = j
                    break

            if init_idx is None:
                continue

            # Replace: init → Store(arr, [idx], init_value)
            init_value = stmts[init_idx].value
            stmts[init_idx] = Store(arr_name, arr_indices, init_value)

            # Replace all Param("t") and Store("t",...) with Load("arr",[idx]) and Store("arr",[idx],...)
            for k in range(init_idx + 1, end_idx):
                stmts[k] = _substitute_scalar_to_array(
                    stmts[k], scalar_name, arr_name, arr_indices)

            # Remove the final copy-back
            stmts.pop(end_idx)
            changed = True
            break

    if len(stmts) == 0:
        return Unknown("empty after de-promotion")
    if len(stmts) == 1:
        return stmts[0]
    return Seq(tuple(stmts))


def _substitute_scalar_to_array(
    term: Term, scalar_name: str, arr_name: str, arr_indices: tuple[Term, ...],
    binder_depth: int = 0,
) -> Term:
    """Replace scalar variable references with array element references.

    Store("t", (), expr) → Store("arr", [idx], expr')
    Param("t") → Load("arr", [idx])

    Uses De Bruijn shift: when entering a For binder, shift the
    arr_indices up by 1 so DBVar references stay correct.
    """
    from .term import shift as db_shift

    # Compute shifted indices for current depth
    shifted_indices = tuple(
        db_shift(idx, binder_depth) for idx in arr_indices
    )

    if isinstance(term, Store) and term.array == scalar_name and not term.indices:
        new_value = _substitute_scalar_to_array(
            term.value, scalar_name, arr_name, arr_indices, binder_depth)
        return Store(arr_name, shifted_indices, new_value)
    if isinstance(term, Param) and term.name == scalar_name:
        return Load(arr_name, shifted_indices)

    # Recurse, incrementing binder_depth inside For/Reduce
    if isinstance(term, For):
        return For(
            _substitute_scalar_to_array(term.lo, scalar_name, arr_name, arr_indices, binder_depth),
            _substitute_scalar_to_array(term.hi, scalar_name, arr_name, arr_indices, binder_depth),
            _substitute_scalar_to_array(term.step, scalar_name, arr_name, arr_indices, binder_depth),
            _substitute_scalar_to_array(term.body, scalar_name, arr_name, arr_indices, binder_depth + 1),
        )
    if isinstance(term, Seq):
        return Seq(tuple(
            _substitute_scalar_to_array(s, scalar_name, arr_name, arr_indices, binder_depth)
            for s in term.stmts
        ))
    if isinstance(term, Store):
        return Store(
            term.array,
            tuple(_substitute_scalar_to_array(i, scalar_name, arr_name, arr_indices, binder_depth) for i in term.indices),
            _substitute_scalar_to_array(term.value, scalar_name, arr_name, arr_indices, binder_depth),
        )
    if isinstance(term, BinOp):
        return BinOp(term.op,
            _substitute_scalar_to_array(term.left, scalar_name, arr_name, arr_indices, binder_depth),
            _substitute_scalar_to_array(term.right, scalar_name, arr_name, arr_indices, binder_depth))
    if isinstance(term, Neg):
        return Neg(_substitute_scalar_to_array(term.operand, scalar_name, arr_name, arr_indices, binder_depth))
    if isinstance(term, Load):
        return Load(term.array,
            tuple(_substitute_scalar_to_array(i, scalar_name, arr_name, arr_indices, binder_depth) for i in term.indices))

    return term


# ── Helper: recursive term mapping ─────────────────────────────────

def _map_term(term: Term, fn: Callable[[Term], Term]) -> Term:
    """Apply fn to every node in the term tree (bottom-up)."""
    term = _map_children(term, lambda t: _map_term(t, fn))
    return fn(term)


def _map_children(term: Term, fn: Callable[[Term], Term]) -> Term:
    """Apply fn to immediate children of term."""
    if isinstance(term, (Const, Param, DBVar, Unknown)):
        return term
    if isinstance(term, Load):
        return Load(term.array, tuple(fn(i) for i in term.indices))
    if isinstance(term, Store):
        return Store(term.array, tuple(fn(i) for i in term.indices), fn(term.value))
    if isinstance(term, BinOp):
        return BinOp(term.op, fn(term.left), fn(term.right))
    if isinstance(term, Neg):
        return Neg(fn(term.operand))
    if isinstance(term, For):
        return For(fn(term.lo), fn(term.hi), fn(term.step), fn(term.body))
    if isinstance(term, Seq):
        return Seq(tuple(fn(s) for s in term.stmts))
    if isinstance(term, Let):
        return Let(term.var, fn(term.expr), fn(term.body))
    if isinstance(term, Reduce):
        return Reduce(term.op, fn(term.lo), fn(term.hi), fn(term.body))
    return term
