from __future__ import annotations

import ast
from dataclasses import dataclass

from testsniff.config.types import Confidence, Severity
from testsniff.docs.rule_metadata import EMPTY_TEST
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding


@dataclass(slots=True)
class EmptyTestRule:
    rule_id: str = EMPTY_TEST.rule_id
    default_severity: Severity = EMPTY_TEST.default_severity
    default_confidence: Confidence = EMPTY_TEST.default_confidence

    def analyze(self, module: ModuleContext) -> list[Finding]:
        findings: list[Finding] = []
        for target in module.index.test_targets:
            function = target.node
            if not _is_effectively_empty(function):
                continue
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    headline=EMPTY_TEST.headline,
                    severity=self.default_severity,
                    confidence=self.default_confidence,
                    path=str(module.path),
                    line=function.lineno,
                    column=function.col_offset + 1,
                    why=EMPTY_TEST.why,
                    fix=EMPTY_TEST.fix,
                    example=EMPTY_TEST.example,
                    references=EMPTY_TEST.references,
                )
            )
        return findings


def _is_effectively_empty(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = list(function.body)
    if _has_leading_docstring(body):
        body = body[1:]
    if not body:
        return True
    return len(body) == 1 and isinstance(body[0], ast.Pass)


def _has_leading_docstring(body: list[ast.stmt]) -> bool:
    if not body:
        return False
    first = body[0]
    if not isinstance(first, ast.Expr):
        return False
    return isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)
