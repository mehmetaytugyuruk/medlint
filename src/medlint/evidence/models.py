"""Small immutable contracts shared by detectors, policy, and reporters."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from medlint.catalog import CatalogCoverage


class EvidenceCategory(str, Enum):
    AUTHORITATIVE_GROUP_RELATIONSHIP = "authoritative_group_relationship"
    ACQUISITION_IDENTIFIER_RELATIONSHIP = "acquisition_identifier_relationship"
    EXACT_FILE_CONTENT_RELATIONSHIP = "exact_file_content_relationship"


@dataclass(frozen=True, slots=True)
class Finding:
    """One factual, privacy-safe cross-split relationship."""

    rule_id: str
    rule_version: str
    category: EvidenceCategory
    evidence_strength: str
    component_id: str
    splits: tuple[str, ...]
    record_aliases: tuple[str, ...]
    observed_fact: str
    method: str
    explanation: str
    limitation: str
    recommendation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "category": self.category.value,
            "evidence_strength": self.evidence_strength,
            "component_id": self.component_id,
            "splits": list(self.splits),
            "record_aliases": list(self.record_aliases),
            "observed_fact": self.observed_fact,
            "method": self.method,
            "explanation": self.explanation,
            "limitation": self.limitation,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True, slots=True)
class DetectorCoverage:
    detector_id: str
    eligible_records: int
    evaluated_records: int
    unavailable_records: int
    eligible_splits: tuple[str, ...]
    evaluated_splits: tuple[str, ...]
    reason_counts: tuple[tuple[str, int], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "detector_id": self.detector_id,
            "eligible_records": self.eligible_records,
            "evaluated_records": self.evaluated_records,
            "unavailable_records": self.unavailable_records,
            "eligible_splits": list(self.eligible_splits),
            "evaluated_splits": list(self.evaluated_splits),
            "reason_counts": [
                {"reason": reason, "count": count}
                for reason, count in self.reason_counts
            ],
        }


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    record_alias: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.record_alias is not None:
            payload["record_alias"] = self.record_alias
        return payload


@dataclass(frozen=True, slots=True)
class DetectorResult:
    detector_id: str
    findings: tuple[Finding, ...]
    coverage: DetectorCoverage
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        if self.detector_id != self.coverage.detector_id:
            raise ValueError("detector result and coverage identifiers must match")


@dataclass(frozen=True, slots=True)
class PolicyOutcome:
    """Policy interpretation kept separate from the factual findings."""

    policy_id: str
    policy_version: str
    finding_status: str
    coverage_status: str
    audit_state: str
    exit_code: int
    summary: str

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "finding_status": self.finding_status,
            "coverage_status": self.coverage_status,
            "audit_state": self.audit_state,
            "exit_code": self.exit_code,
            "summary": self.summary,
        }


@dataclass(frozen=True, slots=True)
class RecordReference:
    """Private result context used only for explicit path-inclusive output."""

    alias: str
    path: Path


@dataclass(frozen=True, slots=True)
class AuditResult:
    schema_version: str
    tool_version: str
    config_digest: str
    splits: tuple[str, ...]
    findings: tuple[Finding, ...]
    catalog_coverage: CatalogCoverage
    detector_coverage: tuple[DetectorCoverage, ...]
    diagnostics: tuple[Diagnostic, ...]
    policy_outcome: PolicyOutcome
    provenance: tuple[tuple[str, str], ...]
    _record_references: tuple[RecordReference, ...] = field(default=(), repr=False)
    _protected_files: tuple[Path, ...] = field(default=(), repr=False)
    _protected_roots: tuple[Path, ...] = field(default=(), repr=False)

    @property
    def finding_status(self) -> str:
        return self.policy_outcome.finding_status

    @property
    def coverage_status(self) -> str:
        return self.policy_outcome.coverage_status

    @property
    def audit_state(self) -> str:
        return self.policy_outcome.audit_state

    @property
    def exit_code(self) -> int:
        return self.policy_outcome.exit_code

    def to_dict(self, *, include_paths: bool = False) -> dict[str, object]:
        """Return the canonical report representation.

        Raw DICOM identifiers are never retained by ``AuditResult``.  Local
        paths are excluded unless a caller deliberately opts in here.
        """

        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "tool_version": self.tool_version,
            "config_digest": self.config_digest,
            "splits": list(self.splits),
            "finding_status": self.finding_status,
            "coverage_status": self.coverage_status,
            "audit_state": self.audit_state,
            "findings": [finding.to_dict() for finding in self.findings],
            "coverage": {
                "catalog": self.catalog_coverage.to_dict(),
                "detectors": [item.to_dict() for item in self.detector_coverage],
            },
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "policy": self.policy_outcome.to_dict(),
            "provenance": {name: version for name, version in self.provenance},
        }
        if include_paths:
            payload["record_paths"] = [
                {"record_alias": item.alias, "path": str(item.path)}
                for item in self._record_references
            ]
        return payload

    def to_json(self, *, include_paths: bool = False, indent: int | None = 2) -> str:
        return json.dumps(
            self.to_dict(include_paths=include_paths),
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )
