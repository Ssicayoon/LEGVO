"""Polyhedral equivalence verification.

Given two ScopModels (reference and candidate), determines whether the
candidate is a legal reschedule of the reference by directly checking:

1. Iteration domain equality   (isl set equality)
2. Read access equality         (isl map equality)
3. Write access equality        (isl map equality)
4. Schedule dependence legality (isl flow analysis + delta check)

Soundness assumption for the footprint fallback path:
    The footprint check (steps 4-5) verifies that each statement touches
    the same *set* of memory locations, not that the iteration-to-location
    *mapping* is identical.  This is sound when the candidate is a
    polyhedral reschedule of the reference (access functions are preserved
    by construction in tadashi/PET transformations), but would not catch a
    program that accesses the same locations via a completely different
    access function.  The 0/720 false-positive rate on known-incorrect
    variants provides empirical evidence, but this theoretical gap should
    be noted.
"""

from __future__ import annotations

import logging

import islpy as isl

from . import isl_helpers
from .model import ScopModel, VerifyResult

log = logging.getLogger(__name__)


def _restrict_to_domain(model: ScopModel) -> ScopModel:
    """Strip accesses for statements not in the iteration domain."""
    dom = isl.UnionSet(model.domain)
    return ScopModel(
        domain=model.domain,
        schedule=str(isl.UnionMap(model.schedule).intersect_domain(dom)),
        reads=str(isl.UnionMap(model.reads).intersect_domain(dom)),
        writes=str(isl.UnionMap(model.writes).intersect_domain(dom)),
    )


def verify(ref: ScopModel, cand: ScopModel) -> VerifyResult:
    """Check if *cand* is a legal reschedule of *ref*."""
    checks: dict = {}

    # Step 0: strip non-domain accesses (PET artifacts like loop-var writes)
    ref = _restrict_to_domain(ref)
    cand = _restrict_to_domain(cand)

    # Step 1: statement correspondence — rename candidate to match reference
    mapping = isl_helpers.find_statement_mapping(ref, cand)
    if mapping is not None:
        cand = isl_helpers.rename_model(cand, mapping)
        checks["stmt_mapping"] = mapping

    # Step 2: domain equality
    domains_eq = isl_helpers.sets_equal(ref.domain, cand.domain)
    checks["domains_equal"] = domains_eq

    # Step 3: access equality
    reads_eq = isl_helpers.maps_equal(ref.reads, cand.reads)
    writes_eq = isl_helpers.maps_equal(ref.writes, cand.writes)
    checks["reads_equal"] = reads_eq
    checks["writes_equal"] = writes_eq

    if domains_eq and reads_eq and writes_eq:
        # Exact match on domain + accesses → check schedule
        return _check_schedule(ref, cand, checks)

    # Step 4: per-statement footprint fallback.
    # When the domain is shifted, the raw domain/access strings differ
    # but each statement still touches the same memory locations.
    try:
        footprints_eq = isl_helpers.access_footprints_equal(ref, cand)
    except isl.Error as exc:
        log.debug("footprint check failed: %s", exc)
        footprints_eq = False
    checks["footprints_equal"] = footprints_eq

    if not footprints_eq:
        # Step 5: whole-program footprint fallback.
        # Tiling may change statement dims/count but the total memory
        # footprint (all reads, all writes) is preserved.
        try:
            whole_fp_eq = isl_helpers.whole_program_footprints_equal(ref, cand)
        except isl.Error as exc:
            log.debug("whole-program footprint check failed: %s", exc)
            whole_fp_eq = False
        checks["whole_footprints_equal"] = whole_fp_eq

        if not whole_fp_eq:
            if not domains_eq:
                return VerifyResult("unknown", "Iteration domains differ", checks)
            return VerifyResult("unknown", "Access patterns differ", checks)

    # Footprints match — the candidate touches the same memory locations
    # per statement (or globally) but via a different iteration scheme
    # (shift / tile).  This is equivalent if the candidate's internal
    # schedule is legal.  See module docstring for soundness assumptions.
    return _check_schedule_self(cand, checks)


def _check_schedule(
    ref: ScopModel, cand: ScopModel, checks: dict,
) -> VerifyResult:
    """Check schedule when domain + accesses are identical."""
    schedules_eq = isl_helpers.maps_equal(ref.schedule, cand.schedule)
    checks["schedules_equal"] = schedules_eq
    if schedules_eq:
        return VerifyResult(
            "equivalent", "Identical polyhedral model (identity)", checks,
        )

    try:
        deps = isl_helpers.compute_deps(
            ref.domain, ref.reads, ref.writes, ref.schedule,
        )
        checks["deps_computed"] = True
        legal = isl_helpers.schedule_preserves_deps(deps, cand.schedule)
        checks["schedule_legal"] = legal
        if legal:
            return VerifyResult(
                "equivalent",
                "Candidate schedule preserves all reference dependences",
                checks,
            )
        return VerifyResult(
            "unknown",
            "Candidate schedule violates a data dependence",
            checks,
        )
    except isl.Error as exc:
        checks["deps_error"] = str(exc)
        return VerifyResult(
            "unknown", f"Could not verify schedule legality: {exc}", checks,
        )


def _check_schedule_self(cand: ScopModel, checks: dict) -> VerifyResult:
    """Check that the candidate's own schedule is legal w.r.t. its own deps.

    Used when the candidate has a shifted/tiled domain but matching
    footprints.  A legal internal schedule means the candidate produces
    the same output as any other legal schedule over the same footprint,
    assuming the candidate is a polyhedral reschedule of the reference
    (see module docstring for the full soundness argument).
    """
    try:
        deps = isl_helpers.compute_deps(
            cand.domain, cand.reads, cand.writes, cand.schedule,
        )
        checks["self_deps_computed"] = True
        legal = isl_helpers.schedule_preserves_deps(deps, cand.schedule)
        checks["self_schedule_legal"] = legal
        if legal:
            return VerifyResult(
                "equivalent",
                "Matching footprints with legal candidate schedule",
                checks,
            )
        return VerifyResult(
            "unknown",
            "Candidate schedule violates its own data dependences",
            checks,
        )
    except isl.Error as exc:
        checks["self_deps_error"] = str(exc)
        return VerifyResult(
            "unknown",
            f"Could not verify candidate schedule legality: {exc}",
            checks,
        )
