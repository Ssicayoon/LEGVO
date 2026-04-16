"""Unit tests for verify — constructs ScopModel directly, no tadashi."""

from legvo.polyhedral.model import ScopModel
from legvo.polyhedral.verify import verify


def _make(domain, schedule, reads, writes):
    return ScopModel(domain=domain, schedule=schedule, reads=reads, writes=writes)


class TestVerifyIdentity:
    def test_identical_model(self):
        m = _make(
            domain="[N] -> { S[i,j] : 0 <= i < N and 0 <= j < N }",
            schedule="[N] -> { S[i,j] -> [i,j] }",
            reads="[N] -> { S[i,j] -> B[i,j]; S[i,j] -> C[i,j] }",
            writes="[N] -> { S[i,j] -> A[i,j] }",
        )
        result = verify(m, m)
        assert result.status == "equivalent"
        assert result.checks["schedules_equal"]


class TestVerifyInterchange:
    def test_legal_interchange(self):
        """No carried deps — interchange is legal."""
        ref = _make(
            domain="[N] -> { S[i,j] : 0 <= i < N and 0 <= j < N }",
            schedule="[N] -> { S[i,j] -> [i,j] }",
            reads="[N] -> { S[i,j] -> B[i,j]; S[i,j] -> C[i,j] }",
            writes="[N] -> { S[i,j] -> A[i,j] }",
        )
        cand = _make(
            domain="[N] -> { S[i,j] : 0 <= i < N and 0 <= j < N }",
            schedule="[N] -> { S[i,j] -> [j,i] }",
            reads="[N] -> { S[i,j] -> B[i,j]; S[i,j] -> C[i,j] }",
            writes="[N] -> { S[i,j] -> A[i,j] }",
        )
        result = verify(ref, cand)
        assert result.status == "equivalent"
        assert result.checks["schedule_legal"]


class TestVerifyStmtCorrespondence:
    def test_renamed_statements(self):
        """Same model but statement IDs differ — should still match."""
        ref = _make(
            domain="[N] -> { S_0[i,j] : 0 <= i < N and 0 <= j < N }",
            schedule="[N] -> { S_0[i,j] -> [i,j] }",
            reads="[N] -> { S_0[i,j] -> B[i,j] }",
            writes="[N] -> { S_0[i,j] -> A[i,j] }",
        )
        cand = _make(
            domain="[N] -> { S_5[i,j] : 0 <= i < N and 0 <= j < N }",
            schedule="[N] -> { S_5[i,j] -> [i,j] }",
            reads="[N] -> { S_5[i,j] -> B[i,j] }",
            writes="[N] -> { S_5[i,j] -> A[i,j] }",
        )
        result = verify(ref, cand)
        assert result.status == "equivalent"

    def test_multi_stmt_renamed(self):
        """Multiple statements, all renamed."""
        ref = _make(
            domain="[N] -> { S_0[i] : 0 <= i < N; S_1[i,j] : 0 <= i < N and 0 <= j < N }",
            schedule="[N] -> { S_0[i] -> [i,0]; S_1[i,j] -> [i,j] }",
            reads="[N] -> { S_1[i,j] -> A[i,j] }",
            writes="[N] -> { S_0[i] -> x[i]; S_1[i,j] -> x[i] }",
        )
        cand = _make(
            domain="[N] -> { S_3[i] : 0 <= i < N; S_7[i,j] : 0 <= i < N and 0 <= j < N }",
            schedule="[N] -> { S_3[i] -> [i,0]; S_7[i,j] -> [i,j] }",
            reads="[N] -> { S_7[i,j] -> A[i,j] }",
            writes="[N] -> { S_3[i] -> x[i]; S_7[i,j] -> x[i] }",
        )
        result = verify(ref, cand)
        assert result.status == "equivalent"


class TestVerifyShiftedDomain:
    def test_shifted_iteration(self):
        """Domain shifted by constant — same footprint, should be equivalent."""
        ref = _make(
            domain="[N] -> { S_0[i] : 0 <= i < N }",
            schedule="[N] -> { S_0[i] -> [i] }",
            reads="[N] -> { S_0[i] -> A[i] }",
            writes="[N] -> { S_0[i] -> B[i] }",
        )
        # Shifted by 10: i' = i + 10, so A[i'-10] = A[i]
        cand = _make(
            domain="[N] -> { S_0[i] : 10 <= i < N + 10 }",
            schedule="[N] -> { S_0[i] -> [i] }",
            reads="[N] -> { S_0[i] -> A[i - 10] }",
            writes="[N] -> { S_0[i] -> B[i - 10] }",
        )
        result = verify(ref, cand)
        assert result.status == "equivalent"


class TestVerifyUnknown:
    def test_different_domains(self):
        ref = _make(
            domain="[N] -> { S[i] : 0 <= i < N }",
            schedule="[N] -> { S[i] -> [i] }",
            reads="[N] -> { S[i] -> A[i] }",
            writes="[N] -> { S[i] -> B[i] }",
        )
        cand = _make(
            domain="[N] -> { S[i] : 0 <= i < N + 1 }",
            schedule="[N] -> { S[i] -> [i] }",
            reads="[N] -> { S[i] -> A[i] }",
            writes="[N] -> { S[i] -> B[i] }",
        )
        result = verify(ref, cand)
        assert result.status == "unknown"
        assert not result.checks["domains_equal"]

    def test_different_reads(self):
        ref = _make(
            domain="[N] -> { S[i] : 0 <= i < N }",
            schedule="[N] -> { S[i] -> [i] }",
            reads="[N] -> { S[i] -> A[i] }",
            writes="[N] -> { S[i] -> B[i] }",
        )
        cand = _make(
            domain="[N] -> { S[i] : 0 <= i < N }",
            schedule="[N] -> { S[i] -> [i] }",
            reads="[N] -> { S[i] -> C[i] }",
            writes="[N] -> { S[i] -> B[i] }",
        )
        result = verify(ref, cand)
        assert result.status == "unknown"
        assert not result.checks["reads_equal"]

    def test_different_writes(self):
        ref = _make(
            domain="[N] -> { S[i] : 0 <= i < N }",
            schedule="[N] -> { S[i] -> [i] }",
            reads="[N] -> { S[i] -> A[i] }",
            writes="[N] -> { S[i] -> B[i] }",
        )
        cand = _make(
            domain="[N] -> { S[i] : 0 <= i < N }",
            schedule="[N] -> { S[i] -> [i] }",
            reads="[N] -> { S[i] -> A[i] }",
            writes="[N] -> { S[i] -> D[i] }",
        )
        result = verify(ref, cand)
        assert result.status == "unknown"
        assert not result.checks["writes_equal"]

    def test_illegal_reversal(self):
        """RAW dep along i — reversal violates it."""
        ref = _make(
            domain="[N] -> { S[i] : 1 <= i < N }",
            schedule="[N] -> { S[i] -> [i] }",
            reads="[N] -> { S[i] -> A[i - 1] }",
            writes="[N] -> { S[i] -> A[i] }",
        )
        cand = _make(
            domain="[N] -> { S[i] : 1 <= i < N }",
            schedule="[N] -> { S[i] -> [-i] }",
            reads="[N] -> { S[i] -> A[i - 1] }",
            writes="[N] -> { S[i] -> A[i] }",
        )
        result = verify(ref, cand)
        assert result.status == "unknown"
        assert not result.checks.get("schedule_legal", True)
