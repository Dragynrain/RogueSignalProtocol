# 1.0.0 Release Runbook - 2026-06-01

Tailored to the current state. The generic master checklist is at `docs/RELEASE_CHECKLIST.md` if you need long-form detail on any step. Delete this file after the release is complete.

---

## What's already done (skip these)

- Version pinned at 1.0.0 in `game_rules.json`, README badges, all packaging files
- CHANGELOG dated 2026-06-01 with full content + voice pass
- `validate-release.py`: all 6 checks pass (`--no-cov` bug fixed)
- Save migration: synthetic 0.9.2-shaped save loads with version warning, schema unchanged
- `pip audit`: 16 CVEs, all in dev-only deps (no runtime exposure - pillow not imported)
- Public-facing voice pass: launch announcement, READMEs, itch.io page (HTML+BBCode), CHANGELOG, roguebasin
- 1.0 content updates on all 4 Reddit/forum drafts
- Packaging fixes: metainfo date (2026-06-01), developer name (Adam not Alex), exploit count (13 not 12), Steam Deck wording ("tested" not "verified"), Flathub manifest URL filename, copyright 2026
- Workflow `build_info.txt` cosmetic bug fixed (was hardcoded "Alpha")

---

## Pre-flight checks (5 min)

Run all of these first. Stop and investigate if any fail.

```bash
# Working tree clean (all 1.0 prep committed)
git status
# Expected: "nothing to commit, working tree clean"

# gh authenticated
gh auth status
# Expected: "Logged in to github.com"

# Butler available (if pushing to itch manually)
build\butler\butler.exe status dragynrain/rogue-signal-protocol
# Expected: shows channel list

# Itch auto-push configured?
gh variable list -R Dragynrain/RogueSignalProtocol
# Look for: ENABLE_ITCH_PUSH = true
# If absent or false: you'll need to run push-all.bat after the release

# Docker running (needed for AUR .SRCINFO generation on Windows)
docker --version

# Version source of truth
grep '"version"' game_rules.json
# Expected: "version": "1.0.0"
```

---

## Step 1: Build Windows locally (10 min)

```bash
build\build.bat release 1.0.0
```

Verify:
```bash
dir dist\RogueSignalProtocol.exe
# Expected: ~39 MB

dir releases\RogueSignalProtocol_release_1.0.0.zip
# Expected: ~195 MB

dir releases\RogueSignalProtocol_release_1.0.0.zip.sha256
# Expected: checksum file exists
```

**Smoke test the actual exe** before tagging. This is the only manual gate:
1. Run `dist\RogueSignalProtocol.exe`
2. Confirm no CMD window appears (the console=False fix from this release)
3. Run through the prologue tutorial end-to-end (5 sections)
4. Start a real run, make it to level 2 minimum
5. Die at least once, confirm save is deleted
6. Check `%LOCALAPPDATA%\RogueSignalProtocol\logs\` for errors

If anything blocks, stop and fix before tagging.

---

## Step 2: Tag and create the GitHub Release (5 min)

```bash
# Tag the current main HEAD
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Verify tag on remote
git ls-remote --tags origin | grep v1.0.0

# Extract release notes from CHANGELOG
# (PowerShell since git-bash sed handling of ## is awkward)
powershell -NoProfile -Command "(Get-Content CHANGELOG.md -Raw) -split '(?ms)^## \[' | Select-Object -Index 1" > release_notes.tmp

# Create the GitHub Release - this triggers the Linux build workflow
gh release create v1.0.0 ^
  --title "v1.0.0" ^
  --notes-file release_notes.tmp ^
  "releases/RogueSignalProtocol_release_1.0.0.zip"

del release_notes.tmp
```

Verify the workflow started:
```bash
gh run list --workflow=release.yml -L 1
# Expected: status "in_progress" or "queued"
```

If `gh release create` fails, the most common cause is the asset path - make sure the zip name matches what `build.bat release 1.0.0` actually produced.

---

## Step 3: Wait for the workflow (~10 min)

```bash
gh run watch <run-id>
```

Once it completes successfully:
```bash
gh release view v1.0.0 --json assets -q '.assets[].name'
# Expected: 3 files
#   RogueSignalProtocol-1.0.0-Linux.tar.gz
#   RogueSignalProtocol-1.0.0-x86_64.AppImage
#   RogueSignalProtocol_release_1.0.0.zip
```

If the workflow fails, see Rollback section at the bottom. **Do not proceed past this step until all 3 assets are on the release.**

---

## Step 4: itch.io push (5 min, may be automatic)

**If `ENABLE_ITCH_PUSH=true`** (checked in pre-flight): the `push-itch` workflow job already ran. Just verify:

```bash
build\butler\butler.exe status dragynrain/rogue-signal-protocol
# Expected: windows / linux / linux-appimage all show 1.0.0
```

**If not auto-pushed:**

```bash
build\push-all.bat 1.0.0
```

This downloads the Linux assets from the GitHub release and pushes all three channels.

Confirm:
```bash
curl -s -o NUL -w "%%{http_code}" https://dragynrain.itch.io/rogue-signal-protocol
# Expected: 200
```

---

## Step 5: AUR push (10-15 min)

PKGBUILD is already pre-bumped to `pkgver=1.0.0`. Only the sha256 needs updating (computed from the GitHub-hosted Linux tarball).

```bash
build\update-aur.bat 1.0.0 release
```

This will:
- Download the tarball from the GitHub release
- Compute its sha256, patch PKGBUILD
- Regenerate .SRCINFO via Docker
- Copy into D:\Projects\aur-rogue-signal-protocol-bin\

Then push:
```bash
cd /d/Projects/aur-rogue-signal-protocol-bin
git add PKGBUILD .SRCINFO rogue-signal-protocol-bin.install
git commit -m "Update to 1.0.0"
git push origin master
```

Verify (after a few minutes of AUR API cache):
```bash
curl -s "https://aur.archlinux.org/rpc/v5/info?arg[]=rogue-signal-protocol-bin" | grep -o '"Version":"[^"]*"'
# Expected: "Version":"1.0.0-1"
```

---

## Step 6: Marketing (spread across the day)

Paste-ready files are in `marketing/`:

- **itch.io page text:** open https://dragynrain.itch.io/rogue-signal-protocol/edit, paste from `marketing/itch_io_page.html` (rich text mode) or `marketing/itch_io_page_formatted.txt` (BBCode mode).
- **itch.io devlog post:** `marketing/itch_100_launch_announcement.md` - paste body, set title to "1.0 - Out of Beta" or similar.
- **Reddit r/roguelikedev or r/roguelikes:** `marketing/reddit_post_roguelikes.md` - post weekday morning, respond to comments within 2 hours.
- **Reddit Sharing Saturday** (only if Saturday): `marketing/reddit_sharing_saturday.md`.
- **r/DestroyMyGame** (optional, for bug-hunt feedback): `marketing/reddit_destroymygame_draft.md`.
- **RogueTemple forums:** `marketing/roguetemple_100_draft.md` - BBCode version at the bottom.
- **RogueBasin wiki:** `marketing/roguebasin_wiki_draft.md` - paste the wiki markup block. Verify the `{{Gameinfo}}` template name against current RogueBasin conventions before saving.

Also worth a single Discord announcement linking to the itch.io page.

---

## Step 7: Wiki sync (5 min)

```bash
.venv\Scripts\python.exe docs\generate_wiki.py
```

This regenerates auto-generated wiki pages from `game_content.json`. Review the diff, then sync to the GitHub Wiki repo:

```bash
cd ..
git clone https://github.com/Dragynrain/RogueSignalProtocol.wiki.git
cp -r RogueSignalProtocol/docs/wiki/*.md RogueSignalProtocol.wiki/
cd RogueSignalProtocol.wiki
git add . && git commit -m "Update wiki for v1.0.0" && git push
```

---

## Post-release (first 24 hours)

- Watch itch.io comments
- Watch GitHub Issues
- Watch the Discord
- Note any crash reports - if 2+ people report the same crash, that's a hotfix candidate

---

## Deferred past launch day (acceptable)

- **Flathub submission.** Manifest at `packaging/linux/info.aforster.roguesignalprotocol.yml` still has `PLACEHOLDER_UPDATE_AFTER_LINUX_BUILD` for sha256. After step 3, compute sha256 of the Linux tarball and patch it in. Then needs Linux environment to test-build, record video of it running, submit PR manually via GitHub web UI (Flathub bans CLI and AI submissions). Previous PR #7414 was rejected only because Flathub doesn't accept betas - they explicitly said resubmit at 1.0. Aim for week 1.
- **Screenshot refresh** (have 5, press-kit ideal is 9-12). Can backfill.
- **Trailer.** Raw `gameplay_full.mp4` / `gameplay_short.mp4` exist. Final cut per `marketing/TRAILER_PLAN.md`. Reddit posts work without it.
- **VirusTotal scan** of the .exe for documentation purposes.

---

## Rollback procedures

**Bad commit pushed but tag not created:**
```bash
git reset --soft HEAD~1
# fix issue, recommit, push
```

**Tag pushed but release creation failed:**
```bash
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
# fix, retry from step 2
```

**Release created but workflow failed:**
```bash
gh release delete v1.0.0 --yes
# Investigate workflow log: gh run view <run-id> --log-failed
# Fix issue, recreate from step 2
```

**Release published but critical bug found post-launch:**
- Mark the GitHub Release as pre-release immediately (`gh release edit v1.0.0 --prerelease`)
- Update release description with a warning at the top
- Cut hotfix branch: `git checkout -b hotfix/v1.0.1`
- Fix, test, release v1.0.1 ASAP

**Itch.io push failed but GitHub release succeeded:**
- `push-all.bat` is idempotent, just re-run it
