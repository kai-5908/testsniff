from __future__ import annotations

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
