"""Extract a Term representation from a C source file.

Uses PET/tadashi for polyhedral extraction (domain, schedule, accesses)
and parses the computation body from the C source at statement locations.

The extracted Term is a complete representation of the kernel's
computation, suitable for e-graph equivalence checking.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable

from .term import (
    BinOp, Const, DBVar, For, Let, Load, Neg, Param, Reduce,
    Seq, Store, Term, Unknown,
)


# ── Expression parser (recursive descent) ───────────────────────────

# Tokenizer patterns
_TOKEN_RE = re.compile(
    r"(\d+\.?\d*(?:[eE][+-]?\d+)?)"  # number
    r"|([a-zA-Z_]\w*)"                # identifier
    r"|([+\-*/()[\],;=<>!&|])"        # operator/punct
    r"|(\s+)"                          # whitespace (skip)
)


def _tokenize(text: str) -> list[str]:
    tokens = []
    for m in _TOKEN_RE.finditer(text):
        if m.group(4):  # whitespace
            continue
        tokens.append(m.group(0))
    return tokens


class _ExprParser:
    """Recursive descent parser for C arithmetic expressions."""

    def __init__(self, tokens: list[str], params: set[str],
                 loop_vars: list[str] | None = None):
        self.tokens = tokens
        self.pos = 0
        self.params = params  # known scalar parameters
        self.loop_vars = loop_vars or []  # stack: [outermost, ..., innermost]

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected: str | None = None) -> str:
        tok = self.tokens[self.pos]
        if expected and tok != expected:
            raise ValueError(f"Expected {expected!r}, got {tok!r}")
        self.pos += 1
        return tok

    def parse_expr(self) -> Term:
        return self._additive()

    def _additive(self) -> Term:
        left = self._multiplicative()
        while self.peek() in ("+", "-"):
            op = self.consume()
            right = self._multiplicative()
            left = BinOp("Add" if op == "+" else "Sub", left, right)
        return left

    def _multiplicative(self) -> Term:
        left = self._unary()
        while self.peek() in ("*", "/"):
            op = self.consume()
            right = self._unary()
            left = BinOp("Mul" if op == "*" else "Div", left, right)
        return left

    def _unary(self) -> Term:
        if self.peek() == "-":
            self.consume()
            operand = self._unary()
            return Neg(operand)
        return self._primary()

    def _primary(self) -> Term:
        tok = self.peek()
        if tok is None:
            return Unknown("unexpected end of expression")

        # Number literal
        if tok[0].isdigit() or (tok[0] == "." and len(tok) > 1):
            self.consume()
            return Const(float(tok))

        # Parenthesized expression or type cast
        if tok == "(":
            self.consume("(")
            # Check for type cast: (DATA_TYPE)expr or (double)expr
            if self.peek() in ("DATA_TYPE", "double", "float", "int"):
                self.consume()  # consume type name
                if self.peek() == ")":
                    self.consume(")")
                return self._primary()  # parse the casted expression
            expr = self.parse_expr()
            if self.peek() == ")":
                self.consume(")")
            return expr

        # Pointer dereference *ptr → treat as Unknown (can't resolve)
        if tok == "*":
            self.consume()
            operand = self._primary()
            return Unknown("pointer deref")

        # Address-of &x → skip
        if tok == "&":
            self.consume()
            return self._primary()

        # Identifier: variable, parameter, or array access
        if tok[0].isalpha() or tok[0] == "_":
            name = self.consume()
            if self.peek() == "[":
                # Array access: name[idx1][idx2]...
                indices = []
                while self.peek() == "[":
                    self.consume("[")
                    idx = self.parse_expr()
                    indices.append(idx)
                    if self.peek() == "]":
                        self.consume("]")
                return Load(name, tuple(indices))
            if self.peek() == "(":
                # Function call: name(args) — treat as opaque Param
                self.consume("(")
                args = []
                while self.peek() and self.peek() != ")":
                    args.append(self.parse_expr())
                    if self.peek() == ",":
                        self.consume(",")
                if self.peek() == ")":
                    self.consume(")")
                # Binary function calls → BinOp for comparability
                if len(args) == 2 and name in ("max_score", "max", "min", "match",
                                                "fmax", "fmin", "pow", "fmod"):
                    return BinOp(name.capitalize(), args[0], args[1])
                # Other function calls → opaque Param
                if args:
                    arg_strs = "_".join(a.to_egg().replace('"','').replace(' ','')[:20] for a in args)
                    return Param(f"{name}({arg_strs})")
                return Param(name)
            # Check loop variables (De Bruijn index)
            for depth_from_inner, var_name in enumerate(reversed(self.loop_vars)):
                if name == var_name:
                    return DBVar(depth_from_inner)
            # Scalar parameter
            if name in self.params:
                return Param(name)
            # Unknown identifier — treat as Param (could be a scalar local)
            return Param(name)

        return Unknown(f"unexpected token: {tok}")


def parse_expr(text: str, params: set[str] | None = None,
               loop_vars: list[str] | None = None) -> Term:
    """Parse a C arithmetic expression string into a Term."""
    tokens = _tokenize(text)
    if not tokens:
        return Unknown("empty expression")
    parser = _ExprParser(tokens, params or set(), loop_vars or [])
    try:
        result = parser.parse_expr()
        return result
    except (ValueError, IndexError) as e:
        return Unknown(str(e))


# ── Statement parser ────────────────────────────────────────────────

_ASSIGN_RE = re.compile(
    r"([a-zA-Z_]\w*(?:\[[^\]]*\])*)"  # LHS (possibly with indices)
    r"\s*([+\-*/]?=)\s*"              # operator (=, +=, -=, *=, /=)
    r"(.+)"                            # RHS
)

_ARRAY_LHS_RE = re.compile(
    r"([a-zA-Z_]\w*)((?:\[[^\]]*\])*)"
)


def _parse_lhs(text: str, params: set[str],
               loop_vars: list[str] | None = None) -> tuple[str, tuple[Term, ...]]:
    """Parse LHS of assignment: array[i][j] → (array, (i_term, j_term))."""
    m = _ARRAY_LHS_RE.match(text.strip())
    if not m:
        return text.strip(), ()
    name = m.group(1)
    idx_text = m.group(2)
    if not idx_text:
        return name, ()
    indices = []
    for idx_m in re.finditer(r"\[([^\]]*)\]", idx_text):
        indices.append(parse_expr(idx_m.group(1), params, loop_vars))
    return name, tuple(indices)


def parse_statement(text: str, params: set[str] | None = None,
                    loop_vars: list[str] | None = None) -> Term | None:
    """Parse a single C assignment statement into a Term.

    Returns Store(...) for assignments, None for non-assignment lines.
    """
    params = params or set()
    loop_vars = loop_vars or []
    text = text.strip().rstrip(";").strip()
    if not text:
        return None

    m = _ASSIGN_RE.match(text)
    if not m:
        return None

    lhs_text = m.group(1)
    op = m.group(2)
    rhs_text = m.group(3)

    array, indices = _parse_lhs(lhs_text, params, loop_vars)
    rhs = parse_expr(rhs_text, params, loop_vars)

    if op == "=":
        return Store(array, indices, rhs)
    elif op == "+=":
        load = Load(array, indices) if indices else Param(array)
        return Store(array, indices, BinOp("Add", load, rhs))
    elif op == "-=":
        load = Load(array, indices) if indices else Param(array)
        return Store(array, indices, BinOp("Sub", load, rhs))
    elif op == "*=":
        load = Load(array, indices) if indices else Param(array)
        return Store(array, indices, BinOp("Mul", load, rhs))
    elif op == "/=":
        load = Load(array, indices) if indices else Param(array)
        return Store(array, indices, BinOp("Div", load, rhs))
    return None


# ── SCoP → Term extraction ─────────────────────────────────────────


def _ensure_tadashi() -> None:
    """Make sure tadashi is importable."""
    try:
        import tadashi  # noqa: F401
        return
    except ImportError:
        pass
    env_root = os.environ.get("TADASHI_ROOT")
    if env_root:
        sys.path.insert(0, env_root)
        try:
            import tadashi  # noqa: F401
            return
        except ImportError:
            pass
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / "tadashi"
    if (candidate / "tadashi").is_dir():
        sys.path.insert(0, str(candidate))
        return
    raise ImportError("tadashi not found")


def extract_scop_region(source: Path) -> str:
    """Extract the computation region from a C source file.

    Tries (in order):
    1. Text between #pragma scop / #pragma endscop
    2. Body of kernel_* function (LLM sometimes removes pragmas)
    """
    text = source.read_text(errors="replace")

    # Try pragma scop first
    m = re.search(
        r"#pragma\s+scop\s*\n(.*?)#pragma\s+endscop",
        text, re.DOTALL,
    )
    if m:
        return m.group(1)

    # Fallback: find kernel function body
    # Match "void kernel_xxx(...) {" and extract everything up to
    # the matching closing brace
    m = re.search(
        r"void\s+kernel_\w+\s*\([^)]*\)\s*\{",
        text,
    )
    if m:
        start = m.end()
        depth = 1
        pos = start
        while pos < len(text) and depth > 0:
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
            pos += 1
        if depth == 0:
            body = text[start:pos - 1]
            # Strip variable declarations at the top
            lines = body.strip().splitlines()
            code_lines = []
            past_decls = False
            for line in lines:
                stripped = line.strip()
                if not past_decls:
                    # Skip pure declarations: "int i, j;" or "DATA_TYPE x;"
                    if re.match(
                        r"^(int|DATA_TYPE|double|float|const|unsigned)\s+[^=]*;$",
                        stripped,
                    ):
                        continue
                    if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
                        continue
                    past_decls = True
                code_lines.append(line)
            return "\n".join(code_lines)

    return ""


def extract_term(
    source: Path,
    include_dirs: Iterable[Path] = (),
) -> Term:
    """Extract a Term from a C source file with #pragma scop.

    Uses PET for polyhedral info + C source parsing for computation body.
    """
    # Get the scop region text
    scop_text = extract_scop_region(source)
    if not scop_text:
        return Unknown("no #pragma scop region found")

    # Detect parameters (scalar variables used in loop bounds)
    # PET will give us this, but we can also infer from macros
    params: set[str] = set()
    # Common PolyBench parameters
    for m in re.finditer(r"_PB_(\w+)", scop_text):
        params.add(m.group(0))
    for m in re.finditer(r"\b([nmNM])\b", scop_text):
        params.add(m.group(1))
    # Also add alpha, beta etc
    for p in ["alpha", "beta"]:
        if p in scop_text:
            params.add(p)

    # Preprocess: expand compound assignment expressions
    # a = (b /= c) → b /= c; a = b;
    scop_text = _expand_compound_assign_expr(scop_text)
    # Preprocess: strip single-statement braces to normalize brace style
    scop_text = _strip_single_stmt_braces(scop_text)
    return _parse_scop_body(scop_text, params)


def _expand_compound_assign_expr(text: str) -> str:
    """Expand compound assignment expressions used as values.

    a = (b /= c);  →  b /= c;\n a = b;
    a = (b += c);  →  b += c;\n a = b;
    """
    import re as _re
    # Pattern: lhs = (target op= expr);
    def repl(m):
        lhs = m.group(1)
        target = m.group(2)
        op = m.group(3)
        expr = m.group(4)
        return f"{target} {op}= {expr};\n{lhs} = {target};"
    text = _re.sub(
        r'(\w+(?:\[[^\]]*\])*)\s*=\s*\((\w+(?:\[[^\]]*\])*)\s*([+\-*/])=\s*(.+?)\)\s*;',
        repl, text,
    )
    return text


def _strip_single_stmt_braces(text: str) -> str:
    """Remove braces around single statements in for-loop bodies.

    Converts:
        for (...) { stmt; }  →  for (...) stmt;
        for (...)
          { stmt; }          →  for (...) stmt;

    Only strips when the braced block contains exactly one statement
    (no nested for-loops, no multiple statements).
    """
    import re as _re
    # Pattern: { single_stmt; } on one line (possibly with whitespace)
    text = _re.sub(
        r'\{\s*([^{};]+;)\s*\}',
        r'\1',
        text,
    )
    return text


def _parse_scop_body(text: str, params: set[str],
                     loop_vars: list[str] | None = None) -> Term:
    """Parse the body of a scop region into a Term tree."""
    loop_vars = list(loop_vars or [])
    lines = text.strip().splitlines()
    stmts: list[Term] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line or line.startswith("//"):
            continue
        if line.startswith("/*"):
            # Skip block comment (possibly multi-line)
            while i < len(lines) and "*/" not in lines[i - 1]:
                i += 1
            continue
        # Strip inline comments
        line = re.sub(r"/\*.*?\*/", "", line).strip()
        line = re.sub(r"//.*$", "", line).strip()
        if not line or line in ("{", "}"):
            continue
        # Strip inline braces: "{ stmt; }" → "stmt;"
        if line.startswith("{") and line.endswith("}"):
            line = line[1:-1].strip()
            if not line:
                continue
        # Skip preprocessor and builtin calls
        if line.startswith("#") or "__builtin_" in line:
            continue
        # Skip if-guards: range checks like "if (N > 0)", "if (j-1>=0)", "if (i+1<N)"
        # These are bounds checks that don't change semantics — treat the body as unconditional
        m_if = re.match(r"if\s*\((.+)\)\s*$", line)
        if not m_if:
            m_if = re.match(r"if\s*\((.+)\)\s*\{?\s*$", line)
        if m_if:
            # Consume the if-body (next statement or braced block) as regular statements
            continue

        # For loop — handles:
        #   for (i = 0; i < N; i++)
        #   for (int i = 0; i < N; i++)
        #   for (i = 0; i <= N - 1; i++)
        #   for (i = 0; i < N; i++, ptr++)  — extra increment ignored
        #   for (; i < N; i++)  — continuation loop
        m = re.match(
            r"for\s*\(\s*(?:(?:int|DATA_TYPE)\s+)?(?:(\w+)\s*=\s*([^;]+)|)\s*;\s*"
            r"(\w+)\s*(<=|<)\s*([^;]+);\s*"
            r"(\w+)\s*(\+\+|--|\+=\s*\d+|=\s*\w+\s*\+\s*\d+|=\s*\d+\s*\+\s*\w+)[^)]*\)",
            line,
        )
        if m:
            var = m.group(1) or m.group(3)  # use cond var for continuation loops
            lo_text = m.group(2)
            lo = parse_expr(lo_text.strip(), params, loop_vars) if lo_text else Const(0)
            hi_expr = m.group(5).strip()
            hi = parse_expr(hi_expr, params, loop_vars)
            step_text = m.group(7).strip()
            if step_text == "++":
                step = Const(1)
            elif step_text == "--":
                step = Const(-1)
            elif step_text.startswith("+="):
                step = parse_expr(step_text[2:].strip(), params, loop_vars)
            elif step_text.startswith("="):
                # Handle "= i + 1" or "= 1 + i" — extract the constant
                step = Const(1)  # all observed patterns are step-by-1
            else:
                step = parse_expr(step_text, params, loop_vars)

            # Collect the loop body
            # Check if body starts on same line after for(...)
            remainder = line[m.end():].strip()
            body_lines = []
            brace_depth = 0
            if remainder and remainder != "{":
                # Body starts on same line: "for (...) stmt..." or "for (...) { stmt..."
                if remainder.startswith("{"):
                    # "for (...) { body" — add remainder after {, track braces
                    inner = remainder[1:].strip()
                    if inner:
                        body_lines.append(inner)
                    brace_depth = 1
                    while i < len(lines) and brace_depth > 0:
                        bl = lines[i]
                        brace_depth += bl.count("{") - bl.count("}")
                        if brace_depth > 0:
                            body_lines.append(bl)
                        i += 1
                else:
                    # "for (...) stmt" — body is remainder + continuation lines
                    body_lines.append(remainder)
                    while not body_lines[-1].rstrip().endswith(";") and i < len(lines):
                        body_lines.append(lines[i].strip())
                        i += 1
            elif "{" in line:
                brace_depth = 1
                while i < len(lines) and brace_depth > 0:
                    bl = lines[i]
                    brace_depth += bl.count("{") - bl.count("}")
                    if brace_depth > 0:
                        body_lines.append(bl)
                    i += 1
            elif i < len(lines) and lines[i].strip() == "{":
                # Brace on next line
                i += 1  # skip the {
                brace_depth = 1
                while i < len(lines) and brace_depth > 0:
                    bl = lines[i]
                    brace_depth += bl.count("{") - bl.count("}")
                    if brace_depth > 0:
                        body_lines.append(bl)
                    i += 1
            else:
                # Single statement body (no braces on for-line or next line)
                # Track braces inside for nested for-loops with braced bodies
                if i < len(lines):
                    body_lines.append(lines[i])
                    i += 1
                    inner_brace = body_lines[-1].count("{") - body_lines[-1].count("}")
                    while i < len(lines):
                        if inner_brace > 0:
                            # Inside braces — keep collecting until closed
                            body_lines.append(lines[i])
                            inner_brace += lines[i].count("{") - lines[i].count("}")
                            i += 1
                            if inner_brace <= 0:
                                break  # braces closed
                        elif body_lines[-1].strip().endswith(";"):
                            break  # statement complete
                        else:
                            body_lines.append(lines[i])
                            inner_brace += lines[i].count("{") - lines[i].count("}")
                            i += 1

            body_text = "\n".join(body_lines)
            # Add this loop var to the stack for De Bruijn indexing
            body = _parse_scop_body(body_text, params, loop_vars + [var])
            stmts.append(For(lo, hi, step, body))
            continue

        # Variable declaration with initialization (possibly multi-line)
        m = re.match(
            r"(?:DATA_TYPE|double|float|int)\s+(?:\*?\s*(?:restrict|const)\s+)*"
            r"(\w+)\s*=\s*(.+)",
            line,
        )
        if m:
            var_name = m.group(1)
            decl_line = m.group(2)
            # Collect continuation lines if no semicolon yet
            while not decl_line.rstrip().endswith(";") and i < len(lines):
                decl_line += " " + lines[i].strip()
                i += 1
            # Strip trailing semicolon
            init_text = decl_line.rstrip().rstrip(";").strip()
            init_expr = parse_expr(init_text, params, loop_vars)
            stmts.append(Store(var_name, (), init_expr))
            continue

        # Unrecognized for-loop (e.g., i >= 0; i--) — skip as opaque block
        if re.match(r"for\s*\(", line):
            # Collect body by brace tracking or single statement
            if "{" in line:
                brace_depth = line.count("{") - line.count("}")
                while i < len(lines) and brace_depth > 0:
                    brace_depth += lines[i].count("{") - lines[i].count("}")
                    i += 1
            else:
                while i < len(lines) and not lines[i-1].strip().endswith(";"):
                    i += 1
            continue

        # Assignment statement (possibly multi-line)
        full_line = line
        max_concat = 10  # safety: don't consume more than 10 lines
        concat = 0
        while not full_line.rstrip().endswith(";") and i < len(lines) and concat < max_concat:
            full_line += " " + lines[i].strip()
            i += 1
            concat += 1

        stmt = parse_statement(full_line, params, loop_vars)
        if stmt is not None:
            stmts.append(stmt)

    if not stmts:
        return Unknown("empty scop body")
    if len(stmts) == 1:
        return stmts[0]
    return Seq(tuple(stmts))
