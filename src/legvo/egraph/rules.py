"""Egglog rewrite rules — the sole equivalence reasoning engine.

All equivalence reasoning happens via these rules inside egglog:
- Algebraic: fp-safe (Mul comm, identity, cancellation) and real-arith
  (Add comm/assoc, distributivity)
- Structural: Nop elimination, Neg distribution
- Constant folding: integer arithmetic on Const nodes
- Binding-aware (in binding_rules_full()):
  - SwapDB propagation: reduces SwapDB(term, d1, d2) to concrete terms
  - DbShift propagation: reduces DbShift(term, delta, cutoff)
  - Loop interchange: polyhedral-gated, uses SwapDB for De Bruijn adjustment
  - Statement reorder: polyhedral-gated Seq commutativity
  - Scalar inlining: InlineableScalar relation (injected per-program)

Polyhedral-gated rules require (ScheduleLegal) fact from polyhedral analysis.
Polyhedral analysis provides PERMISSION; egglog does DERIVATION.
"""


def arithmetic_rules_fp_safe() -> str:
    return """\
(ruleset fp-safe)
(with-ruleset fp-safe
  ;; Multiplication commutativity (IEEE 754 safe)
  (rewrite (Mul ?x ?y) (Mul ?y ?x))

  ;; Multiplication associativity (IEEE 754 safe for exact values)
  (rewrite (Mul ?x (Mul ?y ?z)) (Mul (Mul ?x ?y) ?z))

  ;; Identity elements
  (rewrite (Add ?x (Const 0)) ?x)
  (rewrite (Add (Const 0) ?x) ?x)
  (rewrite (Mul ?x (Const 1)) ?x)
  (rewrite (Mul (Const 1) ?x) ?x)
  (rewrite (Mul ?x (Const 0)) (Const 0))
  (rewrite (Mul (Const 0) ?x) (Const 0))
  (rewrite (Sub ?x (Const 0)) ?x)

  ;; Self-cancellation
  (rewrite (Sub ?x ?x) (Const 0))

  ;; Cancellation
  (rewrite (Sub (Add ?x ?y) ?y) ?x)
  (rewrite (Sub (Add ?x ?y) ?x) ?y)

  ;; Negation
  (rewrite (Neg (Neg ?x)) ?x)
  (rewrite (Neg (Const 0)) (Const 0))
  (rewrite (Sub ?x ?y) (Add ?x (Neg ?y)))
  (rewrite (Mul (Const -1) ?x) (Neg ?x))
  (rewrite (Mul ?x (Const -1)) (Neg ?x))
  (rewrite (Neg ?x) (Mul (Const -1) ?x))
  (rewrite (Add ?x (Neg ?x)) (Const 0))
  (rewrite (Add (Neg ?x) ?x) (Const 0))
  ;; Neg distribution through Mul
  (rewrite (Mul (Neg ?x) ?y) (Neg (Mul ?x ?y)))
  (rewrite (Mul ?x (Neg ?y)) (Neg (Mul ?x ?y)))

  ;; Division as multiplication by reciprocal
  (rewrite (Div ?x ?c) (Mul ?x (Div (Const 1) ?c)))

  ;; Division identity
  (rewrite (Div ?x (Const 1)) ?x)

  ;; Division of division: (Div a (Div b c)) = (Div (Mul a c) b)
  (rewrite (Div ?a (Div ?b ?c)) (Div (Mul ?a ?c) ?b))

  ;; Mul/Div cancellation: (Div (Mul ?x ?c) ?c) = ?x
  (rewrite (Div (Mul ?x ?c) ?c) ?x)
  (rewrite (Div (Mul ?c ?x) ?c) ?x)

  ;; ConstF ↔ Const bridging for common values
  (rewrite (ConstF 0.0) (Const 0))
  (rewrite (ConstF 1.0) (Const 1))
  (rewrite (ConstF -1.0) (Const -1))
  (rewrite (ConstF 2.0) (Const 2))
  (rewrite (ConstF -2.0) (Const -2))

  ;; ConstF identity
  (rewrite (Mul ?x (ConstF 1.0)) ?x)
  (rewrite (Mul (ConstF 1.0) ?x) ?x)
  (rewrite (Add ?x (ConstF 0.0)) ?x)
  (rewrite (Add (ConstF 0.0) ?x) ?x)

  ;; ConstF half: 0.5 = 1/2
  (rewrite (ConstF 0.5) (Div (Const 1) (Const 2)))

  ;; Common reciprocals for Div↔Mul bridging
  (rewrite (Div ?x (Const 9)) (Mul ?x (ConstF 0.1111111111111111)))
  (rewrite (Mul ?x (ConstF 0.1111111111111111)) (Div ?x (Const 9)))

  ;; Strength reduction
  (rewrite (Add ?x ?x) (Mul (Const 2) ?x))
  (rewrite (Mul ?x (ConstF 0.5)) (Div ?x (Const 2)))
  (rewrite (Mul (ConstF 0.5) ?x) (Div ?x (Const 2)))
)
"""


def arithmetic_rules_real() -> str:
    return """\
(ruleset real-arith)
(with-ruleset real-arith
  ;; Addition commutativity
  (rewrite (Add ?x ?y) (Add ?y ?x))

  ;; Associativity
  (rewrite (Add ?x (Add ?y ?z)) (Add (Add ?x ?y) ?z))
  (rewrite (Add (Add ?x ?y) ?z) (Add ?x (Add ?y ?z)))
  (rewrite (Mul ?x (Mul ?y ?z)) (Mul (Mul ?x ?y) ?z))

  ;; Distributivity
  (rewrite (Mul ?x (Add ?y ?z)) (Add (Mul ?x ?y) (Mul ?x ?z)))
  (rewrite (Add (Mul ?x ?y) (Mul ?x ?z)) (Mul ?x (Add ?y ?z)))

  ;; Division distributivity over Add
  (rewrite (Div (Add ?x ?y) ?c) (Add (Div ?x ?c) (Div ?y ?c)))
)
"""


def constant_fold_rules() -> str:
    return """\
(ruleset const-fold)
(with-ruleset const-fold
  ;; Constant folding for integer arithmetic
  (rule ((= ?x (Add (Const ?a) (Const ?b))))
        ((union ?x (Const (+ ?a ?b)))))
  ;; Constant accumulation: Add(Add(x, a), b) → Add(x, a+b)
  (rule ((= ?x (Add (Add ?y (Const ?a)) (Const ?b))))
        ((union ?x (Add ?y (Const (+ ?a ?b))))))
  (rule ((= ?x (Sub (Const ?a) (Const ?b))))
        ((union ?x (Const (- ?a ?b)))))
  (rule ((= ?x (Mul (Const ?a) (Const ?b))))
        ((union ?x (Const (* ?a ?b)))))
  (rule ((= ?x (Div (Const ?a) (Const ?b)))
         (!= ?b 0))
        ((union ?x (Const (/ ?a ?b)))))
  (rule ((= ?x (Neg (Const ?a))))
        ((union ?x (Const (- 0 ?a)))))
)
"""


def structural_rules() -> str:
    return """\
(ruleset structural)
(with-ruleset structural
  ;; Nop elimination
  (rewrite (Seq ?x (Nop)) ?x)
  (rewrite (Seq (Nop) ?x) ?x)

  ;; Dead store elimination: Store(arr, idx, Load(arr, idx)) = Nop
  ;; Writing the same value that's already there is a no-op.
  (rewrite (Store ?arr ?idx (Load ?arr ?idx)) (Nop))
  (rewrite (Store2 ?arr ?i1 ?i2 (Load2 ?arr ?i1 ?i2)) (Nop))
  (rewrite (Store3 ?arr ?i1 ?i2 ?i3 (Load3 ?arr ?i1 ?i2 ?i3)) (Nop))

  ;; Seq associativity — canonical right-nesting
  (rewrite (Seq (Seq ?a ?b) ?c) (Seq ?a (Seq ?b ?c)))

  ;; Neg distribution over Add: -(a+b) = (-a) + (-b)
  (rewrite (Neg (Add ?x ?y)) (Add (Neg ?x) (Neg ?y)))

  ;; Neg through Mul: -(a*b) = (-a)*b
  (rewrite (Neg (Mul ?x ?y)) (Mul (Neg ?x) ?y))

  ;; Store value equivalence: Store(a, idx, e1) = Store(a, idx, e2) when e1 = e2
  ;; This is implicit in egglog — if e1 and e2 are in the same e-class,
  ;; Store nodes with them are automatically equivalent.

  ;; Seq with identical prefix/suffix
  ;; (handled by congruence closure in egglog)

  ;; For loop with equivalent body
  ;; (handled by congruence closure — if body1 = body2, For(...,body1) = For(...,body2))
)
"""


def binding_rules_full() -> str:
    """Binding-aware propagation rules with SwapDB as constructor.

    SwapDB and DbShift are CONSTRUCTORS in the Term datatype (not functions).
    This enables their use in both LHS and RHS of rewrite/rule.

    Propagation rules reduce SwapDB nodes to concrete Term nodes:
      SwapDB(Add(a,b), d1, d2) → Add(SwapDB(a,d1,d2), SwapDB(b,d1,d2))
      SwapDB(DBVar(d), d1, d2) → DBVar(d2)  when d=d1
    Eventually all SwapDB wrappers are eliminated, leaving a normal Term.

    Loop interchange uses SwapDB to express the body transformation:
      For(a,b,s1, For(c,d,s2, body))
        = For(c,d,s2, For(a,b,s1, SwapDB(body, 0, 1)))
    """
    return """\
;; === SwapDB propagation rules (binding-aware) ===
;; SwapDB is a Term constructor. These rules reduce SwapDB nodes
;; by recursing through the term structure, eventually eliminating
;; all SwapDB wrappers via congruence closure.

;; Base cases — DBVar: swap depths d1 ↔ d2
(rule ((= ?r (SwapDB (DBVar ?d) ?d1 ?d2)) (= ?d ?d1))
      ((union ?r (DBVar ?d2))))
(rule ((= ?r (SwapDB (DBVar ?d) ?d1 ?d2)) (= ?d ?d2))
      ((union ?r (DBVar ?d1))))
(rule ((= ?r (SwapDB (DBVar ?d) ?d1 ?d2)) (!= ?d ?d1) (!= ?d ?d2))
      ((union ?r (DBVar ?d))))

;; Terminals — constants and params are unaffected by variable swapping
(rule ((= ?r (SwapDB (Const ?c) ?d1 ?d2)))  ((union ?r (Const ?c))))
(rule ((= ?r (SwapDB (ConstF ?c) ?d1 ?d2))) ((union ?r (ConstF ?c))))
(rule ((= ?r (SwapDB (Param ?n) ?d1 ?d2)))  ((union ?r (Param ?n))))

;; Arithmetic — propagate SwapDB to operands
(rewrite (SwapDB (Add ?a ?b) ?d1 ?d2) (Add (SwapDB ?a ?d1 ?d2) (SwapDB ?b ?d1 ?d2)))
(rewrite (SwapDB (Mul ?a ?b) ?d1 ?d2) (Mul (SwapDB ?a ?d1 ?d2) (SwapDB ?b ?d1 ?d2)))
(rewrite (SwapDB (Sub ?a ?b) ?d1 ?d2) (Sub (SwapDB ?a ?d1 ?d2) (SwapDB ?b ?d1 ?d2)))
(rewrite (SwapDB (Div ?a ?b) ?d1 ?d2) (Div (SwapDB ?a ?d1 ?d2) (SwapDB ?b ?d1 ?d2)))
(rewrite (SwapDB (Neg ?a) ?d1 ?d2)    (Neg (SwapDB ?a ?d1 ?d2)))

;; Load/Store — propagate to indices and values
(rewrite (SwapDB (Load ?arr ?idx) ?d1 ?d2)
         (Load ?arr (SwapDB ?idx ?d1 ?d2)))
(rewrite (SwapDB (Load2 ?arr ?i1 ?i2) ?d1 ?d2)
         (Load2 ?arr (SwapDB ?i1 ?d1 ?d2) (SwapDB ?i2 ?d1 ?d2)))
(rewrite (SwapDB (Store ?arr ?idx ?val) ?d1 ?d2)
         (Store ?arr (SwapDB ?idx ?d1 ?d2) (SwapDB ?val ?d1 ?d2)))
(rewrite (SwapDB (Store2 ?arr ?i1 ?i2 ?val) ?d1 ?d2)
         (Store2 ?arr (SwapDB ?i1 ?d1 ?d2) (SwapDB ?i2 ?d1 ?d2) (SwapDB ?val ?d1 ?d2)))
(rewrite (SwapDB (Load3 ?arr ?i1 ?i2 ?i3) ?d1 ?d2)
         (Load3 ?arr (SwapDB ?i1 ?d1 ?d2) (SwapDB ?i2 ?d1 ?d2) (SwapDB ?i3 ?d1 ?d2)))
(rewrite (SwapDB (Store3 ?arr ?i1 ?i2 ?i3 ?val) ?d1 ?d2)
         (Store3 ?arr (SwapDB ?i1 ?d1 ?d2) (SwapDB ?i2 ?d1 ?d2) (SwapDB ?i3 ?d1 ?d2) (SwapDB ?val ?d1 ?d2)))

;; Seq — propagate to both statements
(rewrite (SwapDB (Seq ?a ?b) ?d1 ?d2)
         (Seq (SwapDB ?a ?d1 ?d2) (SwapDB ?b ?d1 ?d2)))

;; For — propagate, incrementing depths inside the binder
(rewrite (SwapDB (For ?lo ?hi ?step ?body) ?d1 ?d2)
         (For (SwapDB ?lo ?d1 ?d2) (SwapDB ?hi ?d1 ?d2)
              (SwapDB ?step ?d1 ?d2) (SwapDB ?body (+ ?d1 1) (+ ?d2 1))))

;; Nop
(rule ((= ?r (SwapDB (Nop) ?d1 ?d2))) ((union ?r (Nop))))

;; === DbShift propagation rules ===
;; DbShift(term, delta, cutoff) shifts free variables >= cutoff by delta.
;; Used for adjusting De Bruijn indices when terms move across binders.

;; Base case — DBVar: shift if depth >= cutoff
(rule ((= ?r (DbShift (DBVar ?d) ?delta ?cutoff))
       (>= ?d ?cutoff))
      ((union ?r (DBVar (+ ?d ?delta)))))
(rule ((= ?r (DbShift (DBVar ?d) ?delta ?cutoff))
       (< ?d ?cutoff))
      ((union ?r (DBVar ?d))))

;; Terminals
(rule ((= ?r (DbShift (Const ?c) ?delta ?cutoff)))  ((union ?r (Const ?c))))
(rule ((= ?r (DbShift (ConstF ?c) ?delta ?cutoff))) ((union ?r (ConstF ?c))))
(rule ((= ?r (DbShift (Param ?n) ?delta ?cutoff)))  ((union ?r (Param ?n))))

;; Arithmetic
(rewrite (DbShift (Add ?a ?b) ?d ?c) (Add (DbShift ?a ?d ?c) (DbShift ?b ?d ?c)))
(rewrite (DbShift (Mul ?a ?b) ?d ?c) (Mul (DbShift ?a ?d ?c) (DbShift ?b ?d ?c)))
(rewrite (DbShift (Sub ?a ?b) ?d ?c) (Sub (DbShift ?a ?d ?c) (DbShift ?b ?d ?c)))
(rewrite (DbShift (Div ?a ?b) ?d ?c) (Div (DbShift ?a ?d ?c) (DbShift ?b ?d ?c)))
(rewrite (DbShift (Neg ?a) ?d ?c)    (Neg (DbShift ?a ?d ?c)))

;; Load/Store
(rewrite (DbShift (Load ?arr ?idx) ?d ?c)
         (Load ?arr (DbShift ?idx ?d ?c)))
(rewrite (DbShift (Load2 ?arr ?i1 ?i2) ?d ?c)
         (Load2 ?arr (DbShift ?i1 ?d ?c) (DbShift ?i2 ?d ?c)))
(rewrite (DbShift (Store ?arr ?idx ?val) ?d ?c)
         (Store ?arr (DbShift ?idx ?d ?c) (DbShift ?val ?d ?c)))
(rewrite (DbShift (Store2 ?arr ?i1 ?i2 ?val) ?d ?c)
         (Store2 ?arr (DbShift ?i1 ?d ?c) (DbShift ?i2 ?d ?c) (DbShift ?val ?d ?c)))
(rewrite (DbShift (Load3 ?arr ?i1 ?i2 ?i3) ?d ?c)
         (Load3 ?arr (DbShift ?i1 ?d ?c) (DbShift ?i2 ?d ?c) (DbShift ?i3 ?d ?c)))
(rewrite (DbShift (Store3 ?arr ?i1 ?i2 ?i3 ?val) ?d ?c)
         (Store3 ?arr (DbShift ?i1 ?d ?c) (DbShift ?i2 ?d ?c) (DbShift ?i3 ?d ?c) (DbShift ?val ?d ?c)))

;; Seq
(rewrite (DbShift (Seq ?a ?b) ?d ?c)
         (Seq (DbShift ?a ?d ?c) (DbShift ?b ?d ?c)))

;; For — increment cutoff inside binder
(rewrite (DbShift (For ?lo ?hi ?step ?body) ?d ?c)
         (For (DbShift ?lo ?d ?c) (DbShift ?hi ?d ?c)
              (DbShift ?step ?d ?c) (DbShift ?body ?d (+ ?c 1))))

;; Nop
(rule ((= ?r (DbShift (Nop) ?d ?c))) ((union ?r (Nop))))

;; === Subst propagation rules ===
;; Subst(term, depth, repl) substitutes DBVar(depth) with repl.
;; Used for loop peeling: extracting a specific iteration from a loop body.

;; Base case — DBVar: substitute if depth matches
(rule ((= ?r (Subst (DBVar ?d) ?target ?repl)) (= ?d ?target))
      ((union ?r ?repl)))
(rule ((= ?r (Subst (DBVar ?d) ?target ?repl)) (!= ?d ?target))
      ((union ?r (DBVar ?d))))

;; Terminals
(rule ((= ?r (Subst (Const ?c) ?target ?repl)))  ((union ?r (Const ?c))))
(rule ((= ?r (Subst (ConstF ?c) ?target ?repl))) ((union ?r (ConstF ?c))))
(rule ((= ?r (Subst (Param ?n) ?target ?repl)))  ((union ?r (Param ?n))))
(rule ((= ?r (Subst (Nop) ?target ?repl)))       ((union ?r (Nop))))

;; Arithmetic
(rewrite (Subst (Add ?a ?b) ?t ?r) (Add (Subst ?a ?t ?r) (Subst ?b ?t ?r)))
(rewrite (Subst (Mul ?a ?b) ?t ?r) (Mul (Subst ?a ?t ?r) (Subst ?b ?t ?r)))
(rewrite (Subst (Sub ?a ?b) ?t ?r) (Sub (Subst ?a ?t ?r) (Subst ?b ?t ?r)))
(rewrite (Subst (Div ?a ?b) ?t ?r) (Div (Subst ?a ?t ?r) (Subst ?b ?t ?r)))
(rewrite (Subst (Neg ?a) ?t ?r)    (Neg (Subst ?a ?t ?r)))

;; Load/Store
(rewrite (Subst (Load ?arr ?idx) ?t ?r)
         (Load ?arr (Subst ?idx ?t ?r)))
(rewrite (Subst (Load2 ?arr ?i1 ?i2) ?t ?r)
         (Load2 ?arr (Subst ?i1 ?t ?r) (Subst ?i2 ?t ?r)))
(rewrite (Subst (Load3 ?arr ?i1 ?i2 ?i3) ?t ?r)
         (Load3 ?arr (Subst ?i1 ?t ?r) (Subst ?i2 ?t ?r) (Subst ?i3 ?t ?r)))
(rewrite (Subst (Store ?arr ?idx ?val) ?t ?r)
         (Store ?arr (Subst ?idx ?t ?r) (Subst ?val ?t ?r)))
(rewrite (Subst (Store2 ?arr ?i1 ?i2 ?val) ?t ?r)
         (Store2 ?arr (Subst ?i1 ?t ?r) (Subst ?i2 ?t ?r) (Subst ?val ?t ?r)))
(rewrite (Subst (Store3 ?arr ?i1 ?i2 ?i3 ?val) ?t ?r)
         (Store3 ?arr (Subst ?i1 ?t ?r) (Subst ?i2 ?t ?r) (Subst ?i3 ?t ?r) (Subst ?val ?t ?r)))

;; Seq
(rewrite (Subst (Seq ?a ?b) ?t ?r)
         (Seq (Subst ?a ?t ?r) (Subst ?b ?t ?r)))

;; For — increment target inside binder (DBVar shifts under binder)
(rewrite (Subst (For ?lo ?hi ?step ?body) ?t ?r)
         (For (Subst ?lo ?t ?r) (Subst ?hi ?t ?r)
              (Subst ?step ?t ?r) (Subst ?body (+ ?t 1) ?r)))

;; === Polyhedral-gated relations ===
;; ScheduleLegal is asserted by polyhedral analysis when it confirms
;; that the candidate schedule preserves all data dependences.
;; Always declared; only populated when polyhedral analysis provides the fact.
(relation ScheduleLegal ())
(relation FootprintMatch ())

;; === Loop interchange rewrite rule (polyhedral-gated) ===
;; Exchanges two nested For loops, adjusting variable bindings via SwapDB.
;; SwapDB(body, 0, 1) swaps DBVar(0) ↔ DBVar(1) in the body.
;;
;; Gated by (ScheduleLegal): polyhedral analysis must confirm that
;; the candidate schedule preserves all data dependences before this
;; rule is enabled. Polyhedral analysis provides PERMISSION, egglog does
;; the DERIVATION via SwapDB propagation + congruence closure.
(rule ((= ?r (For ?a ?b ?s1 (For ?c ?d ?s2 ?body)))
       (ScheduleLegal))
      ((union ?r (For ?c ?d ?s2 (For ?a ?b ?s1 (SwapDB ?body 0 1))))))

;; === Statement reorder (polyhedral-gated) ===
;; Seq(a, b) = Seq(b, a) when polyhedral analysis confirms that
;; reordering preserves all data dependences.
(rule ((= ?r (Seq ?a ?b))
       (ScheduleLegal))
      ((union ?r (Seq ?b ?a))))

;; === Loop fusion (polyhedral-gated) ===
;; Two adjacent loops with identical bounds can be fused into one loop
;; containing a Seq of both bodies. Only when polyhedral analysis confirms safety.
(rule ((= ?r (Seq (For ?lo ?hi ?s ?b1) (For ?lo ?hi ?s ?b2)))
       (ScheduleLegal))
      ((union ?r (For ?lo ?hi ?s (Seq ?b1 ?b2)))))

;; === Loop fission (polyhedral-gated) ===
;; A loop over a Seq body can be split into two adjacent loops.
;; Reverse of fusion — only when polyhedral analysis confirms safety.
(rule ((= ?r (For ?lo ?hi ?s (Seq ?b1 ?b2)))
       (ScheduleLegal))
      ((union ?r (Seq (For ?lo ?hi ?s ?b1) (For ?lo ?hi ?s ?b2)))))
"""


def all_rules(*, mode: str = "fp_safe") -> str:
    parts = [arithmetic_rules_fp_safe(), constant_fold_rules(),
             structural_rules()]
    if mode == "real":
        parts.append(arithmetic_rules_real())
    return "\n".join(parts)


def run_schedule(*, mode: str = "fp_safe", run_global: bool = False,
                 term_size: int = 0) -> str:
    rulesets = ["fp-safe", "const-fold", "structural"]
    if mode == "real":
        rulesets.append("real-arith")
    # Adaptive saturation: small programs get more rounds to let
    # SwapDB fully propagate through nested structures. Large programs
    # keep fewer rounds to avoid e-graph explosion.
    if run_global and term_size < 1000:
        rounds = 6
    else:
        rounds = 3
    limit = 100000
    lines = [f"(let-scheduler bo (back-off :match-limit {limit}))"]
    for _round in range(rounds):
        for rs in rulesets:
            lines.append(f"(run-with bo {rs})")
        if run_global:
            lines.append("(run-with bo)")
    return "(run-schedule\n  " + "\n  ".join(lines) + ")\n"
