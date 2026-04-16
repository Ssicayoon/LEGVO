"""Integration tests for the unified e-graph verifier."""

import pytest
from pathlib import Path

from legvo.egraph.verify import verify

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"

_egglog = Path(__file__).resolve().parents[2] / "egglog-experimental" / "target" / "release" / "egglog-experimental"

pytestmark = pytest.mark.skipif(
    not _egglog.is_file(),
    reason="egglog-experimental not built",
)


class TestEgraphVerify:
    def test_identity(self):
        """Same file → equivalent."""
        r = verify(
            EXAMPLES / "interchange_ref.c",
            EXAMPLES / "interchange_ref.c",
            egglog_bin=_egglog,
        )
        assert r.status == "equivalent"

    def test_interchange_commutative_body(self):
        """Interchange with commutative body (Add)."""
        r = verify(
            EXAMPLES / "interchange_ref.c",
            EXAMPLES / "interchange_cand.c",
            egglog_bin=_egglog,
            mode="real",
        )
        # May be equivalent (if loop interchange rule applies) or unknown
        assert r.status in ("equivalent", "unknown")
