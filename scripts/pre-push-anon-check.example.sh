#!/usr/bin/env bash
# Machine-local pre-push guard — copy to scripts/local/pre-push-anon-check.sh
# (that path is gitignored). Installed by scripts/install-local-hooks.sh
#
# Blocks push unless github-identity active profile is "anon" and check passes.

set -euo pipefail

ACTIVE_FILE="${HOME}/.github-profiles/active"

if [[ ! -f "$ACTIVE_FILE" ]]; then
  echo "pre-push blocked: no github-identity profile active"
  echo "Run: github-identity anon && github-identity check"
  exit 1
fi

active=$(tr -d '[:space:]' < "$ACTIVE_FILE")
if [[ "$active" != "anon" ]]; then
  echo "pre-push blocked: active github-identity profile is '${active}', not 'anon'"
  echo "This repo must be pushed only under the anonymous GitHub account."
  echo "Run: github-identity anon"
  exit 1
fi

if ! command -v github-identity >/dev/null 2>&1; then
  echo "pre-push blocked: github-identity not found in PATH"
  echo "Ensure ~/bin is on PATH (see ~/.bash_profile)"
  exit 1
fi

if ! github-identity check; then
  echo "pre-push blocked: github-identity check failed"
  exit 1
fi

exit 0
