#!/usr/bin/env bash
# Publish only to the authorized target, preserving compatible existing history.
set -euo pipefail
cd "$(dirname "$0")/../.."
if ! command -v gh >/dev/null; then
  echo 'GitHub CLI unavailable. Install gh, then run gh auth login --web. Existing Git credentials alone cannot create a private repository.' >&2
  exit 1
fi
command -v git-lfs >/dev/null
gh auth status
[[ "$(git branch --show-current)" == main ]]
[[ -z "$(git status --porcelain)" ]]
git lfs fsck
response=$(mktemp)
trap 'rm -f "$response"' EXIT
url=https://github.com/kkkkkmj/cyclo_lab_toast.git
if gh api repos/kkkkkmj/cyclo_lab_toast >"$response" 2>&1; then
  gh repo view kkkkkmj/cyclo_lab_toast --json nameWithOwner,isPrivate,defaultBranchRef,url
  python3 - "$response" <<'PY'
import json, sys
info = json.load(open(sys.argv[1]))
if not info['private']:
    raise SystemExit('Existing repository is public: stop for review; visibility is not changed automatically.')
PY
  # Inspect actual remote files and branches before deciding whether an FF is safe.
  git ls-remote "$url"
  gh api repos/kkkkkmj/cyclo_lab_toast/contents --jq '.[].path'
  git fetch "$url" refs/heads/main
  git show --stat --oneline FETCH_HEAD
  git diff --stat FETCH_HEAD HEAD
  if ! git merge-base --is-ancestor FETCH_HEAD HEAD; then
    echo 'Remote main is not an ancestor of local main. Stop: no overwrite or force push.' >&2
    exit 2
  fi
else
  if ! grep -q 'HTTP 404' "$response"; then
    echo 'Repository lookup failed; resolve network/authentication and retry.' >&2
    exit 1
  fi
  gh repo create kkkkkmj/cyclo_lab_toast --private
fi
if git remote get-url origin >/dev/null 2>&1; then
  [[ "$(git remote get-url origin)" == "$url" ]] || { echo 'Unexpected local origin; refusing to change it.' >&2; exit 2; }
else
  git remote add origin "$url"
fi
[[ "$(git remote get-url --push --all origin)" == "$url" ]] || { echo 'Unexpected push target; refusing to publish.' >&2; exit 2; }
git lfs push --all origin main
git push -u origin main
local_commit=$(git rev-parse HEAD)
remote_commit=$(git ls-remote origin refs/heads/main | cut -f1)
[[ "$local_commit" == "$remote_commit" ]]
clone_dir=$(mktemp -d)
# HTTPS clone, fresh object store; explicitly override any configured shared LFS cache.
GIT_LFS_SKIP_SMUDGE=1 git clone "$url" "$clone_dir/verify"
git -C "$clone_dir/verify" config --local lfs.storage "$clone_dir/verify/.git/lfs"
git -C "$clone_dir/verify" lfs pull
git -C "$clone_dir/verify" lfs fsck
[[ "$(git -C "$clone_dir/verify" rev-parse HEAD)" == "$local_commit" ]]
python3 "$clone_dir/verify/scripts/tools/check_release.py"
echo "Verified remote commit, independent Git/LFS retrieval, vendored dependency checkout and CPU preflight: $local_commit"
echo "Verification clone: $clone_dir/verify"
echo 'External assets still require the documented acquisition, authorization and --assets check; no GPU test is implied.'
