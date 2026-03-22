from __future__ import annotations

from pathlib import Path

import pytest

from testsniff.config.loader import load_scan_config
from testsniff.config.types import ConfigOverrides


def test_load_scan_config_merges_pyproject_and_overrides(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.testsniff]
format = "compact"
minimum_confidence = "high"
select = ["TS001"]
target_paths = ["custom-tests"]
""".strip()
    )

    config = load_scan_config(
        tmp_path,
        ConfigOverrides(output_format="json", ignored_rule_ids=("TS999",)),
    )

    assert config.output_format == "json"
    assert config.minimum_confidence == "high"
    assert config.selected_rule_ids == ("TS001",)
    assert config.ignored_rule_ids == ("TS999",)
    assert config.target_paths == ("custom-tests",)


def test_load_scan_config_uses_defaults_without_pyproject() -> None:
    config = load_scan_config(Path("/tmp/does-not-need-to-exist"))

    assert config.output_format == "human"
    assert config.minimum_confidence == "medium"
    assert config.minimum_severity == "info"
    assert config.include_patterns == ("test_*.py", "*_test.py")


def test_load_scan_config_rejects_non_table_tool_testsniff_section(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('tool = { testsniff = "invalid" }\n')

    with pytest.raises(ValueError, match=r"\[tool\.testsniff\] must be a TOML table\."):
        load_scan_config(tmp_path)


def test_load_scan_config_rejects_non_string_list_values(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.testsniff]
include = ["test_*.py", 1]
""".strip()
    )

    with pytest.raises(ValueError, match="Expected a list of strings"):
        load_scan_config(tmp_path)


def test_load_scan_config_rejects_non_string_scalar_values(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.testsniff]
minimum_severity = 1
""".strip()
    )

    with pytest.raises(ValueError, match="Expected a string value"):
        load_scan_config(tmp_path)


def test_load_scan_config_rejects_unknown_literal_values(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.testsniff]
format = "wide"
""".strip()
    )

    with pytest.raises(ValueError, match="Expected output format to be one of"):
        load_scan_config(tmp_path)
