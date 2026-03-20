from __future__ import annotations

from typing import cast

from testsniff.config.types import ScanConfig
from testsniff.rules.base import Rule
from testsniff.rules.checks.comments_only_test import CommentsOnlyTestRule
from testsniff.rules.checks.empty_test import EmptyTestRule
from testsniff.rules.checks.missing_assertion import MissingAssertionRule

AVAILABLE_RULES: tuple[Rule, ...] = (
    cast(Rule, EmptyTestRule()),
    cast(Rule, CommentsOnlyTestRule()),
    cast(Rule, MissingAssertionRule()),
)


def get_enabled_rules(config: ScanConfig) -> tuple[Rule, ...]:
    rules_by_id = {rule.rule_id: rule for rule in AVAILABLE_RULES}

    if config.selected_rule_ids:
        unknown = sorted(set(config.selected_rule_ids) - set(rules_by_id))
        if unknown:
            joined = ", ".join(unknown)
            raise ValueError(f"Unknown rule ID(s): {joined}")
        selected = [rules_by_id[rule_id] for rule_id in config.selected_rule_ids]
    else:
        selected = list(AVAILABLE_RULES)

    ignored = set(config.ignored_rule_ids)
    return tuple(rule for rule in selected if rule.rule_id not in ignored)
