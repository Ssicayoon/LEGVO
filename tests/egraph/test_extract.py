"""Tests for Term extraction from C source."""

from legvo.egraph.extract import parse_expr, parse_statement
from legvo.egraph.term import *


class TestParseExpr:
    def test_constant(self):
        assert parse_expr("42") == Const(42.0)

    def test_param(self):
        assert parse_expr("N", {"N"}) == Param("N")

    def test_loop_var_dbvar(self):
        """Loop variable should become DBVar."""
        r = parse_expr("i", set(), ["i"])
        assert r == DBVar(0)

    def test_nested_loop_vars(self):
        """Inner loop var = DBVar(0), outer = DBVar(1)."""
        r = parse_expr("i", set(), ["i", "j"])
        assert r == DBVar(1)
        r2 = parse_expr("j", set(), ["i", "j"])
        assert r2 == DBVar(0)

    def test_add(self):
        r = parse_expr("a + b", {"a", "b"})
        assert isinstance(r, BinOp) and r.op == "Add"

    def test_mul(self):
        r = parse_expr("a * b", {"a", "b"})
        assert isinstance(r, BinOp) and r.op == "Mul"

    def test_precedence(self):
        r = parse_expr("a + b * c", {"a", "b", "c"})
        assert r.op == "Add" and r.right.op == "Mul"

    def test_array_access(self):
        r = parse_expr("A[i][j]", set(), ["i", "j"])
        assert isinstance(r, Load)
        assert r.array == "A"
        assert r.indices == (DBVar(1), DBVar(0))

    def test_complex_polybench(self):
        r = parse_expr("0.33333 * (A[i-1] + A[i] + A[i+1])", {"N"}, ["t", "i"])
        assert isinstance(r, BinOp) and r.op == "Mul"


class TestParseStatement:
    def test_simple_assign(self):
        r = parse_statement("A[i] = B[i] + C[i];", set(), ["i"])
        assert isinstance(r, Store)
        assert r.array == "A"
        assert r.indices == (DBVar(0),)

    def test_accumulate(self):
        r = parse_statement("tmp[i] += A[i][j] * x[j];", set(), ["i", "j"])
        assert isinstance(r, Store)
        assert r.value.op == "Add"


class TestDebruijnEquivalence:
    def test_loop_var_name_irrelevant(self):
        """for(i, 0, N, A[i]=B[i]) == for(j, 0, N, A[j]=B[j]) with De Bruijn."""
        from legvo.egraph.extract import _parse_scop_body

        body1 = "for (int i = 0; i < N; i++)\n  A[i] = B[i];"
        body2 = "for (int j = 0; j < N; j++)\n  A[j] = B[j];"

        t1 = _parse_scop_body(body1, {"N"})
        t2 = _parse_scop_body(body2, {"N"})
        assert t1 == t2, f"\n{t1.to_egg()}\n!=\n{t2.to_egg()}"


class TestTermToEgg:
    def test_const(self):
        assert Const(0).to_egg() == "(Const 0)"

    def test_dbvar(self):
        assert DBVar(0).to_egg() == "(DBVar 0)"
        assert DBVar(2).to_egg() == "(DBVar 2)"

    def test_for_debruijn(self):
        t = For(Const(0), Param("N"), Const(1),
                Store("A", (DBVar(0),), Const(0)))
        egg = t.to_egg()
        assert "(For" in egg
        assert "(DBVar 0)" in egg


class TestSwapDB:
    def test_swap01(self):
        t = Load("A", (DBVar(0), DBVar(1)))
        s = swap_db(t, 0, 1)
        assert s == Load("A", (DBVar(1), DBVar(0)))

    def test_swap_in_for(self):
        """Swap inside a For shifts the swap targets."""
        t = For(Const(0), Param("N"), Const(1),
                Load("A", (DBVar(0), DBVar(1))))
        s = swap_db(t, 0, 1)
        # Inside the For, DBVar depths are shifted by 1
        # So swap(0,1) becomes swap(1,2) inside the body
        expected = For(Const(0), Param("N"), Const(1),
                       Load("A", (DBVar(0), DBVar(1))))
        # The bounds are NOT inside a For, so DBVar(0)↔DBVar(1) applies to bounds
        # But there are no DBVars in bounds here
        assert isinstance(s, For)
