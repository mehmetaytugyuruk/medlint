from __future__ import annotations

import pytest

from medlint.privacy.aliases import IdentifierTokenizer, assign_record_aliases


def test_record_aliases_are_opaque_and_deterministic() -> None:
    assert assign_record_aliases(3) == (
        "record-000001",
        "record-000002",
        "record-000003",
    )


def test_identifier_tokens_support_equality_without_exposing_value() -> None:
    tokenizer = IdentifierTokenizer(key=b"a" * 32)
    first = tokenizer.token("patient", ("site-a", "PATIENT-001"))
    second = tokenizer.token("patient", ("site-a", "PATIENT-001"))
    different = tokenizer.token("patient", ("site-a", "PATIENT-002"))

    assert first == second
    assert first != different
    assert "PATIENT" not in first


def test_privacy_helpers_reject_unsafe_arguments() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        assign_record_aliases(-1)

    with pytest.raises(ValueError, match="at least 16 bytes"):
        IdentifierTokenizer(key=b"short")
