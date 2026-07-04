#!/usr/bin/env bash
# deploy_fix.sh — push the current branch to roam + bump gateway submodule + open/merge PR.
#
# Usage (from /root/roam):
#   ./scripts/deploy_fix.sh "Short reason for deploy"
#
# Assumes:
#   - You are on a feature/fix branch in /root/roam
#   - /root/gateway exists and has a matching branch (or master)
#   - gh CLI is authenticated

set -euo pipefail

REASON="${1:-}"
if [[ -z "$REASON" ]]; then
    echo "Usage: $0 \"Short reason for deploy\"" >&2
    exit 1
fi

ROAM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GATEWAY_DIR="/root/gateway"
ROAM_BRANCH="$(git -C "$ROAM_DIR" rev-parse --abbrev-ref HEAD)"

# ── 1. Roam: run tests, format, push ─────────────────────────────────────────
echo "==> [roam] running tests…"
(cd "$ROAM_DIR" && python3 -m pytest tests/ -q --tb=short)

echo "==> [roam] pushing $ROAM_BRANCH…"
git -C "$ROAM_DIR" push origin "$ROAM_BRANCH"
ROAM_SHA="$(git -C "$ROAM_DIR" rev-parse --short HEAD)"
echo "==> [roam] HEAD = $ROAM_SHA"

# ── 2. Gateway: update submodule, rebase on master, push, open+merge PR ──────
echo "==> [gateway] fetching + checking out roam@$ROAM_SHA…"
(cd "$GATEWAY_DIR/services/roam" && git fetch origin && git checkout "$ROAM_SHA")

# Commit the submodule bump
GW_BRANCH="fix/idbfs-save-persistence"
git -C "$GATEWAY_DIR" checkout "$GW_BRANCH" 2>/dev/null || git -C "$GATEWAY_DIR" checkout -b "$GW_BRANCH"
git -C "$GATEWAY_DIR" add services/roam
git -C "$GATEWAY_DIR" commit -m "fix: bump services/roam to $ROAM_SHA ($REASON)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>" || echo "nothing to commit in gateway"

# Rebase on master so PR is clean
git -C "$GATEWAY_DIR" fetch origin master
git -C "$GATEWAY_DIR" rebase origin/master

git -C "$GATEWAY_DIR" push --force-with-lease origin "$GW_BRANCH"

# Create PR if none exists; otherwise it's just the updated push
PR_URL="$(gh pr list --repo Stephenson-Software/gateway --head "$GW_BRANCH" --json url -q '.[0].url' 2>/dev/null || true)"
PR_NUMBER="$(gh pr list --repo Stephenson-Software/gateway --head "$GW_BRANCH" --json number -q '.[0].number' 2>/dev/null || true)"

if [[ -z "$PR_URL" ]]; then
    echo "==> [gateway] creating PR…"
    PR_URL="$(gh pr create \
        --repo Stephenson-Software/gateway \
        --title "fix: $REASON" \
        --body "Bumps services/roam to $ROAM_SHA.

🤖 Generated with [Claude Code](https://claude.com/claude-code)" \
        --base master \
        --head "$GW_BRANCH")"
    PR_NUMBER="${PR_URL##*/}"
fi

echo "==> [gateway] PR: $PR_URL — merging…"
gh pr merge "$PR_NUMBER" --repo Stephenson-Software/gateway --merge 2>&1 || {
    echo "Merge failed (possibly needs rebase); retrying after re-fetch…"
    git -C "$GATEWAY_DIR" fetch origin master
    git -C "$GATEWAY_DIR" rebase origin/master
    git -C "$GATEWAY_DIR" push --force-with-lease origin "$GW_BRANCH"
    gh pr merge "$PR_NUMBER" --repo Stephenson-Software/gateway --merge
}

# ── 3. Monitor deploy ─────────────────────────────────────────────────────────
echo "==> [gateway] waiting for deploy…"
RUN_ID="$(gh run list --repo Stephenson-Software/gateway --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID" --repo Stephenson-Software/gateway

# ── 4. Smoke-check prod ───────────────────────────────────────────────────────
echo "==> [smoke] checking https://roam.preponderous.org/play …"
HTTP=$(curl -sS -o /dev/null -w "%{http_code}" "https://roam.preponderous.org/play")
if [[ "$HTTP" != "200" ]]; then
    echo "ERROR: /play returned HTTP $HTTP" >&2
    exit 1
fi

echo "==> [smoke] checking game-worker.js version…"
WORKER=$(curl -sS "https://roam.preponderous.org/web/game-worker.js" | head -5)
echo "$WORKER"

echo ""
echo "Deploy complete. Worker serving roam@$ROAM_SHA."
echo "Play at: https://roam.preponderous.org/play"
