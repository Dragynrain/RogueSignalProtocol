# GitHub Repository Setup Guide

Complete checklist for configuring your GitHub repository settings.

---

## ✅ Files Created (Already Done!)

The following files have been added to your repository:

- `.github/ISSUE_TEMPLATE/bug_report.md` - Bug report template
- `.github/ISSUE_TEMPLATE/feature_request.md` - Feature request template
- `.github/PULL_REQUEST_TEMPLATE.md` - Pull request template
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Community standards
- `SECURITY.md` - Security policy

**Next Step:** Commit and push these files to GitHub.

---

## 📋 GitHub Settings to Update Manually

You'll need to log into GitHub and update these settings manually:

### 1. Repository Description

**Where:** Repository main page → "About" section (gear icon ⚙️)

**Current:** "Hacking themed Stealth Traditional Roguelike in Python TCOD"

**Update to:**
```
A coffee break cyberspace stealth roguelike with 10-15 minute runs. Exfiltrate from corporate networks, avoid AI security, discover hidden secrets. Built with Python + TCOD.
```

---

### 2. Website URL

**Where:** Repository main page → "About" section (gear icon ⚙️)

**Add one of:**
- **Option A (Recommended):** `https://dragynrain.itch.io/rogue-signal-protocol`
- **Option B:** `https://discord.gg/aUZgmrpU`

---

### 3. Topics/Tags

**Where:** Repository main page → "About" section (gear icon ⚙️) → "Topics"

**Add these 10 topics:**
```
roguelike
python
tcod
stealth-game
cyberpunk
procedural-generation
indie-game
gamedev
roguelite
turn-based
```

**How to add:** Click the gear icon → In the "Topics" field, type each topic and press Enter.

---

### 4. Social Preview Image

**Where:** Settings → General → Social preview

**Steps:**
1. Go to: `https://github.com/Dragynrain/RogueSignalProtocol/settings`
2. Scroll to "Social preview"
3. Click "Edit"
4. Upload: `docs/images/banner.png` from your repository
5. Click "Save"

**Note:** GitHub recommends 1280x640px. Your banner is 1200x600px which works fine.

---

### 5. Enable GitHub Discussions

**Where:** Settings → General → Features → Discussions

**Steps:**
1. Go to: `https://github.com/Dragynrain/RogueSignalProtocol/settings`
2. Scroll to "Features" section
3. Check ✅ **Discussions**
4. Click "Set up discussions"
5. GitHub will create a welcome post - you can customize it

**Recommended Categories:**
- 💬 General - General discussion
- 💡 Ideas - Feature suggestions and brainstorming
- 🎮 Gameplay - Share runs, strategies, stories
- 🐛 Q&A - Questions and help
- 📢 Announcements - Development updates (you can post only)

---

### 6. Repository Features (Verify These Are Enabled)

**Where:** Settings → General → Features

**Ensure these are checked ✅:**
- [x] Issues
- [x] Projects
- [x] Discussions (after step 5)
- [x] Preserve this repository (optional but recommended)

**Can be unchecked:**
- [ ] Wikis (unless you want a wiki)
- [ ] Sponsorships (unless you want GitHub Sponsors)

---

### 7. Default Branch Protection (Optional but Recommended)

**Where:** Settings → Branches → Branch protection rules

**Steps:**
1. Click "Add branch protection rule"
2. Branch name pattern: `main`
3. Enable these protections:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Select: "build-windows" (your GitHub Actions workflow)
   - ✅ Require conversation resolution before merging

**Note:** This prevents accidental direct pushes to main. Use branches instead.

---

## 🗑️ Optional Cleanup

### Files to Consider Removing

**Keep As-Is (Recommended):**
- `pytest.ini` - Pytest configuration (needed for development)
- `RogueSignalProtocol.spec` - PyInstaller spec (auto-generated, gitignored)
- `game_inspection.py` - Debug/development tool (useful for troubleshooting)
- `tests/` - Test suite (important for development)

**No cleanup needed!** Your `.gitignore` is properly configured and the GitHub Actions workflow only packages necessary files for releases.

---

## ✅ Debug Mode in Releases - CONFIRMED

**From `.github/workflows/release.yml` lines 58-61:**
```yaml
# Create debug_mode.flag for alpha releases
Write-Host "Creating debug_mode.flag for alpha/beta testing..."
"This file enables DEBUG logging for playtester bug reports." | Out-File -FilePath "dist\debug_mode.flag" -Encoding ASCII
```

**Status:** ✅ **Debug mode IS enabled** in GitHub Actions releases.

All alpha releases automatically include `debug_mode.flag`, enabling verbose logging for bug reports.

---

## 📝 Commit These Changes

After updating GitHub settings, commit the new community files:

```bash
git add .github/ISSUE_TEMPLATE/ .github/PULL_REQUEST_TEMPLATE.md
git add CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md
git commit -m "Add GitHub community health files

- Add bug report and feature request templates
- Add pull request template
- Add contributing guidelines
- Add code of conduct (Contributor Covenant 2.1)
- Add security policy for vulnerability reporting"
git push origin main
```

---

## 🎉 Verification Checklist

After completing all steps, verify:

- [ ] Repository description is updated
- [ ] Website URL is added
- [ ] All 10 topics are added
- [ ] Social preview image shows your banner
- [ ] GitHub Discussions is enabled
- [ ] Community files are committed and pushed
- [ ] Issue templates appear when creating new issues
- [ ] Pull request template appears when creating PRs

**GitHub will show a "Community Profile" score** at:
`https://github.com/Dragynrain/RogueSignalProtocol/community`

You should see checkmarks for:
- ✅ Description
- ✅ README
- ✅ Code of conduct
- ✅ Contributing
- ✅ License
- ✅ Issue templates
- ✅ Pull request template
- ✅ Security policy

---

## 🔗 Quick Links for Settings Pages

- **General Settings:** https://github.com/Dragynrain/RogueSignalProtocol/settings
- **Community Profile:** https://github.com/Dragynrain/RogueSignalProtocol/community
- **Branch Protection:** https://github.com/Dragynrain/RogueSignalProtocol/settings/branches
- **Discussions Setup:** https://github.com/Dragynrain/RogueSignalProtocol/settings (scroll to Features)

---

**Questions?** Just ask or check the [GitHub Docs](https://docs.github.com/en/repositories).
