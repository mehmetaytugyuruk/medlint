"""The conservative v0.1 split-integrity policy."""

from __future__ import annotations

from typing import Protocol

from medlint.catalog import CatalogCoverage
from medlint.evidence import DetectorCoverage, Finding, PolicyOutcome


class AuditPolicy(Protocol):
    policy_id: str
    policy_version: str

    def evaluate(
        self,
        findings: tuple[Finding, ...],
        coverage: CatalogCoverage,
        detector_coverage: tuple[DetectorCoverage, ...],
        *,
        operational_error: bool = False,
    ) -> PolicyOutcome:
        """Interpret evidence without altering it."""


class ConservativeDefaultPolicy:
    """Report any finding as a reviewable potential contamination risk."""

    policy_id = "medlint.conservative-split-integrity"
    policy_version = "1"

    def evaluate(
        self,
        findings: tuple[Finding, ...],
        coverage: CatalogCoverage,
        detector_coverage: tuple[DetectorCoverage, ...],
        *,
        operational_error: bool = False,
    ) -> PolicyOutcome:
        finding_status = "potential_risk_detected" if findings else "no_findings"

        if operational_error:
            coverage_status = "operational_error"
            audit_state = "operational_error"
            exit_code = 2
            summary = (
                "The audit could not be completed because an operational error "
                "occurred."
            )
        else:
            has_cross_split_evidence_scope = any(
                len(item.evaluated_splits) >= 2 for item in detector_coverage
            )
            if (
                coverage.discovered == 0
                or coverage.declared_split_count < 2
                or not has_cross_split_evidence_scope
            ):
                coverage_status = "inconclusive"
            elif (
                coverage.populated_split_count < coverage.declared_split_count
                or coverage.unsupported > 0
                or coverage.unreadable > 0
                or coverage.outside_primary_profile > 0
                or any(item.unavailable_records > 0 for item in detector_coverage)
            ):
                coverage_status = "partial"
            else:
                coverage_status = "complete"

            if coverage_status == "inconclusive":
                audit_state = "inconclusive"
            elif coverage_status == "partial":
                audit_state = "partial"
            elif findings:
                audit_state = "complete_with_findings"
            else:
                audit_state = "complete_no_findings"

            # CI precedence: operational error (handled above), finding, partial
            # or inconclusive coverage, then a complete no-finding result.
            if findings:
                exit_code = 1
                if coverage_status == "complete":
                    summary = (
                        "Potential contamination risk detected; review the factual "
                        "evidence before model training."
                    )
                else:
                    summary = (
                        "Potential contamination risk detected, and audit coverage "
                        f"was {coverage_status}; review both before model training."
                    )
            elif coverage_status in {"partial", "inconclusive"}:
                exit_code = 3
                summary = (
                    "No configured finding was detected, but the audit coverage was "
                    f"{coverage_status}."
                )
            else:
                exit_code = 0
                summary = (
                    "No configured finding was detected within the checks and "
                    "coverage reported by this audit."
                )

        return PolicyOutcome(
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            finding_status=finding_status,
            coverage_status=coverage_status,
            audit_state=audit_state,
            exit_code=exit_code,
            summary=summary,
        )
