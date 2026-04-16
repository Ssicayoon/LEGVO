"""CLI entry point for the polyhedral verifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="legvo-polyhedral",
        description="Polyhedral equivalence verifier for affine loop kernels",
    )
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument(
        "-I", "--include-dir", action="append", default=[], type=Path,
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    from .extract import extract_scop
    from .verify import verify

    try:
        ref = extract_scop(args.reference, include_dirs=args.include_dir)
    except (ValueError, ImportError) as exc:
        print(f"Error extracting reference: {exc}", file=sys.stderr)
        return 1

    try:
        cand = extract_scop(args.candidate, include_dirs=args.include_dir)
    except (ValueError, ImportError) as exc:
        print(f"Error extracting candidate: {exc}", file=sys.stderr)
        return 1

    result = verify(ref, cand)

    if args.json:
        print(json.dumps({
            "status": result.status,
            "reason": result.reason,
            "checks": result.checks,
        }, indent=2))
    else:
        print(f"{result.status}: {result.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
