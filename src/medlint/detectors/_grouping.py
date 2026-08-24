"""Internal helpers for safe, deterministic evidence components."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Callable, Iterable

from medlint.catalog import CatalogRecord
from medlint.evidence import EvidenceCategory, Finding


def component_id(rule_id: str, aliases: Iterable[str]) -> str:
    payload = "\x1f".join((rule_id, *sorted(aliases))).encode("utf-8")
    return f"component-{hashlib.sha256(payload).hexdigest()[:16]}"


def cross_split_findings(
    records: Iterable[CatalogRecord],
    *,
    key: Callable[[CatalogRecord], str | None],
    rule_id: str,
    rule_version: str,
    category: EvidenceCategory,
    strength: str,
    observed_fact: str,
    method: str,
    explanation: str,
    limitation: str,
    recommendation: str,
) -> tuple[Finding, ...]:
    groups: dict[str, list[CatalogRecord]] = defaultdict(list)
    for record in records:
        value = key(record)
        if value is not None:
            groups[value].append(record)

    findings: list[Finding] = []
    for members in groups.values():
        splits = tuple(sorted({member.split for member in members}))
        if len(splits) < 2:
            continue
        aliases = tuple(sorted(member.alias for member in members))
        findings.append(
            Finding(
                rule_id=rule_id,
                rule_version=rule_version,
                category=category,
                evidence_strength=strength,
                component_id=component_id(rule_id, aliases),
                splits=splits,
                record_aliases=aliases,
                observed_fact=observed_fact.format(
                    record_count=len(aliases), split_count=len(splits)
                ),
                method=method,
                explanation=explanation,
                limitation=limitation,
                recommendation=recommendation,
            )
        )
    findings.sort(
        key=lambda finding: (
            finding.rule_id,
            finding.splits,
            finding.record_aliases,
            finding.component_id,
        )
    )
    return tuple(findings)
