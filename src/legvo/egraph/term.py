"""Term algebra for loop program representation.

Uses De Bruijn indices for loop variable binding:
- ``DBVar(depth)`` refers to the loop variable bound ``depth`` levels up.
  ``DBVar(0)`` = innermost enclosing For's variable.
  ``DBVar(1)`` = next enclosing For's variable, etc.

This makes alpha-equivalence trivial: two terms with the same De Bruijn
structure are equivalent regardless of original variable names.

Loop interchange becomes:
    For(a, b, s, For(c, d, t, body))
    → For(c, d, t, For(a, b, s, swap01(body)))
where swap01 exchanges DBVar(0) ↔ DBVar(1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union


# ── Leaf nodes ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class Const:
    value: float
    def to_egg(self) -> str:
        if self.value == int(self.value):
            return f"(Const {int(self.value)})"
        return f"(ConstF {self.value})"


@dataclass(frozen=True)
class Param:
    """Named scalar parameter (alpha, beta, N, M)."""
    name: str
    def to_egg(self) -> str:
        return f'(Param "{self.name}")'


@dataclass(frozen=True)
class DBVar:
    """De Bruijn index: reference to loop variable depth levels up."""
    depth: int
    def to_egg(self) -> str:
        return f"(DBVar {self.depth})"


@dataclass(frozen=True)
class Unknown:
    desc: str = ""
    def to_egg(self) -> str:
        return f'(Unknown "{self.desc}")'


# ── Memory ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Load:
    array: str
    indices: tuple[Term, ...]
    def to_egg(self) -> str:
        n = len(self.indices)
        if n == 0:
            # Scalar load: use dummy index (Const 0)
            return f'(Load "{self.array}" (Const 0))'
        idx = " ".join(i.to_egg() for i in self.indices)
        tag = "Load" if n == 1 else f"Load{n}"
        return f'({tag} "{self.array}" {idx})'


@dataclass(frozen=True)
class Store:
    array: str
    indices: tuple[Term, ...]
    value: Term
    def to_egg(self) -> str:
        n = len(self.indices)
        val = self.value.to_egg()
        if n == 0:
            # Scalar store: use dummy index (Const 0)
            return f'(Store "{self.array}" (Const 0) {val})'
        idx = " ".join(i.to_egg() for i in self.indices)
        tag = "Store" if n == 1 else f"Store{n}"
        return f'({tag} "{self.array}" {idx} {val})'


# ── Arithmetic ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class BinOp:
    op: str  # "Add", "Mul", "Sub", "Div"
    left: Term
    right: Term
    def to_egg(self) -> str:
        return f"({self.op} {self.left.to_egg()} {self.right.to_egg()})"


@dataclass(frozen=True)
class Neg:
    operand: Term
    def to_egg(self) -> str:
        return f"(Neg {self.operand.to_egg()})"


# ── Control flow ────────────────────────────────────────────────────

@dataclass(frozen=True)
class For:
    """Loop with De Bruijn binding.

    ``For(lo, hi, step, body)`` binds a fresh variable accessible
    as ``DBVar(0)`` inside *body*.  Each enclosing For shifts existing
    DBVars up by 1.
    """
    lo: Term
    hi: Term
    step: Term
    body: Term
    def to_egg(self) -> str:
        return (
            f"(For {self.lo.to_egg()} {self.hi.to_egg()} "
            f"{self.step.to_egg()} {self.body.to_egg()})"
        )


@dataclass(frozen=True)
class Seq:
    stmts: tuple[Term, ...]
    def to_egg(self) -> str:
        if len(self.stmts) == 0:
            return "(Nop)"
        if len(self.stmts) == 1:
            return self.stmts[0].to_egg()
        result = "(Nop)"
        for s in reversed(self.stmts):
            result = f"(Seq {s.to_egg()} {result})"
        return result


@dataclass(frozen=True)
class Let:
    var: str
    expr: Term
    body: Term
    def to_egg(self) -> str:
        return f'(Let "{self.var}" {self.expr.to_egg()} {self.body.to_egg()})'


@dataclass(frozen=True)
class Reduce:
    op: str
    lo: Term
    hi: Term
    body: Term  # DBVar(0) is the reduce variable inside body
    def to_egg(self) -> str:
        return (
            f'(Reduce "{self.op}" {self.lo.to_egg()} '
            f"{self.hi.to_egg()} {self.body.to_egg()})"
        )


# ── Type alias ──────────────────────────────────────────────────────

Term = Union[
    Const, Param, DBVar, Load, Store, BinOp, Neg,
    For, Seq, Let, Reduce, Unknown,
]


# ── De Bruijn helpers ───────────────────────────────────────────────

def shift(term: Term, delta: int, cutoff: int = 0) -> Term:
    """Shift all free DBVar indices by *delta* (indices >= cutoff)."""
    if isinstance(term, DBVar):
        return DBVar(term.depth + delta) if term.depth >= cutoff else term
    if isinstance(term, (Const, Param, Unknown)):
        return term
    if isinstance(term, Load):
        return Load(term.array, tuple(shift(i, delta, cutoff) for i in term.indices))
    if isinstance(term, Store):
        return Store(term.array, tuple(shift(i, delta, cutoff) for i in term.indices),
                     shift(term.value, delta, cutoff))
    if isinstance(term, BinOp):
        return BinOp(term.op, shift(term.left, delta, cutoff), shift(term.right, delta, cutoff))
    if isinstance(term, Neg):
        return Neg(shift(term.operand, delta, cutoff))
    if isinstance(term, For):
        return For(shift(term.lo, delta, cutoff), shift(term.hi, delta, cutoff),
                   shift(term.step, delta, cutoff), shift(term.body, delta, cutoff + 1))
    if isinstance(term, Seq):
        return Seq(tuple(shift(s, delta, cutoff) for s in term.stmts))
    if isinstance(term, Let):
        return Let(term.var, shift(term.expr, delta, cutoff), shift(term.body, delta, cutoff))
    if isinstance(term, Reduce):
        return Reduce(term.op, shift(term.lo, delta, cutoff), shift(term.hi, delta, cutoff),
                      shift(term.body, delta, cutoff + 1))
    return term


def swap_db(term: Term, d1: int = 0, d2: int = 1) -> Term:
    """Swap DBVar(d1) ↔ DBVar(d2) in term. Used for loop interchange."""
    if isinstance(term, DBVar):
        if term.depth == d1:
            return DBVar(d2)
        if term.depth == d2:
            return DBVar(d1)
        return term
    if isinstance(term, (Const, Param, Unknown)):
        return term
    if isinstance(term, Load):
        return Load(term.array, tuple(swap_db(i, d1, d2) for i in term.indices))
    if isinstance(term, Store):
        return Store(term.array, tuple(swap_db(i, d1, d2) for i in term.indices),
                     swap_db(term.value, d1, d2))
    if isinstance(term, BinOp):
        return BinOp(term.op, swap_db(term.left, d1, d2), swap_db(term.right, d1, d2))
    if isinstance(term, Neg):
        return Neg(swap_db(term.operand, d1, d2))
    if isinstance(term, For):
        return For(swap_db(term.lo, d1, d2), swap_db(term.hi, d1, d2),
                   swap_db(term.step, d1, d2), swap_db(term.body, d1 + 1, d2 + 1))
    if isinstance(term, Seq):
        return Seq(tuple(swap_db(s, d1, d2) for s in term.stmts))
    if isinstance(term, Let):
        return Let(term.var, swap_db(term.expr, d1, d2), swap_db(term.body, d1, d2))
    if isinstance(term, Reduce):
        return Reduce(term.op, swap_db(term.lo, d1, d2), swap_db(term.hi, d1, d2),
                      swap_db(term.body, d1 + 1, d2 + 1))
    return term


# ── Egglog datatype ─────────────────────────────────────────────────

def egglog_datatype() -> str:
    return """\
(datatype Term
  (Const i64)
  (ConstF f64)
  (Param String)
  (DBVar i64)
  (Load String Term)
  (Load2 String Term Term)
  (Load3 String Term Term Term)
  (Store String Term Term)
  (Store2 String Term Term Term)
  (Store3 String Term Term Term Term)
  (Add Term Term)
  (Mul Term Term)
  (Sub Term Term)
  (Div Term Term)
  (Neg Term)
  (Max_score Term Term)
  (Max Term Term)
  (Min Term Term)
  (Match Term Term)
  (Capitalize Term Term)
  (Fmax Term Term)
  (Fmin Term Term)
  (Pow Term Term)
  (Fmod Term Term)
  (For Term Term Term Term)
  (Seq Term Term)
  (Nop)
  (Let String Term Term)
  (Reduce String Term Term Term)
  (Unknown String)
  ;; === Binding-aware operations (De Bruijn) ===
  ;; These are CONSTRUCTORS in the Term datatype, enabling their use
  ;; in both LHS and RHS of rewrite/rule. Propagation rules reduce
  ;; SwapDB/DbShift nodes to concrete Term nodes during saturation.
  (SwapDB Term i64 i64)   ;; swap variables at depth d1 and d2
  (DbShift Term i64 i64)  ;; shift free variables >= cutoff by delta
  (Subst Term i64 Term)   ;; substitute DBVar(depth) with replacement term
)"""
