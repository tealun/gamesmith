#!/usr/bin/env bash
# Commit the contents of a built plugin folder to a branch that holds nothing else,
# then push it. Appends one commit per change; never rewrites the branch's history.
# Usage: scripts/publish_plugin_branch.sh <built-plugin-dir> <branch> [remote]
set -euo pipefail

src=$(cd "$1" && pwd)
branch=$2
remote=${3:-origin}
version=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['version'])" "$src/.claude-plugin/plugin.json")
source_sha=$(git rev-parse --short HEAD)
work=$(mktemp -d)
trap 'git worktree remove --force "$work" >/dev/null 2>&1 || true' EXIT

git config user.name >/dev/null || git config user.name "github-actions[bot]"
git config user.email >/dev/null || git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

if git ls-remote --exit-code --heads "$remote" "$branch" >/dev/null; then
  git fetch --quiet "$remote" "refs/heads/$branch"
  git worktree add --quiet --detach "$work" FETCH_HEAD
else
  git worktree add --quiet --detach "$work"
  git -C "$work" checkout --quiet --orphan "publish-$branch"
fi

# Replace everything except .git with the built plugin.
find "$work" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
git -C "$work" rm -rq --cached --ignore-unmatch .
cp -a "$src/." "$work/"
git -C "$work" add -A

if git -C "$work" diff --cached --quiet && git -C "$work" rev-parse --verify --quiet HEAD >/dev/null; then
  echo "$branch already holds gamesmith $version; nothing to commit"
  exit 0
fi
git -C "$work" commit --quiet -m "gamesmith $version (built from $source_sha)"
git -C "$work" push --quiet "$remote" "HEAD:refs/heads/$branch"
echo "pushed gamesmith $version to $branch: $(git -C "$work" rev-parse --short HEAD)"
