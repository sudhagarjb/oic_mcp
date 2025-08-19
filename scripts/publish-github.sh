#!/bin/sh
set -euo pipefail

REPO_NAME=${1:-oic-monitoring-mcp}
GITHUB_USER=${2:-sudhagarjb}

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "Error: GITHUB_TOKEN environment variable is required" >&2
  exit 1
fi

API_JSON=$(cat <<JSON
{
  "name": "${REPO_NAME}",
  "private": false,
  "has_issues": true,
  "has_projects": false,
  "has_wiki": false
}
JSON
)

# Create repository if it doesn't exist
HTTP_CODE=$(curl -sS -o /tmp/gh_create_resp.json -w "%{http_code}" \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d "${API_JSON}")

if [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "422" ]; then
  echo "Failed to create repo. HTTP $HTTP_CODE" >&2
  cat /tmp/gh_create_resp.json >&2 || true
  exit 1
fi

REMOTE_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

# Set remote
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

git branch -M main || true
git push -u origin main 