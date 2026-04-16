from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class ScopModel:
    """Polyhedral model of a single SCoP region.

    All fields are isl string representations.
    """

    domain: str     # isl union set: iteration domains
    schedule: str   # isl union map: instance -> execution time
    reads: str      # isl union map: instance -> read memory location
    writes: str     # isl union map: instance -> written memory location


@dataclass(frozen=True)
class VerifyResult:
    """Result of polyhedral equivalence verification."""

    status: Literal["equivalent", "unknown", "error"]
    reason: str
    checks: dict = field(default_factory=dict)
