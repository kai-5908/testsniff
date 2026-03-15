from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, cast

from testsniff.config.defaults import (
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_INCLUDE_PATTERNS,
    DEFAULT_MINIMUM_CONFIDENCE,
    DEFAULT_MINIMUM_SEVERITY,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_TARGET_PATHS,
)
from testsniff.config.types import (
    CONFIDENCE_VALUES,
    OUTPUT_FORMAT_VALUES,
    SEVERITY_VALUES,
    Confidence,
    ConfigOverrides,
    OutputFormat,
    ScanConfig,
    Severity,
)


def load_scan_config(cwd: Path, overrides: ConfigOverrides | None = None) -> ScanConfig:
    raw = _load_pyproject_config(cwd)
    overrides = overrides or ConfigOverrides()

    return ScanConfig(
        target_paths=_tuple_value(
            raw.get("target_paths"),
            DEFAULT_TARGET_PATHS,
            overrides.target_paths,
        ),
        include_patterns=_tuple_value(
            raw.get("include"), DEFAULT_INCLUDE_PATTERNS, overrides.include_patterns
        ),
        exclude_patterns=_tuple_value(
            raw.get("exclude"), DEFAULT_EXCLUDE_PATTERNS, overrides.exclude_patterns
        ),
        selected_rule_ids=_tuple_value(raw.get("select"), (), overrides.selected_rule_ids),
        ignored_rule_ids=_tuple_value(raw.get("ignore"), (), overrides.ignored_rule_ids),
        minimum_confidence=_confidence_value(
            raw.get("minimum_confidence"),
            DEFAULT_MINIMUM_CONFIDENCE,
            overrides.minimum_confidence,
        ),
        minimum_severity=_severity_value(
            raw.get("minimum_severity"),
            DEFAULT_MINIMUM_SEVERITY,
            overrides.minimum_severity,
        ),
        output_format=_output_format_value(
            raw.get("format"),
            DEFAULT_OUTPUT_FORMAT,
            overrides.output_format,
        ),
    )


def _load_pyproject_config(cwd: Path) -> dict[str, Any]:
    pyproject_path = cwd / "pyproject.toml"
    if not pyproject_path.exists():
        return {}

    data = tomllib.loads(pyproject_path.read_text())
    tool_section = data.get("tool", {})
    testsniff_section = tool_section.get("testsniff", {})
    if not isinstance(testsniff_section, dict):
        raise ValueError("[tool.testsniff] must be a TOML table.")
    return testsniff_section


def _tuple_value(
    raw_value: Any,
    default: tuple[str, ...],
    override: tuple[str, ...] | None,
) -> tuple[str, ...]:
    if override is not None:
        return override
    if raw_value is None:
        return default
    if not isinstance(raw_value, list) or not all(isinstance(item, str) for item in raw_value):
        raise ValueError("Expected a list of strings in testsniff config.")
    return tuple(raw_value)


def _scalar_value(raw_value: Any, default: str, override: str | None) -> str:
    if override is not None:
        return override
    if raw_value is None:
        return default
    if not isinstance(raw_value, str):
        raise ValueError("Expected a string value in testsniff config.")
    return raw_value


def _confidence_value(raw_value: Any, default: str, override: str | None) -> Confidence:
    return _literal_value(raw_value, default, override, CONFIDENCE_VALUES, "confidence")


def _severity_value(raw_value: Any, default: str, override: str | None) -> Severity:
    return _literal_value(raw_value, default, override, SEVERITY_VALUES, "severity")


def _output_format_value(raw_value: Any, default: str, override: str | None) -> OutputFormat:
    return _literal_value(raw_value, default, override, OUTPUT_FORMAT_VALUES, "output format")


def _literal_value[TString: str](
    raw_value: Any,
    default: str,
    override: str | None,
    allowed: tuple[TString, ...],
    label: str,
) -> TString:
    value = _scalar_value(raw_value, default, override)
    if value not in allowed:
        allowed_values = ", ".join(allowed)
        raise ValueError(f"Expected {label} to be one of: {allowed_values}")
    return cast(TString, value)
