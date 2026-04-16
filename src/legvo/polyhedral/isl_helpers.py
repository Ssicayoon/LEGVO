"""isl operations for polyhedral verification, via islpy."""

from __future__ import annotations

import islpy as isl


from .model import ScopModel


# ── Comparison ──────────────────────────────────────────────────────


def sets_equal(a: str, b: str) -> bool:
    """Check if two isl union sets are semantically equal."""
    return bool(isl.UnionSet(a).is_equal(isl.UnionSet(b)))


def maps_equal(a: str, b: str) -> bool:
    """Check if two isl union maps are semantically equal."""
    return bool(isl.UnionMap(a).is_equal(isl.UnionMap(b)))


# ── Statement correspondence ────────────────────────────────────────


def _stmt_signature(s: isl.Set, reads: isl.UnionMap, writes: isl.UnionMap) -> tuple:
    """Signature for one statement: (n_dims, domain_shape, read_arrays, write_arrays)."""
    name = s.get_tuple_name()
    ndim = s.dim(isl.dim_type.set)

    # Normalized domain shape (tuple name stripped)
    shape = s.set_tuple_name("_X")

    # Arrays accessed by this statement
    read_arrays: set[str] = set()
    writes_arrays: set[str] = set()

    def _collect_reads(m: isl.Map) -> None:
        if m.get_tuple_name(isl.dim_type.in_) == name:
            read_arrays.add(m.get_tuple_name(isl.dim_type.out))

    def _collect_writes(m: isl.Map) -> None:
        if m.get_tuple_name(isl.dim_type.in_) == name:
            writes_arrays.add(m.get_tuple_name(isl.dim_type.out))

    reads.foreach_map(_collect_reads)
    writes.foreach_map(_collect_writes)

    return (ndim, shape, frozenset(read_arrays), frozenset(writes_arrays))


def find_statement_mapping(ref: ScopModel, cand: ScopModel) -> dict[str, str] | None:
    """Find a bijection mapping *cand* statement names to *ref* names.

    Matches by domain shape + access footprint (arrays read/written).
    Returns ``{cand_name: ref_name, ...}`` or ``None`` if no valid
    mapping exists.
    """
    ref_dom = isl.UnionSet(ref.domain)
    cand_dom = isl.UnionSet(cand.domain)
    ref_rd = isl.UnionMap(ref.reads).intersect_domain(ref_dom)
    ref_wr = isl.UnionMap(ref.writes).intersect_domain(ref_dom)
    cand_rd = isl.UnionMap(cand.reads).intersect_domain(cand_dom)
    cand_wr = isl.UnionMap(cand.writes).intersect_domain(cand_dom)

    # Collect per-statement signatures
    ref_stmts: dict[str, tuple] = {}
    ref_dom.foreach_set(
        lambda s: ref_stmts.__setitem__(
            s.get_tuple_name(), _stmt_signature(s, ref_rd, ref_wr),
        )
    )
    cand_stmts: dict[str, tuple] = {}
    cand_dom.foreach_set(
        lambda s: cand_stmts.__setitem__(
            s.get_tuple_name(), _stmt_signature(s, cand_rd, cand_wr),
        )
    )

    if len(ref_stmts) != len(cand_stmts):
        return None

    # Group by (ndim, read_arrays, write_arrays)
    def _group_key(sig: tuple) -> tuple:
        return (sig[0], sig[2], sig[3])  # ndim, reads, writes

    ref_groups: dict[tuple, list[str]] = {}
    for name, sig in ref_stmts.items():
        ref_groups.setdefault(_group_key(sig), []).append(name)

    cand_groups: dict[tuple, list[str]] = {}
    for name, sig in cand_stmts.items():
        cand_groups.setdefault(_group_key(sig), []).append(name)

    if set(ref_groups.keys()) != set(cand_groups.keys()):
        return None

    mapping: dict[str, str] = {}
    for key, ref_names in ref_groups.items():
        cand_names = cand_groups[key]
        if len(ref_names) != len(cand_names):
            return None
        if len(ref_names) == 1:
            mapping[cand_names[0]] = ref_names[0]
        else:
            # Disambiguate by domain shape equality
            matched_ref: set[str] = set()
            for cn in cand_names:
                c_shape = cand_stmts[cn][1]  # normalized Set
                found = False
                for rn in ref_names:
                    if rn in matched_ref:
                        continue
                    r_shape = ref_stmts[rn][1]
                    if c_shape.is_equal(r_shape):
                        mapping[cn] = rn
                        matched_ref.add(rn)
                        found = True
                        break
                if not found:
                    # Cannot disambiguate — give up and let the
                    # footprint fallback handle it downstream.
                    return None

    return mapping if len(mapping) == len(ref_stmts) else None


def rename_union_set(us_str: str, name_map: dict[str, str]) -> str:
    """Rename statement tuple IDs in a union set."""
    us = isl.UnionSet(us_str)
    result = isl.UnionSet.empty(us.get_space())
    sets: list[isl.Set] = []
    us.foreach_set(sets.append)
    for s in sets:
        name = s.get_tuple_name()
        s = s.set_tuple_name(name_map.get(name, name))
        result = result.union(isl.UnionSet(str(s)))
    return str(result)


def rename_union_map_domain(um_str: str, name_map: dict[str, str]) -> str:
    """Rename input (domain) tuple IDs in a union map, keep output names."""
    um = isl.UnionMap(um_str)
    result = isl.UnionMap.empty(um.get_space())
    maps: list[isl.Map] = []
    um.foreach_map(maps.append)
    for m in maps:
        in_name = m.get_tuple_name(isl.dim_type.in_)
        m = m.set_tuple_name(isl.dim_type.in_, name_map.get(in_name, in_name))
        result = result.union(isl.UnionMap(str(m)))
    return str(result)


def rename_model(model: ScopModel, name_map: dict[str, str]) -> ScopModel:
    """Return a copy of *model* with statement IDs renamed per *name_map*."""
    return ScopModel(
        domain=rename_union_set(model.domain, name_map),
        schedule=rename_union_map_domain(model.schedule, name_map),
        reads=rename_union_map_domain(model.reads, name_map),
        writes=rename_union_map_domain(model.writes, name_map),
    )


# ── Footprint comparison ────────────────────────────────────────────


def access_footprints_equal(ref: ScopModel, cand: ScopModel) -> bool:
    """Check that ref and cand access the same memory locations per statement.

    This is weaker than full access-map equality but handles cases where
    the iteration domain is shifted or tiled: the *set* of memory
    locations touched by each statement must match, even if the
    iteration-to-location mapping differs.
    """
    ref_rd = isl.UnionMap(ref.reads)
    ref_wr = isl.UnionMap(ref.writes)
    cand_rd = isl.UnionMap(cand.reads)
    cand_wr = isl.UnionMap(cand.writes)

    # Quick whole-program check first (fast fail for obvious mismatches
    # before the more expensive per-statement loop below).
    if not _fp_equal(ref_rd.range(), cand_rd.range()):
        return False
    if not _fp_equal(ref_wr.range(), cand_wr.range()):
        return False

    # Per-statement footprint: each statement must touch the same locations
    ref_stmts: set[str] = set()
    isl.UnionSet(ref.domain).foreach_set(
        lambda s: ref_stmts.add(s.get_tuple_name())
    )
    cand_stmts: set[str] = set()
    isl.UnionSet(cand.domain).foreach_set(
        lambda s: cand_stmts.add(s.get_tuple_name())
    )
    if ref_stmts != cand_stmts:
        return False

    for name in ref_stmts:
        r_rd = _maps_for_stmt(ref_rd, name)
        c_rd = _maps_for_stmt(cand_rd, name)
        if not _fp_equal(r_rd.range(), c_rd.range()):
            return False
        r_wr = _maps_for_stmt(ref_wr, name)
        c_wr = _maps_for_stmt(cand_wr, name)
        if not _fp_equal(r_wr.range(), c_wr.range()):
            return False

    return True


def whole_program_footprints_equal(ref: ScopModel, cand: ScopModel) -> bool:
    """Check that ref and cand access the same total memory locations.

    Ignores per-statement breakdown — only checks that the union of all
    read locations matches and the union of all write locations matches.
    This handles tiling where statement dimensionality changes but the
    overall memory footprint is preserved.
    """
    ref_dom = isl.UnionSet(ref.domain)
    cand_dom = isl.UnionSet(cand.domain)
    ref_rd = isl.UnionMap(ref.reads).intersect_domain(ref_dom)
    ref_wr = isl.UnionMap(ref.writes).intersect_domain(ref_dom)
    cand_rd = isl.UnionMap(cand.reads).intersect_domain(cand_dom)
    cand_wr = isl.UnionMap(cand.writes).intersect_domain(cand_dom)

    if not _fp_equal(ref_rd.range(), cand_rd.range()):
        return False
    if not _fp_equal(ref_wr.range(), cand_wr.range()):
        return False
    return True


def _fp_equal(ref_fp: isl.UnionSet, cand_fp: isl.UnionSet) -> bool:
    """Compare footprints, tolerating codegen parameter upper bounds.

    Tadashi codegen can introduce parameter upper bounds (e.g.
    ``n <= 29020049``) that make the candidate's footprint a strict
    subset of the reference's.  This check accepts that case by
    comparing per-array: for each array, if the candidate set is a
    subset of the reference and equals the reference when restricted
    to the candidate's own parameter constraints, the array matches.

    Per-array comparison is needed because ``UnionSet.params()``
    returns the *intersection* of parameter constraints across all
    sets in the union — a bound present on only one array would be
    lost.
    """
    if ref_fp.is_equal(cand_fp):
        return True
    if not cand_fp.is_subset(ref_fp):
        return False

    # Compare per-array (per named set in the union)
    ref_sets: dict[str, isl.Set] = {}
    ref_fp.foreach_set(lambda s: ref_sets.__setitem__(s.get_tuple_name(), s))
    cand_sets: dict[str, isl.Set] = {}
    cand_fp.foreach_set(lambda s: cand_sets.__setitem__(s.get_tuple_name(), s))

    if set(ref_sets.keys()) != set(cand_sets.keys()):
        return False

    for name, r_set in ref_sets.items():
        c_set = cand_sets[name]
        if r_set.is_equal(c_set):
            continue
        if not c_set.is_subset(r_set):
            return False
        # Difference is only param bounds?
        c_params = c_set.params()
        if not r_set.intersect_params(c_params).is_equal(c_set):
            return False

    return True


def _maps_for_stmt(um: isl.UnionMap, stmt_name: str) -> isl.UnionMap:
    """Extract maps from a union map whose input tuple is *stmt_name*."""
    result = isl.UnionMap.empty(um.get_space())
    maps: list[isl.Map] = []
    um.foreach_map(maps.append)
    for m in maps:
        if m.get_tuple_name(isl.dim_type.in_) == stmt_name:
            result = result.union(isl.UnionMap(str(m)))
    return result


# ── Dependence analysis ────────────────────────────────────────────


def compute_deps(
    domain: str, reads: str, writes: str, schedule: str,
) -> str:
    """Compute all data dependences (RAW + WAW + WAR) using isl flow analysis.

    Returns a union map string ``{ source -> sink }`` where *source*
    must execute before *sink*.

    Note: writes are treated as may-sources (``set_may_source``) because
    ``extract.py`` provides ``may_writes``.  Using ``set_must_source``
    with may-writes could produce over-precise flow results and miss
    dependences from earlier writes.
    """
    dom = isl.UnionSet(domain)
    rd = isl.UnionMap(reads).intersect_domain(dom)
    wr = isl.UnionMap(writes).intersect_domain(dom)
    sched = isl.UnionMap(schedule).intersect_domain(dom)

    dep_parts: list[isl.UnionMap] = []

    # RAW: read-after-write (may-source for soundness with may-writes)
    if not wr.is_empty() and not rd.is_empty():
        info = isl.UnionAccessInfo.from_sink(rd)
        info = info.set_may_source(wr)
        info = info.set_schedule_map(sched)
        flow = info.compute_flow()
        dep_parts.append(flow.get_may_dependence())

    # WAW: write-after-write
    if not wr.is_empty():
        info = isl.UnionAccessInfo.from_sink(wr)
        info = info.set_may_source(wr)
        info = info.set_schedule_map(sched)
        flow = info.compute_flow()
        dep_parts.append(flow.get_may_dependence())

    # WAR: write-after-read (anti-dependence)
    if not wr.is_empty() and not rd.is_empty():
        info = isl.UnionAccessInfo.from_sink(wr)
        info = info.set_may_source(rd)
        info = info.set_schedule_map(sched)
        flow = info.compute_flow()
        dep_parts.append(flow.get_may_dependence())

    if not dep_parts:
        return str(isl.UnionMap.empty(dom.get_space()))

    result = dep_parts[0]
    for part in dep_parts[1:]:
        result = result.union(part)
    return str(result)


def schedule_preserves_deps(deps_str: str, schedule_str: str) -> bool:
    """Check whether *schedule* preserves all data dependences.

    For each dependence ``(source -> sink)``, verifies that
    ``schedule(source)`` is lexicographically before ``schedule(sink)``.
    """
    deps = isl.UnionMap(deps_str)
    schedule = isl.UnionMap(schedule_str)

    if deps.is_empty():
        return True

    # Apply candidate schedule to both sides: { time(src) -> time(dst) }
    scheduled = deps.apply_domain(schedule).apply_range(schedule)

    # Check each concrete map for lex-positivity of deltas
    maps: list[isl.Map] = []
    scheduled.foreach_map(maps.append)

    for m in maps:
        n_in = m.dim(isl.dim_type.in_)
        n_out = m.dim(isl.dim_type.out)
        if n_in != n_out:
            return False

        # Align tuple names so deltas() works
        m = m.set_tuple_name(isl.dim_type.in_, "T")
        m = m.set_tuple_name(isl.dim_type.out, "T")

        delta = m.deltas()
        if not _deltas_lex_positive(delta):
            return False

    return True


def _deltas_lex_positive(delta: isl.Set) -> bool:
    """Check that every element of *delta* is lexicographically > 0."""
    dim = delta.dim(isl.dim_type.set)
    if dim == 0:
        return delta.is_empty()

    # Build the zero point in the same space
    zero = isl.Set.universe(delta.get_space())
    for i in range(dim):
        zero = zero.fix_val(isl.dim_type.set, i, 0)

    # lex_le_set returns elements of delta that are <= zero
    bad = delta.lex_le_set(zero)
    return bool(bad.is_empty())
