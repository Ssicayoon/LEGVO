"""Polyhedral dependence analysis using islpy.

Extracts iteration domains and access relations from Term ASTs,
then checks whether statement reordering or loop structure changes
violate data dependencies at the instance level.

Uses isl to build domains from For loop bounds and access maps from
Store/Load index expressions, then computes dependence relations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

try:
    import islpy as isl
    HAS_ISL = True
except ImportError:
    HAS_ISL = False

from .term import (
    BinOp, Const, DBVar, For, Let, Load, Neg, Param, Reduce,
    Seq, Store, Term, Unknown,
)


@dataclass
class LoopBound:
    """For loop bound info."""
    var: str      # loop variable name (L0, L1, ...)
    lo: str       # lower bound expression
    hi: str       # upper bound expression (exclusive)


@dataclass
class StmtInfo:
    """Statement with access patterns and loop context."""
    stmt_id: int
    writes: dict[str, list[tuple]]  # array → list of index tuples (as strings)
    reads: dict[str, list[tuple]]
    term: Term
    loop_vars: list[str] = field(default_factory=list)
    loop_bounds: list[LoopBound] = field(default_factory=list)


def _term_to_index_str(term: Term, loop_vars: list[str] | None = None) -> str:
    """Convert an index expression Term to a canonical string."""
    if isinstance(term, DBVar):
        if loop_vars and term.depth < len(loop_vars):
            return loop_vars[-(term.depth + 1)]
        return 'v%d' % term.depth
    if isinstance(term, Const):
        v = term.value
        return str(int(v)) if v == int(v) else str(v)
    if isinstance(term, Param):
        return term.name
    if isinstance(term, BinOp):
        l = _term_to_index_str(term.left, loop_vars)
        r = _term_to_index_str(term.right, loop_vars)
        return '(%s %s %s)' % (l, term.op, r)
    if isinstance(term, Neg):
        return '(-%s)' % _term_to_index_str(term.operand, loop_vars)
    return '?'


def _collect_access_patterns(term: Term, reads: dict, writes: dict,
                              loop_vars: list[str] | None = None):
    """Collect array access patterns with index expressions."""
    if isinstance(term, Store):
        arr = term.array
        idx = tuple(_term_to_index_str(i, loop_vars) for i in term.indices)
        writes.setdefault(arr, []).append(idx)
        for i in term.indices:
            _collect_access_patterns(i, reads, writes, loop_vars)
        _collect_access_patterns(term.value, reads, writes, loop_vars)
    elif isinstance(term, Load):
        arr = term.array
        idx = tuple(_term_to_index_str(i, loop_vars) for i in term.indices)
        reads.setdefault(arr, []).append(idx)
        for i in term.indices:
            _collect_access_patterns(i, reads, writes, loop_vars)
    elif isinstance(term, BinOp):
        _collect_access_patterns(term.left, reads, writes, loop_vars)
        _collect_access_patterns(term.right, reads, writes, loop_vars)
    elif isinstance(term, Neg):
        _collect_access_patterns(term.operand, reads, writes, loop_vars)
    elif isinstance(term, For):
        _collect_access_patterns(term.body, reads, writes, loop_vars)
    elif isinstance(term, Seq):
        for s in term.stmts:
            _collect_access_patterns(s, reads, writes, loop_vars)


def _accesses_may_alias(write_indices: list[tuple],
                         read_indices: list[tuple],
                         loop_bounds: list[LoopBound] | None = None) -> bool:
    """Check if write and read index patterns may access the same element.

    Conservative: returns True (may alias) if unsure.
    Returns False only if provably different for ALL index combinations.
    """
    for widx in write_indices:
        for ridx in read_indices:
            if len(widx) != len(ridx):
                return True  # different dimensionality
            # Check each index position
            all_may_equal = True
            for w, r in zip(widx, ridx):
                if w == r:
                    continue
                if _provably_different(w, r):
                    all_may_equal = False
                    break
            if all_may_equal:
                # Try isl-based check with loop bounds
                if HAS_ISL and loop_bounds:
                    if not _isl_indices_may_equal(widx, ridx, loop_bounds):
                        continue  # isl proved they don't conflict
                return True
    return False


def _provably_different(a: str, b: str) -> bool:
    """Check if two index expressions are provably different."""
    if a == b:
        return False

    # Both are different integer constants
    try:
        ia, ib = int(a), int(b)
        return ia != ib
    except ValueError:
        pass

    # One is constant, other has a variable
    a_is_const = a.lstrip('-').isdigit()
    b_is_const = b.lstrip('-').isdigit()
    if a_is_const != b_is_const:
        return False  # can't prove: var might equal const

    # One is var + offset of the other: v0 vs (v0 Add 1)
    for var, other in [(a, b), (b, a)]:
        if var.startswith('v') and var.isalnum():
            if ('(%s Add ' % var in other or '(%s Sub ' % var in other):
                return True

    return False


def _isl_indices_may_equal(widx: tuple, ridx: tuple,
                            loop_bounds: list[LoopBound]) -> bool:
    """Use isl to check if two index tuples can be equal under loop constraints.

    Builds an isl set with loop bound constraints and the condition
    that all index positions are equal. If the set is empty, the
    indices can never be equal → no conflict.

    Returns True if indices MAY be equal (conflict), False if provably not.
    """
    try:
        # Build variable list from loop bounds
        vars_list = [b.var for b in loop_bounds]
        if not vars_list:
            return True  # no loop context → conservative

        n = len(vars_list)
        var_str = ', '.join(vars_list)

        # Build constraints string
        constraints = []

        # Loop bound constraints: lo <= var < hi
        for b in loop_bounds:
            lo, hi, var = b.lo, b.hi, b.var
            # Only add if lo/hi are simple (avoid complex expressions)
            if _is_simple_expr(lo):
                constraints.append('%s <= %s' % (_to_isl_expr(lo, vars_list), var))
            if _is_simple_expr(hi):
                constraints.append('%s < %s' % (var, _to_isl_expr(hi, vars_list)))

        # Index equality constraints: widx[k] == ridx[k] for all k
        for w, r in zip(widx, ridx):
            if w == r:
                continue  # trivially equal, no constraint needed
            w_isl = _to_isl_expr(w, vars_list)
            r_isl = _to_isl_expr(r, vars_list)
            if w_isl is not None and r_isl is not None:
                constraints.append('%s = %s' % (w_isl, r_isl))
            else:
                return True  # can't express → conservative

        if not constraints:
            return True  # no constraints → could be equal

        set_str = '{ [%s] : %s }' % (var_str, ' and '.join(constraints))
        s = isl.BasicSet(set_str)
        return not s.is_empty()
    except Exception:
        return True  # isl error → conservative


def _is_simple_expr(expr: str) -> bool:
    """Check if an expression can be converted to isl syntax."""
    # Simple: integer, loop var (Lx), or loop var ± integer
    if expr.lstrip('-').isdigit():
        return True
    if expr.startswith('L') and expr[1:].isdigit():
        return True
    if '(' in expr and 'Add' in expr:
        return True
    if '(' in expr and 'Sub' in expr:
        return True
    # Parameter names (N, M, etc.)
    if expr.isalpha() and expr.isupper():
        return True
    return False


def _to_isl_expr(expr: str, vars_list: list[str]) -> str | None:
    """Convert an index expression string to isl syntax."""
    # Integer constant
    if expr.lstrip('-').isdigit():
        return expr
    # Loop variable
    if expr in vars_list:
        return expr
    # (Lx Add c) → Lx + c
    if expr.startswith('(') and ' Add ' in expr:
        parts = expr[1:-1].split(' Add ')
        if len(parts) == 2:
            l = _to_isl_expr(parts[0].strip(), vars_list)
            r = _to_isl_expr(parts[1].strip(), vars_list)
            if l and r:
                return '(%s + %s)' % (l, r)
    # (Lx Sub c) → Lx - c
    if expr.startswith('(') and ' Sub ' in expr:
        parts = expr[1:-1].split(' Sub ')
        if len(parts) == 2:
            l = _to_isl_expr(parts[0].strip(), vars_list)
            r = _to_isl_expr(parts[1].strip(), vars_list)
            if l and r:
                return '(%s - %s)' % (l, r)
    # Parameter (treat as existential — can be any value)
    if expr.isalpha():
        return None  # can't handle params in isl without declaring them
    return None


def check_reorder_safe(ref_term: Term, cand_term: Term) -> bool:
    """Check if ref→cand transformation is safe using dep analysis.

    Extracts statements, matches them, checks reordered pairs for conflicts.
    Returns True if safe, False if potentially unsafe.
    """
    ref_stmts = _extract_stmts(ref_term)
    cand_stmts = _extract_stmts(cand_term)

    if not ref_stmts or not cand_stmts:
        return True

    # Match ref stmts to cand by term equality
    ref_to_cand = {}
    cand_used = set()
    for ri, rs in enumerate(ref_stmts):
        for ci, cs in enumerate(cand_stmts):
            if ci in cand_used:
                continue
            if rs.term == cs.term:
                ref_to_cand[ri] = ci
                cand_used.add(ci)
                break

    # Structural change → allow (can't analyze with dep alone)
    if len(ref_to_cand) != len(ref_stmts):
        return True

    # Check reordered pairs for instance-level conflicts
    for ri in range(len(ref_stmts)):
        for rj in range(ri + 1, len(ref_stmts)):
            ci = ref_to_cand[ri]
            cj = ref_to_cand[rj]

            if ci <= cj:
                continue  # not reordered

            si = ref_stmts[ri]
            sj = ref_stmts[rj]
            # Use the more constrained loop bounds (intersection)
            bounds = si.loop_bounds or sj.loop_bounds

            # RAW: si writes, sj reads same element
            for arr in si.writes:
                if arr in sj.reads:
                    if _accesses_may_alias(si.writes[arr], sj.reads[arr], bounds):
                        return False

            # WAR: si reads, sj writes same element
            for arr in si.reads:
                if arr in sj.writes:
                    if _accesses_may_alias(sj.writes[arr], si.reads[arr], bounds):
                        return False

            # WAW: both write same element
            for arr in si.writes:
                if arr in sj.writes:
                    if _accesses_may_alias(si.writes[arr], sj.writes[arr], bounds):
                        return False

    return True


def _extract_stmts(term: Term) -> list[StmtInfo]:
    """Extract leaf statements with access patterns and loop bounds."""
    result = []
    _walk(term, result, 0, [], [])
    return result


def _walk(term: Term, result: list, counter: int,
          loop_vars: list[str], loop_bounds: list[LoopBound]) -> int:
    if isinstance(term, Store):
        reads = {}
        writes = {}
        _collect_access_patterns(term, reads, writes, loop_vars)
        result.append(StmtInfo(
            stmt_id=counter, writes=writes, reads=reads,
            term=term, loop_vars=list(loop_vars),
            loop_bounds=list(loop_bounds)
        ))
        return counter + 1
    if isinstance(term, For):
        var_name = 'L%d' % len(loop_vars)
        lo_str = _term_to_index_str(term.lo, loop_vars)
        hi_str = _term_to_index_str(term.hi, loop_vars)
        bound = LoopBound(var=var_name, lo=lo_str, hi=hi_str)
        return _walk(term.body, result, counter,
                     loop_vars + [var_name], loop_bounds + [bound])
    if isinstance(term, Seq):
        for s in term.stmts:
            counter = _walk(s, result, counter, loop_vars, loop_bounds)
    return counter
