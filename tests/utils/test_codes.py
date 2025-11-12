import types
from datetime import datetime

import pytest

from app.utils.codes import build_tracking_code, generate_tracking_code


@pytest.mark.parametrize(
    "year,seq,expected",
    [
        (2025, 1, "PRC-2025-000001"),
        (2025, 42, "PRC-2025-000042"),
        (2025, 123456, "PRC-2025-123456"),
        (1999, 7, "PRC-1999-000007"),
    ],
)
def test_build_tracking_code_basic(year, seq, expected):
    assert build_tracking_code(year, seq) == expected


def test_build_tracking_code_zero_seq():
    # Behavior is defined: zero is allowed and zero-padded.
    assert build_tracking_code(2025, 0) == "PRC-2025-000000"


def test_generate_tracking_code_uses_current_year(monkeypatch):
    # Patch module-level datetime used inside codes.py
    # We replace it with a simple object exposing utcnow().year
    fake_dt = types.SimpleNamespace(
        utcnow=lambda: datetime(2033, 5, 4, 12, 0, 0)
    )

    # Import target module and patch its datetime symbol
    import app.utils.codes as codes
    monkeypatch.setattr(codes, "datetime", fake_dt, raising=True)

    # When id = 15 and fake year = 2033 → code must include 2033 and be zero-padded
    assert codes.generate_tracking_code(15) == "PRC-2033-000015"


@pytest.mark.parametrize("bad_seq", [-1, -10])
def test_build_tracking_code_negative_seq(bad_seq):
    # Current implementation allows negatives; decide expected behavior.
    # For MVP we assert the raw formatting outcome for transparency.
    expected = f"PRC-2025--{abs(bad_seq):05d}" if bad_seq < 0 else ""
    assert build_tracking_code(2025, bad_seq) == expected
