#!/usr/bin/env bash
# Explicit retry only: never overwrite an existing repository or force push.
set -euo pipefail
cd "$(dirname "$0")/../.."
command -v gh >/dev/null
command -v git-lfs >/dev/null
gh auth status
[[ "$(git branch --show-current)" == main ]]
[[ -z "$(git status --porcelain)" ]]
git lfs fsck
# HTTP/network/auth errors must not be interpreted as repository absence.
response=$(mktemp)
trap 'rm -f "$response"' EXIT
if gh api repos/kkkkkmj/cyclo-toast-teleop >"$response" 2>&1; then
  gh repo view kkkkkmj/cyclo-toast-teleop --json nameWithOwner,isPrivate,defaultBranchRef,url
  git ls-remote https://github.com/kkkkkmj/cyclo-toast-teleop.git
  echo 'Repository exists: inspect its contents separately. No creation, remote change or push performed.' >&2
  exit 2
fi
if ! grep -q 'HTTP 404' "$response"; then
  echo 'Repository lookup failed; resolve authentication/network before retrying.' >&2
  exit 1
fi
# Use a new repository only; no deletion/recreation or --force.
if git remote get-url origin >/dev/null 2>&1; then
  echo 'Existing local origin requires review before publishing.' >&2
  exit 2
fi
gh repo create kkkkkmj/cyclo-toast-teleop --public --source=. --remote=origin
# Hook pushes LFS content; explicit all upload makes the requirement visible.
git lfs push --all origin main
git push -u origin main
local_commit=$(git rev-parse HEAD)
remote_commit=$(git ls-remote origin refs/heads/main | cut -f1)
[[ "$local_commit" == "$remote_commit" ]]
clone_dir=$(mktemp -d)
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/kkkkkmj/cyclo-toast-teleop.git "$clone_dir/verify"
git -C "$clone_dir/verify" lfs pull
git -C "$clone_dir/verify" lfs fsck
[[ "$(git -C "$clone_dir/verify" rev-parse HEAD)" == "$local_commit" ]]
echo "Verified remote commit and independent LFS retrieval: $local_commit"
echo "Verification clone retained: $clone_dir/verify"
