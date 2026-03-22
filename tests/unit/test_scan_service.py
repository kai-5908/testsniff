from __future__ import annotations

from pathlib import Path

import pytest

from testsniff.config.types import ConfigOverrides, ScanConfig
from testsniff.reporting.finding import ExampleSnippet, Finding
from testsniff.rules.registry import get_enabled_rules
from testsniff.services import scan
from testsniff.services.scan import ScanRequest, run_scan


def test_run_scan_collects_parse_failures_and_returns_failure_exit_code(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    bad_file = tests_dir / "test_bad.py"
    bad_file.write_text("def test_example(:\n")

    result = run_scan(
        ScanRequest(paths=(tests_dir,), paths_explicit=True, overrides=ConfigOverrides()),
        cwd=tmp_path,
    )

    assert result.exit_code == 2
    assert result.files_scanned == 0
    assert [failure.path for failure in result.parse_failures] == [str(bad_file)]


def test_resolve_target_files_raises_for_missing_explicit_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Target path does not exist"):
        scan.resolve_target_files(
            cwd=tmp_path,
            request_paths=(tmp_path / "missing",),
            paths_explicit=True,
            config=_scan_config(),
        )


def test_resolve_target_files_skips_missing_implicit_paths(tmp_path: Path) -> None:
    resolved = scan.resolve_target_files(
        cwd=tmp_path,
        request_paths=(tmp_path / "missing",),
        paths_explicit=False,
        config=_scan_config(),
    )

    assert resolved == []


def test_resolve_target_files_handles_matching_and_nonmatching_explicit_files(
    tmp_path: Path,
) -> None:
    matching = tmp_path / "tests" / "test_ok.py"
    matching.parent.mkdir()
    matching.write_text("def test_ok():\n    assert True\n")
    helper = tmp_path / "tests" / "helper.py"
    helper.write_text("def helper():\n    pass\n")

    resolved = scan.resolve_target_files(
        cwd=tmp_path,
        request_paths=(matching, helper),
        paths_explicit=True,
        config=_scan_config(),
    )

    assert resolved == [matching]


def test_matches_target_uses_absolute_path_when_file_is_outside_cwd(tmp_path: Path) -> None:
    external = Path("/tmp/test_external.py")
    config = _scan_config(include_patterns=("test_*.py",), exclude_patterns=())

    assert scan._matches_target(external, tmp_path, config) is True


def test_matches_target_respects_exclude_patterns_for_relative_paths(tmp_path: Path) -> None:
    config = _scan_config(
        include_patterns=("test_*.py",),
        exclude_patterns=("tests/generated/**",),
    )

    assert scan._matches_target(Path("tests/generated/test_hidden.py"), tmp_path, config) is False


def test_with_request_paths_only_overrides_target_paths_for_explicit_requests() -> None:
    request = ScanRequest(
        paths=(Path("tests"),),
        paths_explicit=True,
        overrides=ConfigOverrides(output_format="json", minimum_severity="warning"),
    )

    explicit = scan._with_request_paths(request)
    implicit = scan._with_request_paths(
        ScanRequest(paths=(), paths_explicit=False, overrides=request.overrides)
    )

    assert explicit.target_paths == ("tests",)
    assert explicit.output_format == "json"
    assert explicit.minimum_severity == "warning"
    assert implicit is request.overrides


def test_prefer_specific_rules_suppresses_empty_test_when_comment_rule_matches_same_location(
) -> None:
    shared = dict(
        headline="Headline",
        severity="error",
        confidence="high",
        path="tests/test_example.py",
        line=1,
        column=1,
        why="Why",
        fix="Fix",
        example=ExampleSnippet(bad="pass", good="assert True"),
        references=(),
    )
    findings = [
        Finding(rule_id="TS001", **shared),
        Finding(rule_id="TS002", **shared),
        Finding(
            rule_id="TS001",
            line=2,
            column=1,
            **{k: v for k, v in shared.items() if k not in {"line", "column"}},
        ),
    ]

    filtered = scan._prefer_specific_rules(findings)

    assert [(finding.rule_id, finding.line) for finding in filtered] == [("TS002", 1), ("TS001", 2)]


def test_get_enabled_rules_rejects_unknown_rule_ids() -> None:
    config = _scan_config(selected_rule_ids=("TS999",))

    with pytest.raises(ValueError, match="Unknown rule ID\\(s\\): TS999"):
        get_enabled_rules(config)


def _scan_config(
    *,
    include_patterns: tuple[str, ...] = ("test_*.py",),
    exclude_patterns: tuple[str, ...] = (),
    selected_rule_ids: tuple[str, ...] = (),
) -> ScanConfig:
    return ScanConfig(
        target_paths=("tests",),
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        selected_rule_ids=selected_rule_ids,
        ignored_rule_ids=(),
        minimum_confidence="medium",
        minimum_severity="info",
        output_format="human",
    )
