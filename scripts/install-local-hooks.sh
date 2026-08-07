#!/usr/bin/env bash
# Install machine-local git hooks for this repo (safe to commit; hooks are local).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_SCRIPT="${REPO_ROOT}/scripts/local/pre-push-anon-check.sh"
EXAMPLE="${REPO_ROOT}/scripts/pre-push-anon-check.example.sh"
HOOK="${REPO_ROOT}/.git/hooks/pre-push"

if [[ ! -f "$EXAMPLE" ]]; then
  echo "missing ${EXAMPLE}" >&2
  exit 1
fi

mkdir -p "${REPO_ROOT}/scripts/local"
if [[ ! -f "$LOCAL_SCRIPT" ]]; then
  cp "$EXAMPLE" "$LOCAL_SCRIPT"
  chmod +x "$LOCAL_SCRIPT"
  echo "Created ${LOCAL_SCRIPT} (gitignored — edit for your machine if needed)"
else
  chmod +x "$LOCAL_SCRIPT"
  echo "Using existing ${LOCAL_SCRIPT}"
fi

cat > "$HOOK" <<EOF
#!/usr/bin/env bash
exec "${LOCAL_SCRIPT}" "\$@"
EOF
chmod +x "$HOOK"

echo "Installed .git/hooks/pre-push -> ${LOCAL_SCRIPT}"
echo "Test with: github-identity anon && github-identity check"
