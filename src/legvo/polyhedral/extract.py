"""Extract a ScopModel from a C source file via tadashi / PET."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

from .model import ScopModel


def _ensure_tadashi() -> None:
    """Make sure the ``tadashi`` package is importable."""
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

    # Try <repo-root>/tadashi
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / "tadashi"
    if (candidate / "tadashi").is_dir():
        sys.path.insert(0, str(candidate))
        return

    raise ImportError(
        "tadashi not found. Set TADASHI_ROOT env var or place a "
        "tadashi/ directory at the repository root."
    )


def extract_scop(
    source: Path,
    include_dirs: Iterable[Path] = (),
) -> ScopModel:
    """Parse *source* with PET and return its polyhedral model.

    The file must contain exactly one ``#pragma scop`` / ``#pragma endscop``
    region.
    """
    _ensure_tadashi()
    from tadashi.translators import Pet  # type: ignore[import-untyped]

    translator = Pet()
    options: list[str] = []
    for d in include_dirs:
        options.extend(["-I", str(d)])
    translator.set_source(source, options)

    if not translator.scops:
        raise ValueError(f"No SCoP region found in {source}")
    if len(translator.scops) > 1:
        raise ValueError(
            f"Found {len(translator.scops)} SCoP regions in {source}; "
            f"only single-SCoP inputs are supported"
        )

    scop = translator.scops[0]
    return ScopModel(
        domain=scop.domain_str,
        schedule=scop.schedule_map_str,
        reads=scop.may_reads_str,
        writes=scop.may_writes_str,
    )
