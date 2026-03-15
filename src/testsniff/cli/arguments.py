from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from testsniff.config.types import Confidence, ConfigOverrides, OutputFormat, Severity


@dataclass(slots=True)
class ScanCommandArgs:
    paths: tuple[Path, ...]
    output_format: OutputFormat | None = None
    select: tuple[str, ...] | None = None
    ignore: tuple[str, ...] | None = None
    minimum_confidence: Confidence | None = None
    minimum_severity: Severity | None = None

    def to_overrides(self) -> ConfigOverrides:
        return ConfigOverrides(
            output_format=self.output_format,
            selected_rule_ids=self.select,
            ignored_rule_ids=self.ignore,
            minimum_confidence=self.minimum_confidence,
            minimum_severity=self.minimum_severity,
        )

