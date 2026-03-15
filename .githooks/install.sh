#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

chmod +x .githooks/pre-commit .githooks/pre-push .githooks/install.sh
git config core.hooksPath .githooks

echo "Configured git hooks path: $(git config --get core.hooksPath)"
echo "Hooks installed from $repo_root/.githooks"
