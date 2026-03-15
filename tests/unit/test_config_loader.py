from __future__ import annotations

from pathlib import Path

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

