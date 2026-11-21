# Repository publication handoff

## Pending migration

The requested targets are private `kkkkkmj/cyclo-toast-teleop-mj` for the original
history and public `kkkkkmj/cyclo-toast-teleop` for the documentation copy.
On 2026-11-21, Git and GitHub CLI could not reach GitHub from this environment.
Neither remote identity/visibility nor remote HEAD could be inspected. No remote
rename, visibility change or repository creation was performed. Do not push the
public documentation to the existing remote until the rename and new repository
creation have been verified.

The original local checkout was renamed to
`/home/mj/nrf_humanoid/cyclo-toast-teleop-mj` and retained at
`197d9926456f6e2ff97a76e20e71391edf25a540`, with its original tracked files,
ignored files, Git history and LFS objects. Its origin now names the intended
private URL; this local configuration is not evidence of remote creation/privacy.
An independent local transport clone at
`/home/mj/nrf_humanoid/cyclo-toast-teleop` contains the documentation changes,
independent Git/LFS storage and no copied ignored output or credentials.

## Resume with working GitHub access

These steps are for the requested migration, not installation. Check each result
before continuing. They use ordinary pushes, never force pushes or deletion.
If either destination already exists, inspect its identity, contents, visibility
and refs; do not overwrite it or assume it belongs to this migration.

1. Inspect both repository names. Record the existing repository's numeric `id`.
   A connection/authentication error is not proof that the archive name is absent.

   ```bash
   gh api repos/kkkkkmj/cyclo-toast-teleop --jq '{id,name,visibility,default_branch}'
   gh api repos/kkkkkmj/cyclo-toast-teleop-mj --jq '{id,name,visibility,default_branch}'
   ```

2. Only after confirming the original identity and that the archive name is
   available, rename the existing repository and make it private. Verify that
   the returned archive ID matches the original ID and visibility is private.

   ```bash
   gh api --method PATCH repos/kkkkkmj/cyclo-toast-teleop \
     -f name=cyclo-toast-teleop-mj -F private=true
   gh api repos/kkkkkmj/cyclo-toast-teleop-mj --jq '{id,name,visibility,default_branch}'
   ```

3. Preserve any remote-only history before pushing the archive. Fetch and inspect
   divergence; a non-fast-forward must be investigated, not forced. The local
   archive has already retained the rack inclusion commit.

   ```bash
   cd /home/mj/nrf_humanoid/cyclo-toast-teleop-mj
   git fetch origin
   git log --oneline --left-right main...origin/main
   git lfs push --all origin
   git push origin --all
   git push origin --tags
   git ls-remote origin HEAD refs/heads/main
   ```

4. Create the new public repository without initialization. Confirm its numeric
   ID differs from the archive and that it has no existing branches. GitHub can
   redirect the old URL after a rename; do not confuse that redirect with the
   new repository.

   ```bash
   gh repo create kkkkkmj/cyclo-toast-teleop --public
   gh api repos/kkkkkmj/cyclo-toast-teleop --jq '{id,name,visibility,default_branch}'
   gh api repos/kkkkkmj/cyclo-toast-teleop/branches --jq '.[].name'
   ```

5. Publish the documentation copy and required LFS history, then verify both
   repository settings and the new remote HEAD.

   ```bash
   cd /home/mj/nrf_humanoid/cyclo-toast-teleop
   git lfs push --all origin
   git push -u origin main
   git push origin --tags
   gh api repos/kkkkkmj/cyclo-toast-teleop-mj --jq '{id,name,visibility,default_branch}'
   gh api repos/kkkkkmj/cyclo-toast-teleop --jq '{id,name,visibility,default_branch}'
   git ls-remote origin HEAD refs/heads/main
   git rev-parse HEAD
   ```

6. Clone from GitHub into a new directory, retrieve LFS and verify the rack and
   documentation. No manual asset copy should be needed for the rack.

   ```bash
   VERIFY_DIR=$(mktemp -d /tmp/toast-public-verify.XXXXXX)
   git clone https://github.com/kkkkkmj/cyclo-toast-teleop.git "$VERIFY_DIR/repo"
   cd "$VERIFY_DIR/repo"
   git lfs pull
   git lfs fsck
   git rev-parse HEAD
   sha256sum source/cyclo_lab/data/objects/bread_slot/bread_slot.usdz
   test -f docs/README.md
   test -f docs/ASSETS.md
   python3 scripts/tools/check_release.py
   ```

   Expected rack SHA256:
   `338eb23d759224c0686857b3e793070b2bf03f9c7fe25f872a3c598bd67330d8`.
   RoboDojo downloads and NVIDIA runtime assets remain separate prerequisites;
   this procedure does not certify Docker, GPU or Quest operation.

## Local checks for the documentation copy

The CPU release preflight passed (three manifests, four groups of 25 scenarios,
eight launcher boundary plans and Python syntax). The seven asset installer /
synthetic downloader tests passed. The full `--assets` check correctly reported
missing RoboDojo files in the clean copy; ignored caches were not carried over.
The serving-success suite could not run because host Python lacks `torch`.
These outcomes do not supersede earlier validation results. No simulator or
container was started, stopped or otherwise manipulated.

## Prior access checks

The earlier 2026-11-21 documentation review observed local and cached remote
refs at `c43e872c64de310b262a464e1ac29828a3a63ee4`, but anonymous remote lookup
failed DNS. The subsequent rack upload attempt created local commit `197d992`
and failed to push/clone due to the same network limitation. These observations
are historical and do not establish current GitHub visibility or HEAD.
The [2026-11-11 validation](VALIDATION.md) retains its original failures and
unverified results. Local cached refs and local clones are not remote verification.
