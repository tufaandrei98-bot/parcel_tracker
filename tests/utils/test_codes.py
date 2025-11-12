import types
from datetime import datetime

import pytest

from freezegun import freeze_time

from app.utils.codes import build_tracking_code, generate_tracking_code


@pytest.mark.parametrize(
    "year,seq,expected",
    [
        (2025, 1, "PRC-2025-000001"),
        (2025, 42, "PRC-2025-000042"),
        (2025, 123456, "PRC-2025-123456"),
        (2025, 999999, "PRC-2025-999999"),
        (1999, 7, "PRC-1999-000007"),
    ],
)
def test_build_tracking_code_basic(year, seq, expected):
    assert build_tracking_code(year, seq) == expected


def test_build_tracking_code_zero_seq():
    # Behavior is defined: zero is allowed and zero-padded.
    assert build_tracking_code(2025, 0) == "PRC-2025-000000"


@freeze_time('2033-05-04')
def test_generate_tracking_code_uses_current_year():
    assert generate_tracking_code(15) == "PRC-2033-000015"


@pytest.mark.parametrize("bad_seq", [-1, -10])
def test_build_tracking_code_negative_seq(bad_seq):
    # Current implementation allows negatives; decide expected behavior.
    # For MVP we assert the raw formatting outcome for transparency.
    expected = f"PRC-2025--{abs(bad_seq):05d}" if bad_seq < 0 else ""
    assert build_tracking_code(2025, bad_seq) == expected
