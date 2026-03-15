from __future__ import annotations

from testsniff.reporting.finding import Finding


def format_compact_header(finding: Finding) -> str:
    return (
        f"{finding.path}:{finding.line}:{finding.column}: "
        f"{finding.severity}[{finding.confidence}] {finding.rule_id} {finding.headline}"
    )

