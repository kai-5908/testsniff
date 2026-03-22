from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


def test_pre_push_guides_meaningful_tests_when_coverage_gate_fails(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    uv_script = fake_bin / "uv"
    uv_script.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [ "$1" != "run" ]; then
  echo "unexpected invocation: $*" >&2
  exit 1
fi
shift
if [ "$1" = "ruff" ] || [ "$1" = "ty" ]; then
  exit 0
fi
if [ "$1" = "pytest" ]; then
  echo "ERROR: Coverage failure: total of 85 is less than fail-under=100" >&2
  echo "FAIL Required test coverage of 100% not reached. Total coverage: 84.52%" >&2
  exit 1
fi
echo "unexpected invocation: $*" >&2
exit 1
""",
        encoding="utf-8",
    )
    uv_script.chmod(uv_script.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        [str(_repo_root() / ".githooks" / "pre-push"), "origin", "git@example.com"],
        cwd=_repo_root(),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "pre-push: coverage must reach 100% before push." in result.stderr
    assert "do not add superficial tests only to raise the percentage." in result.stderr
    assert "understand the domain, user flows, and failure modes" in result.stderr


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]
