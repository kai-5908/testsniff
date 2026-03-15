from __future__ import annotations

from typing import Protocol

from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding


class Rule(Protocol):
    rule_id: str
    default_severity: str
    default_confidence: str

    def analyze(self, module: ModuleContext) -> list[Finding]:
        """Analyze one parsed module and return zero or more findings."""

