from __future__ import annotations

from dataclasses import asdict, dataclass

from testsniff.config.types import Confidence, Severity


@dataclass(slots=True)
class ExampleSnippet:
    bad: str
    good: str


@dataclass(slots=True)
class Finding:
    rule_id: str
    headline: str
    severity: Severity
    confidence: Confidence
    path: str
    line: int
    column: int
    why: str
    fix: str
    example: ExampleSnippet
    references: tuple[str, ...]
    engine: str = "static"

    def to_json(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "headline": self.headline,
            "severity": self.severity,
            "confidence": self.confidence,
            "engine": self.engine,
            "location": {
                "path": self.path,
                "line": self.line,
                "column": self.column,
            },
            "why": self.why,
            "fix": self.fix,
            "example": asdict(self.example),
            "references": list(self.references),
        }


@dataclass(slots=True)
class ParseFailure:
    path: str
    message: str

