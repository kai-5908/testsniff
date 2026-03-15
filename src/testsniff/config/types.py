from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Severity = Literal["error", "warning", "info"]
Confidence = Literal["high", "medium"]
OutputFormat = Literal["human", "compact", "json"]
SEVERITY_VALUES: tuple[Severity, ...] = ("error", "warning", "info")
CONFIDENCE_VALUES: tuple[Confidence, ...] = ("high", "medium")
OUTPUT_FORMAT_VALUES: tuple[OutputFormat, ...] = ("human", "compact", "json")

SEVERITY_ORDER: dict[Severity, int] = {
    "info": 0,
    "warning": 1,
    "error": 2,
}

CONFIDENCE_ORDER: dict[Confidence, int] = {
    "medium": 0,
    "high": 1,
}


@dataclass(slots=True)
class ConfigOverrides:
    output_format: OutputFormat | None = None
    selected_rule_ids: tuple[str, ...] | None = None
    ignored_rule_ids: tuple[str, ...] | None = None
    minimum_confidence: Confidence | None = None
    minimum_severity: Severity | None = None
    target_paths: tuple[str, ...] | None = None
    include_patterns: tuple[str, ...] | None = None
    exclude_patterns: tuple[str, ...] | None = None


@dataclass(slots=True)
class ScanConfig:
    target_paths: tuple[str, ...]
    include_patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...]
    selected_rule_ids: tuple[str, ...]
    ignored_rule_ids: tuple[str, ...]
    minimum_confidence: Confidence
    minimum_severity: Severity
    output_format: OutputFormat


@dataclass(slots=True)
class ResolvedTarget:
    path: Path
    root: Path
