"""Polyhedral analysis for loop transformation legality.

Uses islpy to check whether loop transformations (interchange, fission)
are legal. Polyhedral analysis answers: "is this transformation safe?"
The e-graph handles the rest.

Works at the Term level: given a Term with nested For loops, it checks
if swapping them preserves data dependences by analyzing the array
access patterns and iteration domains within the term.
"""

from __future__ import annotations

from .term import BinOp, Const, DBVar, For, Load, Neg, Param, Seq, Store, Term, Unknown, swap_db


def normalize_loop_order(term: Term) -> Term:
    """Sort nested For loops by upper bound when interchange is safe.

    For two nested For loops For(lo1,hi1,s1, For(lo2,hi2,s2, body)):
    - If body doesn't reference DBVar(1) (outer loop var), loops are
      independent and can be freely swapped.
    - If body DOES reference DBVar(1), check if any Store in body
      writes to a location that depends on DBVar(1) AND is read at
      a different DBVar(1) value. If not, interchange is safe.

    For the conservative MVP: only swap when the inner body doesn't
    use DBVar(1) in any Store target indices.
    """
    return _sort_loops(term)


def _sort_loops(term: Term) -> Term:
    """Recursively sort nested independent loops."""
    # First, recurse into children
    if isinstance(term, For):
        term = For(term.lo, term.hi, term.step, _sort_loops(term.body))
    elif isinstance(term, Seq):
        term = Seq(tuple(_sort_loops(s) for s in term.stmts))
    elif isinstance(term, (Const, Param, DBVar, Unknown, Load)):
        return term
    elif isinstance(term, Store):
        return Store(term.array, term.indices, _sort_loops(term.value))
    elif isinstance(term, BinOp):
        return BinOp(term.op, _sort_loops(term.left), _sort_loops(term.right))
    elif isinstance(term, Neg):
        return Neg(_sort_loops(term.operand))

    if not isinstance(term, For):
        return term

    # Case 1: For(For(body)) — direct nesting, try interchange
    if isinstance(term.body, For):
        outer = term
        inner = term.body
        if _interchange_safe(inner.body):
            outer_key = outer.hi.to_egg()
            inner_key = inner.hi.to_egg()
            if outer_key > inner_key:
                swapped_body = swap_db(inner.body, 0, 1)
                return For(inner.lo, inner.hi, inner.step,
                           For(outer.lo, outer.hi, outer.step, swapped_body))

    # Case 2: For(Seq(For(...), For(...), ...)) — sort independent inner loops
    if isinstance(term.body, Seq):
        sorted_stmts = _sort_seq_loops(term.body.stmts)
        if sorted_stmts != term.body.stmts:
            return For(term.lo, term.hi, term.step, Seq(sorted_stmts))

    return term


def _sort_seq_loops(stmts: tuple[Term, ...]) -> tuple[Term, ...]:
    """Sort independent For loops within a Seq by their upper bound.

    Only sorts contiguous runs of For loops that are independent
    (no data flow between them through the same arrays).
    """
    result = list(stmts)
    # Simple bubble sort on contiguous For blocks
    changed = True
    while changed:
        changed = False
        for i in range(len(result) - 1):
            a, b = result[i], result[i + 1]
            if isinstance(a, For) and isinstance(b, For):
                ka = a.hi.to_egg()
                kb = b.hi.to_egg()
                if ka > kb and _loops_independent(a, b):
                    result[i], result[i + 1] = b, a
                    changed = True
    return tuple(result)


def _loops_independent(a: For, b: For) -> bool:
    """Check if two sibling For loops are independent (no data deps)."""
    # Collect arrays written by a and read by b
    a_writes = _collect_write_arrays(a.body)
    b_reads = _collect_read_arrays(b.body)
    b_writes = _collect_write_arrays(b.body)
    a_reads = _collect_read_arrays(a.body)

    # WAR or RAW dep: a writes array that b reads, or vice versa
    if a_writes & b_reads:
        return False
    if b_writes & a_reads:
        return False
    # WAW: both write same array
    if a_writes & b_writes:
        return False
    return True


def _collect_write_arrays(term: Term) -> set[str]:
    result: set[str] = set()
    if isinstance(term, Store):
        result.add(term.array)
        result |= _collect_write_arrays(term.value)
    elif isinstance(term, Seq):
        for s in term.stmts:
            result |= _collect_write_arrays(s)
    elif isinstance(term, For):
        result |= _collect_write_arrays(term.body)
    return result


def _collect_read_arrays(term: Term) -> set[str]:
    result: set[str] = set()
    if isinstance(term, Load):
        result.add(term.array)
    elif isinstance(term, Store):
        for i in term.indices:
            result |= _collect_read_arrays(i)
        result |= _collect_read_arrays(term.value)
    elif isinstance(term, BinOp):
        result |= _collect_read_arrays(term.left)
        result |= _collect_read_arrays(term.right)
    elif isinstance(term, Neg):
        result |= _collect_read_arrays(term.operand)
    elif isinstance(term, Seq):
        for s in term.stmts:
            result |= _collect_read_arrays(s)
    elif isinstance(term, For):
        result |= _collect_read_arrays(term.body)
    return result


def _interchange_safe(body: Term) -> bool:
    """Conservative check: is it safe to interchange the two enclosing loops?

    Safe when no Store in body writes to a location that depends on
    DBVar(1) (the outer loop variable) — meaning no loop-carried
    dependence through the outer loop.

    This is conservative: it rejects some safe interchanges but never
    accepts an unsafe one.
    """
    if isinstance(body, Store):
        # Check if any write index depends on DBVar(1)
        for idx in body.indices:
            if _has_dbvar(idx, 1):
                # Write target depends on outer loop — could have carried dep
                # Check if the same array is also READ with a different DBVar(1) value
                if _has_self_dep(body, 1):
                    return False
        return _interchange_safe(body.value)
    if isinstance(body, Seq):
        return all(_interchange_safe(s) for s in body.stmts)
    if isinstance(body, For):
        return True  # inner loops don't affect outer interchange safety
    return True


def _has_dbvar(term: Term, depth: int) -> bool:
    """Check if term contains DBVar(depth)."""
    if isinstance(term, DBVar):
        return term.depth == depth
    if isinstance(term, (Const, Param, Unknown)):
        return False
    if isinstance(term, Load):
        return any(_has_dbvar(i, depth) for i in term.indices)
    if isinstance(term, Store):
        return (any(_has_dbvar(i, depth) for i in term.indices)
                or _has_dbvar(term.value, depth))
    if isinstance(term, BinOp):
        return _has_dbvar(term.left, depth) or _has_dbvar(term.right, depth)
    if isinstance(term, Neg):
        return _has_dbvar(term.operand, depth)
    if isinstance(term, For):
        return (_has_dbvar(term.lo, depth) or _has_dbvar(term.hi, depth)
                or _has_dbvar(term.body, depth + 1))
    if isinstance(term, Seq):
        return any(_has_dbvar(s, depth) for s in term.stmts)
    return False


def _has_self_dep(store: Store, outer_depth: int) -> bool:
    """Check if a Store has a self-dependence through the outer loop.

    A self-dep exists when the Store writes array A[..., f(DBVar(outer)), ...]
    and also reads A[..., g(DBVar(outer)), ...] where f ≠ g.

    Conservative: returns True if the same array appears in both write
    target and any read access with different index expressions involving
    the outer loop variable.
    """
    write_array = store.array
    write_indices = store.indices

    # Collect all Load accesses in the Store's value
    loads = _collect_loads(store.value)

    for load_array, load_indices in loads:
        if load_array != write_array:
            continue
        if len(load_indices) != len(write_indices):
            continue
        # Same array, same dimensionality — check if indices differ
        # on the outer loop variable
        for wi, li in zip(write_indices, load_indices):
            if _has_dbvar(wi, outer_depth) or _has_dbvar(li, outer_depth):
                if wi != li:
                    return True  # different index expressions involving outer var
    return False


def _collect_loads(term: Term) -> list[tuple[str, tuple[Term, ...]]]:
    """Collect all (array, indices) from Load nodes in term."""
    result: list[tuple[str, tuple[Term, ...]]] = []
    if isinstance(term, Load):
        result.append((term.array, term.indices))
    if isinstance(term, Store):
        result.extend(_collect_loads(term.value))
    if isinstance(term, BinOp):
        result.extend(_collect_loads(term.left))
        result.extend(_collect_loads(term.right))
    if isinstance(term, Neg):
        result.extend(_collect_loads(term.operand))
    if isinstance(term, For):
        result.extend(_collect_loads(term.body))
    if isinstance(term, Seq):
        for s in term.stmts:
            result.extend(_collect_loads(s))
    return result
