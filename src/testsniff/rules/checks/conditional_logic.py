from __future__ import annotations

import ast
from dataclasses import dataclass

from testsniff.config.types import Confidence, Severity
from testsniff.docs.rule_metadata import CONDITIONAL_LOGIC
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks._function_body import is_effectively_empty, iter_executable_body


@dataclass(slots=True)
class ConditionalLogicRule:
    rule_id: str = CONDITIONAL_LOGIC.rule_id
    default_severity: Severity = CONDITIONAL_LOGIC.default_severity
    default_confidence: Confidence = CONDITIONAL_LOGIC.default_confidence

    def analyze(self, module: ModuleContext) -> list[Finding]:
        findings: list[Finding] = []

        for target in module.index.test_targets:
            function = target.node
            if is_effectively_empty(function):
                continue
            if not _contains_conditional_logic(iter_executable_body(function)):
                continue

            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    headline=CONDITIONAL_LOGIC.headline,
                    severity=self.default_severity,
                    confidence=self.default_confidence,
                    path=str(module.path),
                    line=function.lineno,
                    column=function.col_offset + 1,
                    why=CONDITIONAL_LOGIC.why,
                    fix=CONDITIONAL_LOGIC.fix,
                    example=CONDITIONAL_LOGIC.example,
                    references=CONDITIONAL_LOGIC.references,
                )
            )

        return findings


def _contains_conditional_logic(statements: tuple[ast.stmt, ...] | list[ast.stmt]) -> bool:
    for statement in statements:
        if _statement_contains_conditional_logic(statement):
            return True
    return False


def _statement_contains_conditional_logic(statement: ast.stmt) -> bool:
    if isinstance(statement, ast.If):
        return True

    if isinstance(statement, ast.With | ast.AsyncWith):
        return _contains_conditional_logic(statement.body)

    if isinstance(statement, ast.For | ast.AsyncFor | ast.While):
        return _contains_conditional_logic(statement.body) or _contains_conditional_logic(
            statement.orelse
        )

    if isinstance(statement, ast.Try | ast.TryStar):
        return _try_statement_contains_conditional_logic(statement)

    if isinstance(statement, ast.Match):
        for case in statement.cases:
            if _contains_conditional_logic(case.body):
                return True
        return False

    return False


def _try_statement_contains_conditional_logic(statement: ast.Try | ast.TryStar) -> bool:
    if _contains_conditional_logic(statement.body):
        return True
    for handler in statement.handlers:
        if _contains_conditional_logic(handler.body):
            return True
    return _contains_conditional_logic(statement.orelse) or _contains_conditional_logic(
        statement.finalbody
    )
