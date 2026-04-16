"""Unit tests for isl_helpers — pure islpy, no tadashi needed."""

import pytest

from legvo.polyhedral.isl_helpers import (
    _fp_equal,
    compute_deps,
    maps_equal,
    schedule_preserves_deps,
    sets_equal,
)


# ── sets_equal ──────────────────────────────────────────────────────

class TestSetsEqual:
    def test_identical(self):
        s = "[N] -> { S[i] : 0 <= i < N }"
        assert sets_equal(s, s)

    def test_renamed_variable(self):
        a = "[N] -> { S[i] : 0 <= i < N }"
        b = "[N] -> { S[j] : 0 <= j < N }"
        assert sets_equal(a, b)

    def test_different_bound(self):
        a = "[N] -> { S[i] : 0 <= i < N }"
        b = "[N] -> { S[i] : 0 <= i < N + 1 }"
        assert not sets_equal(a, b)

    def test_multi_statement(self):
        a = "[N] -> { S_0[i] : 0 <= i < N; S_1[j] : 0 <= j < N }"
        b = "[N] -> { S_1[j] : 0 <= j < N; S_0[i] : 0 <= i < N }"
        assert sets_equal(a, b)


# ── maps_equal ──────────────────────────────────────────────────────

class TestMapsEqual:
    def test_identical(self):
        m = "[N] -> { S[i,j] -> A[i,j] }"
        assert maps_equal(m, m)

    def test_different_index(self):
        a = "[N] -> { S[i,j] -> A[i,j] }"
        b = "[N] -> { S[i,j] -> A[j,i] }"
        assert not maps_equal(a, b)

    def test_multi_access(self):
        a = "[N] -> { S[i] -> A[i]; S[i] -> B[i] }"
        b = "[N] -> { S[i] -> B[i]; S[i] -> A[i] }"
        assert maps_equal(a, b)


# ── compute_deps ────────────────────────────────────────────────────

class TestComputeDeps:
    def test_no_overlap(self):
        """Reads B, writes A — disjoint arrays, no deps."""
        import islpy as isl
        deps = compute_deps(
            domain="[N] -> { S[i] : 0 <= i < N }",
            reads="[N] -> { S[i] -> B[i] }",
            writes="[N] -> { S[i] -> A[i] }",
            schedule="[N] -> { S[i] -> [i] }",
        )
        assert isl.UnionMap(deps).is_empty()

    def test_raw_dep(self):
        """A[i] = A[i-1] + 1 — RAW along i."""
        import islpy as isl
        deps = compute_deps(
            domain="[N] -> { S[i] : 1 <= i < N }",
            reads="[N] -> { S[i] -> A[i - 1] }",
            writes="[N] -> { S[i] -> A[i] }",
            schedule="[N] -> { S[i] -> [i] }",
        )
        assert not isl.UnionMap(deps).is_empty()


# ── schedule_preserves_deps ─────────────────────────────────────────

class TestScheduleLegality:
    def _deps_for_forward_chain(self):
        """A[i] = A[i-1] + 1 — forward dep along i."""
        return compute_deps(
            domain="[N] -> { S[i] : 1 <= i < N }",
            reads="[N] -> { S[i] -> A[i - 1] }",
            writes="[N] -> { S[i] -> A[i] }",
            schedule="[N] -> { S[i] -> [i] }",
        )

    def test_identity_legal(self):
        deps = self._deps_for_forward_chain()
        assert schedule_preserves_deps(
            deps, "[N] -> { S[i] -> [i] }",
        )

    def test_reversal_illegal(self):
        deps = self._deps_for_forward_chain()
        assert not schedule_preserves_deps(
            deps, "[N] -> { S[i] -> [-i] }",
        )

    def test_shift_legal(self):
        deps = self._deps_for_forward_chain()
        assert schedule_preserves_deps(
            deps, "[N] -> { S[i] -> [i + 5] }",
        )

    def test_no_deps_anything_legal(self):
        """Disjoint arrays — any schedule is legal."""
        deps = compute_deps(
            domain="[N] -> { S[i] : 0 <= i < N }",
            reads="[N] -> { S[i] -> B[i] }",
            writes="[N] -> { S[i] -> A[i] }",
            schedule="[N] -> { S[i] -> [i] }",
        )
        assert schedule_preserves_deps(
            deps, "[N] -> { S[i] -> [-i] }",
        )

    def test_interchange_no_carried_dep(self):
        """A[i][j] = B[i][j] + C[i][j] — no carried deps, interchange OK."""
        deps = compute_deps(
            domain="[N] -> { S[i,j] : 0 <= i < N and 0 <= j < N }",
            reads="[N] -> { S[i,j] -> B[i,j]; S[i,j] -> C[i,j] }",
            writes="[N] -> { S[i,j] -> A[i,j] }",
            schedule="[N] -> { S[i,j] -> [i,j] }",
        )
        assert schedule_preserves_deps(
            deps, "[N] -> { S[i,j] -> [j,i] }",
        )

    def test_interchange_with_i_dep(self):
        """A[i][j] = A[i-1][j] + B[i][j] — dep along i, interchange still legal."""
        deps = compute_deps(
            domain="[N] -> { S[i,j] : 1 <= i < N and 0 <= j < N }",
            reads="[N] -> { S[i,j] -> A[i-1,j]; S[i,j] -> B[i,j] }",
            writes="[N] -> { S[i,j] -> A[i,j] }",
            schedule="[N] -> { S[i,j] -> [i,j] }",
        )
        assert schedule_preserves_deps(
            deps, "[N] -> { S[i,j] -> [j,i] }",
        )


# ── _fp_equal ───────────────────────────────────────────────────────

class TestFpEqual:
    def test_identical(self):
        import islpy as isl
        a = isl.UnionSet("[N] -> { A[i] : 0 <= i < N }")
        assert _fp_equal(a, a)

    def test_param_upper_bound(self):
        """Codegen artifact: cand has n <= 29020049 — should still match."""
        import islpy as isl
        ref = isl.UnionSet("[N] -> { A[i] : 0 <= i < N }")
        cand = isl.UnionSet("[N] -> { A[i] : 0 <= i < N and N <= 29020049 }")
        assert _fp_equal(ref, cand)

    def test_non_param_difference(self):
        """Cand has genuinely different index range — should NOT match."""
        import islpy as isl
        ref = isl.UnionSet("[N] -> { A[i] : 0 <= i < N }")
        cand = isl.UnionSet("[N] -> { A[i] : 0 <= i < N - 1 }")
        assert not _fp_equal(ref, cand)

    def test_multi_array_partial_bound(self):
        """Only one array has the param bound — per-array check catches it."""
        import islpy as isl
        ref = isl.UnionSet("[N] -> { A[i] : 0 <= i < N; B[j] : 0 <= j < N }")
        cand = isl.UnionSet("[N] -> { A[i] : 0 <= i < N; B[j] : 0 <= j < N and N <= 18046081 }")
        assert _fp_equal(ref, cand)

    def test_cand_not_subset(self):
        """Cand accesses MORE locations than ref — should NOT match."""
        import islpy as isl
        ref = isl.UnionSet("[N] -> { A[i] : 0 <= i < N }")
        cand = isl.UnionSet("[N] -> { A[i] : 0 <= i < N + 1 }")
        assert not _fp_equal(ref, cand)

    def test_different_arrays(self):
        """Cand accesses a different array — should NOT match."""
        import islpy as isl
        ref = isl.UnionSet("[N] -> { A[i] : 0 <= i < N }")
        cand = isl.UnionSet("[N] -> { B[i] : 0 <= i < N }")
        assert not _fp_equal(ref, cand)
