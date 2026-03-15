from __future__ import annotations

import json
from typing import TYPE_CHECKING

from testsniff.config.types import CONFIDENCE_ORDER, SEVERITY_ORDER, OutputFormat
from testsniff.reporting.exit_codes import FAILURE, FINDINGS, SUCCESS
from testsniff.reporting.finding import Finding, ParseFailure

if TYPE_CHECKING:
    from testsniff.services.scan import ScanResult


def render_result(result: ScanResult, output_format: OutputFormat) -> str:
    if output_format == "json":
        return _render_json(result)
    if output_format == "compact":
        return _render_compact(result)
    return _render_human(result)


def resolve_exit_code(findings: list[Finding], parse_failures: list[ParseFailure]) -> int:
    if parse_failures:
        return FAILURE
    if findings:
        return FINDINGS
    return SUCCESS


def _render_human(result: ScanResult) -> str:
    if not result.findings and not result.parse_failures:
        return "No findings.\n"

    lines: list[str] = []
    for finding in result.findings:
        headline = (
            f"{finding.severity}[{finding.rule_id}]"
            f"[confidence={finding.confidence}]: {finding.headline}"
        )
        lines.extend(
            [
                headline,
                f"  --> {finding.path}:{finding.line}:{finding.column}",
                f"  WHY: {finding.why}",
                f"  FIX: {finding.fix}",
                "  EXAMPLE:",
                "    # Bad:",
                *[f"    {line}" for line in finding.example.bad.splitlines() or [""]],
                "    # Good:",
                *[f"    {line}" for line in finding.example.good.splitlines() or [""]],
            ]
        )
        if finding.references:
            lines.append(f"  REFERENCES: {', '.join(finding.references)}")
        lines.append("")

    for failure in result.parse_failures:
        lines.append(f"parse_error: {failure.path}: {failure.message}")

    return "\n".join(lines).rstrip() + "\n"


def _render_compact(result: ScanResult) -> str:
    lines = [
        (
            f"{finding.path}:{finding.line}:{finding.column}: "
            f"{finding.severity}[{finding.confidence}] {finding.rule_id} {finding.headline}"
        )
        for finding in result.findings
    ]
    lines.extend(
        f"parse_error: {failure.path}: {failure.message}"
        for failure in result.parse_failures
    )
    if not lines:
        lines.append("No findings.")
    return "\n".join(lines) + "\n"


def _render_json(result: ScanResult) -> str:
    payload = {
        "tool": "testsniff",
        "version": result.version,
        "findings": [finding.to_json() for finding in result.findings],
        "parse_failures": [
            {
                "path": failure.path,
                "message": failure.message,
            }
            for failure in result.parse_failures
        ],
        "files_scanned": result.files_scanned,
        "files_skipped": result.files_skipped,
        "exit_code": result.exit_code,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda finding: (
            finding.path,
            finding.line,
            finding.column,
            -SEVERITY_ORDER[finding.severity],
            -CONFIDENCE_ORDER[finding.confidence],
            finding.rule_id,
        ),
    )
