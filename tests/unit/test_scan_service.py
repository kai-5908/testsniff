from __future__ import annotations

from pathlib import Path

from testsniff.config.types import ConfigOverrides
from testsniff.services import scan as scan_service


class _RecursingRule:
    rule_id = "TS999"
    default_severity = "error"
    default_confidence = "high"

    def analyze(self, module) -> list[object]:
        raise RecursionError("maximum recursion depth exceeded")


def test_run_scan_converts_rule_recursion_error_into_parse_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text("def test_example():\n    assert True\n")

    monkeypatch.setattr(scan_service, "get_enabled_rules", lambda config: (_RecursingRule(),))

    result = scan_service.run_scan(
        scan_service.ScanRequest(
            paths=(tests_dir,),
            paths_explicit=True,
            overrides=ConfigOverrides(),
        ),
        cwd=tmp_path,
    )

    assert result.findings == []
    assert len(result.parse_failures) == 1
    assert result.parse_failures[0].path.endswith("test_example.py")
    assert "TS999" in result.parse_failures[0].message
    assert result.exit_code == 2
