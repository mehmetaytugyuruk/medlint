"""Run-local identifiers for records and sensitive metadata values."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Iterable


def assign_record_aliases(count: int, *, prefix: str = "record") -> tuple[str, ...]:
    """Return deterministic opaque aliases for an already sorted catalog."""

    if count < 0:
        raise ValueError("count must not be negative")
    width = max(6, len(str(max(1, count))))
    return tuple(f"{prefix}-{index:0{width}d}" for index in range(1, count + 1))


class IdentifierTokenizer:
    """Create unlinkable, run-local equality tokens for sensitive values.

    The random key is never placed in an :class:`~medlint.evidence.AuditResult`.
    Tokens are used only as detector grouping keys and are never serialized.
    """

    __slots__ = ("_key",)

    def __init__(self, key: bytes | None = None) -> None:
        self._key = key if key is not None else secrets.token_bytes(32)
        if len(self._key) < 16:
            raise ValueError("identifier token key must contain at least 16 bytes")

    def token(self, domain: str, parts: Iterable[str]) -> str:
        message = "\x1f".join((domain, *parts)).encode("utf-8", errors="strict")
        return hmac.new(self._key, message, hashlib.sha256).hexdigest()
