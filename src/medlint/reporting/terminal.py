"""Small, privacy-safe terminal rendering for audit results."""

from __future__ import annotations

from collections import Counter

from medlint.evidence import AuditResult


def terminal_summary(result: AuditResult) -> str:
    """Render a concise summary without raw paths or DICOM identifiers."""

    coverage = result.catalog_coverage
    lines = [
        "medlint split-integrity audit",
        f"Audit state: {result.audit_state}",
        f"Finding status: {result.finding_status}",
        f"Coverage status: {result.coverage_status}",
        "",
        "Coverage",
        f"  Declared splits: {coverage.declared_split_count}",
        f"  Evaluable splits: {coverage.evaluable_split_count}",
        f"  Discovered: {coverage.discovered}",
        f"  Supported: {coverage.supported}",
        f"  Exact-file fingerprints: {coverage.hashed}",
        f"  DICOM metadata parsed: {coverage.dicom_parsed}",
        f"  Outside primary profile: {coverage.outside_primary_profile}",
        f"  Unsupported: {coverage.unsupported}",
        f"  Unreadable: {coverage.unreadable}",
        "",
        f"Findings: {len(result.findings)}",
    ]

    for finding in result.findings:
        aliases = ", ".join(finding.record_aliases)
        splits = ", ".join(finding.splits)
        lines.extend(
            [
                f"  [{finding.rule_id}] {finding.observed_fact}",
                f"    Splits: {splits}",
                f"    Records: {aliases}",
                f"    Review: {finding.recommendation}",
            ]
        )

    if result.diagnostics:
        lines.extend(["", f"Diagnostics: {len(result.diagnostics)}"])
        groups = Counter(
            (diagnostic.severity, diagnostic.code, diagnostic.message)
            for diagnostic in result.diagnostics
        )
        for (severity, code, message), count in sorted(groups.items()):
            lines.append(f"  [{severity}:{code}] {count} occurrence(s): {message}")

    lines.extend(
        [
            "",
            result.policy_outcome.summary,
            (
                "Scope note: this is an evidence-based smoke test, not a "
                "leakage-free certification or patient-identity claim."
            ),
        ]
    )
    return "\n".join(lines)
