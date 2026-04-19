from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from testsniff.cli.main import app

runner = CliRunner()


def test_cli_scan_reports_empty_test_rule(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text("def test_example():\n    pass\n")

    result = runner.invoke(app, ["scan", str(tests_dir)], catch_exceptions=False)

    assert result.exit_code == 1
    assert "error[TS001][confidence=high]: Test body is empty" in result.stdout
    assert "WHY:" in result.stdout
    assert "FIX:" in result.stdout


def test_cli_scan_reports_empty_pytest_class_method(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_pytest_class_example.py").write_text(
        "class TestExample:\n"
        "    def test_example(self):\n"
        "        pass\n"
    )

    result = runner.invoke(app, ["scan", str(tests_dir)], catch_exceptions=False)

    assert result.exit_code == 1
    assert "error[TS001][confidence=high]: Test body is empty" in result.stdout


def test_cli_scan_reports_empty_unittest_method(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_unittest_example.py").write_text(
        "import unittest\n\n"
        "class TestExample(unittest.TestCase):\n"
        "    def test_example(self):\n"
        "        pass\n"
    )

    result = runner.invoke(app, ["scan", str(tests_dir)], catch_exceptions=False)

    assert result.exit_code == 1
    assert "error[TS001][confidence=high]: Test body is empty" in result.stdout


def test_cli_scan_reports_comments_only_test_rule(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_comments_only.py").write_text(
        "def test_example():\n"
        "    # TODO: add an assertion.\n"
        '    """Document the missing verification."""\n'
        "    # Placeholder until the assertion is added.\n"
    )

    result = runner.invoke(app, ["scan", str(tests_dir)], catch_exceptions=False)

    assert result.exit_code == 1
    assert "error[TS002][confidence=high]: Test contains only placeholder comments" in result.stdout
    assert "error[TS001][confidence=high]" not in result.stdout


def test_cli_scan_select_ts001_keeps_empty_test_contract_for_placeholders(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_comments_only.py").write_text(
        "def test_example():\n"
        "    # TODO: add an assertion.\n"
        '    """Document the missing verification."""\n'
        "    # Placeholder until the assertion is added.\n"
    )

    result = runner.invoke(
        app,
        ["scan", "--select", "TS001", str(tests_dir)],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "error[TS001][confidence=high]: Test body is empty" in result.stdout


def test_cli_scan_ignore_ts002_keeps_empty_test_contract_for_placeholders(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_comments_only.py").write_text(
        "def test_example():\n"
        "    # TODO: add an assertion.\n"
        '    """Document the missing verification."""\n'
        "    # Placeholder until the assertion is added.\n"
    )

    result = runner.invoke(
        app,
        ["scan", "--ignore", "TS002", str(tests_dir)],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "error[TS001][confidence=high]: Test body is empty" in result.stdout


def test_cli_scan_json_includes_ts002_metadata(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_comments_only.py").write_text(
        "def test_example():\n"
        '    """Document the missing verification."""\n'
        "    # Placeholder until the assertion is added.\n"
    )

    result = runner.invoke(
        app,
        ["scan", "--format", "json", str(tests_dir)],
        catch_exceptions=False,
    )

    payload = json.loads(result.stdout)

    assert result.exit_code == 1
    assert len(payload["findings"]) == 1
    assert payload["findings"][0]["rule_id"] == "TS002"
    assert payload["findings"][0]["headline"] == "Test contains only placeholder comments"
    assert "Replace placeholder comments" in payload["findings"][0]["fix"]


def test_cli_scan_reports_missing_assertion_rule(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "def test_example(client):\n"
        '    client.get("/users")\n'
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS003"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "error[TS003][confidence=high]: Test has no recognized assertion" in result.stdout


def test_cli_scan_renders_missing_assertion_rule_in_json(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "def test_example(client):\n"
        '    client.get("/users")\n'
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS003", "--format", "json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["findings"][0]["rule_id"] == "TS003"
    assert payload["findings"][0]["headline"] == "Test has no recognized assertion"


def test_cli_scan_reports_disabled_ignored_rule(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "import pytest\n\n"
        '@pytest.mark.skip(reason="temporarily disabled")\n'
        "def test_example():\n"
        "    assert True\n"
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS004"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "warning[TS004][confidence=high]: Test is disabled or ignored" in result.stdout


def test_cli_scan_renders_disabled_ignored_rule_in_json(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "import pytest\n\n"
        '@pytest.mark.skip(reason="temporarily disabled")\n'
        "class TestExample:\n"
        "    def test_one(self):\n"
        "        assert True\n\n"
        "    def test_two(self):\n"
        "        assert True\n"
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS004", "--format", "json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert [finding["rule_id"] for finding in payload["findings"]] == ["TS004", "TS004"]
    assert [finding["location"]["line"] for finding in payload["findings"]] == [5, 8]
    assert all(
        finding["headline"] == "Test is disabled or ignored"
        for finding in payload["findings"]
    )


def test_cli_scan_reports_duplicate_assert_rule(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "def test_example(response):\n"
        "    assert response.status_code == 201\n"
        "    assert response.status_code == 201\n"
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS005"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "error[TS005][confidence=high]: Test contains duplicated assertion" in result.stdout


def test_cli_scan_renders_duplicate_assert_rule_in_json(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "def test_example(response):\n"
        "    assert response.status_code == 201\n"
        "    assert response.status_code == 201\n"
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS005", "--format", "json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["findings"][0]["rule_id"] == "TS005"
    assert payload["findings"][0]["headline"] == "Test contains duplicated assertion"


def test_cli_scan_reports_magic_number_test_rule(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "def test_example(value):\n"
        "    assert value == 200\n"
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS006"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert (
        "warning[TS006][confidence=high]: "
        "Test uses unexplained magic number in expectation"
    ) in result.stdout
    assert "test_example.py:2:21" in result.stdout


def test_cli_scan_renders_magic_number_test_rule_in_json(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "def test_example(value):\n"
        "    assert value == 200\n"
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS006", "--format", "json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["findings"][0]["rule_id"] == "TS006"
    assert payload["findings"][0]["headline"] == "Test uses unexplained magic number in expectation"
    assert payload["findings"][0]["severity"] == "warning"
    assert payload["findings"][0]["confidence"] == "high"
    assert payload["findings"][0]["location"]["line"] == 2
    assert payload["findings"][0]["location"]["column"] == 21


def test_cli_scan_reports_conditional_logic_rule(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "def test_example(value):\n"
        "    if value:\n"
        "        assert value\n"
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS007"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "warning[TS007][confidence=high]: Test contains conditional logic" in result.stdout


def test_cli_scan_renders_conditional_logic_rule_in_json(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "def test_example(value):\n"
        "    if value:\n"
        "        assert value\n"
    )

    result = runner.invoke(
        app,
        ["scan", str(tests_dir), "--select", "TS007", "--format", "json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["findings"][0]["rule_id"] == "TS007"
    assert payload["findings"][0]["headline"] == "Test contains conditional logic"
    assert payload["findings"][0]["severity"] == "warning"
