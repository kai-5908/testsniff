from __future__ import annotations

from dataclasses import dataclass

from testsniff.config.types import Confidence, Severity
from testsniff.docs.rule_metadata import COMMENTS_ONLY_TEST
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks._comment_placeholder import is_comments_only_placeholder_test


@dataclass(slots=True)
class CommentsOnlyTestRule:
    rule_id: str = COMMENTS_ONLY_TEST.rule_id
    default_severity: Severity = COMMENTS_ONLY_TEST.default_severity
    default_confidence: Confidence = COMMENTS_ONLY_TEST.default_confidence

    def analyze(self, module: ModuleContext) -> list[Finding]:
        findings: list[Finding] = []
        for target in module.index.test_targets:
            function = target.node
            if not is_comments_only_placeholder_test(module, function):
                continue
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    headline=COMMENTS_ONLY_TEST.headline,
                    severity=self.default_severity,
                    confidence=self.default_confidence,
                    path=str(module.path),
                    line=function.lineno,
                    column=function.col_offset + 1,
                    why=COMMENTS_ONLY_TEST.why,
                    fix=COMMENTS_ONLY_TEST.fix,
                    example=COMMENTS_ONLY_TEST.example,
                    references=COMMENTS_ONLY_TEST.references,
                )
            )
        return findings
