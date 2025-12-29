# Plan: 1.0 Release

**Status:** Planning
**Created:** 2025-12-28

---

## Step 0: Setup Tracking (Do This First)

- [ ] Copy `RELEASE_CHECKLIST.md` to `RELEASE_CHECKLIST_1.0_PROGRESS.md`
- [ ] Use the progress file to track all standard release tasks
- [ ] This file tracks 1.0-SPECIFIC items only

---

## 1.0-Specific Items

### Flathub Domain Fix (From PR #7414 Rejection)

The 0.9.0-beta submission was rejected because the domain didn't resolve. Fixed by changing to `aforster.info`, but:

- [ ] Add Rogue Signal Protocol mention to `https://aforster.info`
  - Current state: Page loads, title is "Adam Forster - Portfolio", game NOT mentioned
  - Action: Add text/link mentioning the game anywhere on the page

### Flathub Manifest Fixes (Already Done)

These were fixed 2025-12-28 and will be in the 1.0 submission:

- [x] Added header comments explaining PyInstaller binary distribution
- [x] Added `flathub.json` comment explaining x86_64 limitation
- [x] Fixed `packaging/linux/README.md` - updated outdated `com.dragynrain.*` references to `info.aforster.*`

### Metainfo Update for Stable Release

- [ ] Change `info.aforster.roguesignalprotocol.metainfo.xml`:
  - `version="0.9.0-beta"` → `version="1.0.0"`
  - `type="development"` → `type="stable"`
  - Update `<description>` to reflect stable release

### First Stable Flathub Submission

This is the first stable release, so:

- [ ] Record video of Flatpak running (required for new submissions)
- [ ] Submit to Flathub stable branch (not beta)
- [ ] After acceptance: set up verification badge via Developer Portal

---

## Post-1.0: Verification Badge Setup

After Flathub accepts the app:

- [ ] Log into https://flathub.org/developer-portal
- [ ] Get verification token for `info.aforster.roguesignalprotocol`
- [ ] Create `https://aforster.info/.well-known/org.flathub.VerifiedApps.txt`
- [ ] Add token to file
- [ ] Verify badge appears on Flathub listing

---

## Notes

All other release tasks (version strings, builds, testing, distribution) are covered by `RELEASE_CHECKLIST.md`.
