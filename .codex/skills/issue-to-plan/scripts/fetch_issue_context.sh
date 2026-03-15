#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: bash .codex/skills/issue-to-plan/scripts/fetch_issue_context.sh <issue-number>" >&2
  exit 1
fi

gh issue view "$1" --json number,title,body,url,labels,assignees
