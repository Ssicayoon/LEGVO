"""Tests for term normalization."""

from legvo.egraph.term import *
from legvo.egraph.normalize import normalize, _clean_array_name, _is_local_var_name


class TestCleanArrayName:
    def test_restrict_suffix(self):
        assert _clean_array_name("C_restrict") == "C"

    def test_aligned_suffix(self):
        assert _clean_array_name("A_aligned") == "A"

    def test_no_change(self):
        assert _clean_array_name("A") == "A"


class TestIsLocalVar:
    def test_standard_arrays(self):
        assert not _is_local_var_name("A")
        assert not _is_local_var_name("tmp")
        assert not _is_local_var_name("y")

    def test_local_vars(self):
        assert _is_local_var_name("sumA")
        assert _is_local_var_name("cij")
        assert _is_local_var_name("t")


class TestNormalize:
    def test_scalar_val(self):
        t = Param("SCALAR_VAL")
        assert normalize(t) == Const(0.0)

    def test_param_pb_prefix(self):
        t = Param("_PB_N")
        assert normalize(t) == Param("N")

    def test_array_restrict(self):
        t = Load("C_restrict", (DBVar(0),))
        result = normalize(t)
        assert isinstance(result, Load)
        assert result.array == "C"

    def test_inline_local(self):
        t = Seq((
            Store("t", (), Const(5.0)),
            Store("A", (DBVar(0),), Param("t")),
        ))
        result = normalize(t)
        assert isinstance(result, Store)
        assert result.array == "A"
        assert result.value == Const(5.0)

    def test_full_pipeline(self):
        t = For(Const(0), Param("_PB_N"), Const(1),
                Store("A_restrict", (DBVar(0),),
                      BinOp("Add", Load("B_restrict", (DBVar(0),)), Param("SCALAR_VAL"))))
        result = normalize(t)
        egg = result.to_egg()
        assert "_PB_" not in egg
        assert "restrict" not in egg
        assert "SCALAR_VAL" not in egg
