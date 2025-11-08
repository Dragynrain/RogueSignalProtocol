# Pre-Release Checklist for Alpha 0.8.0

## ✅ COMPLETED

- [x] README.txt created (player-facing documentation)
- [x] Marketing folder created with drafts:
  - [x] itch_io_page_draft.md
  - [x] reddit_post_draft.md
  - [x] feedback_survey_draft.md
- [x] Verified keybindings (L=Look, F=Fragments, ?=Help)
- [x] Identified cleanup targets

---

## 🔴 CRITICAL - MUST FIX BEFORE RELEASE

### 1. ✅ **Create Logic Bomb sound effect** - COMPLETED

~~**PROBLEM:** Logic Bomb exploit uses placeholder sound (needs dedicated sound file)~~

**RESOLVED:** `sound/logic_bomb.wav` created (64KB, Nov 7)

---

### 2. ✅ **Update dist/ folder with current config files** - COMPLETED

~~**PROBLEM:** The `dist/` folder has **OUTDATED** config files!~~

**RESOLVED:** Copied current `game_content.json` to `dist/` (Nov 7) - now has correct exploit names (System Hop, Traffic Masquerade, etc.)

---

### 3. ✅ **Fix welcome message in dist/game_rules.json** - ALREADY CORRECT

~~Line 164 says: "Press 'L' to view discovered lore"~~

**VERIFIED:** Line 388 correctly shows: `"Press 'L' for look mode, 'F' for fragments"` - No changes needed!

---

## ⚠️ IMPORTANT - Should Do Before Release

### 4. ✅ **Clean up leftover files** - COMPLETED
~~```bash
# Delete development artifacts
rm game_debug.log
rm graphic-preview.log
rm nul

# Archive scratch code
mkdir .archive
mv preview_layout_new.py .archive/
```~~

**RESOLVED:** `nul` file deleted, no leftover dev artifacts found (Nov 7)

### 5. **Update README.txt keybindings (player-facing docs)**

Line 68 in README.txt says:
```markdown
- **Lore**: L key to view discovered story fragments
```

Should be:
```markdown
- **Lore**: F key to view discovered story fragments
- **Look Mode**: L key to examine entities and terrain
```

### 6. **Verify .gitignore**

Add these if not already present:
```
*.log
*.tmp
*.pyc
__pycache__/
rogue_signal_save.json
game_debug.log
```

### 7. **Test the EXE**

**Basic functionality:**
- [ ] Test on clean Windows 10/11 system (no Python installed)
- [ ] Verify all config files load correctly
- [ ] Play through one complete run (all 3 levels)
- [ ] Test save/load functionality
- [ ] Verify permadeath deletes save
- [ ] Check all 12 exploits work correctly
- [ ] Verify keybindings (L=Look, F=Fragments, ?=Help)

**CRITICAL: Test with TCOD 19.6.0 changes:**
- [ ] Verify nearest-neighbor scaling looks good (graphics sharper, not broken)
- [ ] Test fullscreen and windowed modes
- [ ] Verify graphics mode toggle still works (G key)

**Audio verification:**
- [ ] Test all 12 exploit sounds play correctly
- [ ] Verify music tracks load and loop
- [ ] Check Logic Bomb sound (logic_bomb.wav) plays

**Debug tools work in EXE:**
- [ ] Shift+F12 creates debug package
- [ ] Settings > Export Debug Package works
- [ ] Verify package includes saves/logs/screenshots

**Achievement system:**
- [ ] Unlock an achievement and verify it persists
- [ ] Check achievement popups display correctly
- [ ] Verify progress tracking works across deaths

**Edge cases:**
- [ ] Test Admin Avatar spawns when trace hits 100%
- [ ] Verify permadeath deletes save file completely
- [ ] Test look mode (L key) mouse and keyboard interaction
- [ ] Check fragments screen (F key) displays all discovered lore

### 7.5 **Create backup before packaging**

- [ ] Copy entire `dist/` folder to `dist_backup_v0.8.0/`
- [ ] Commit current state to git
- [ ] Tag release: `git tag v0.8.0-alpha`
- [ ] Push to GitHub: `git push origin v0.8.0-alpha`

### 7.6 **Test new player experience**

- [ ] Delete `user_settings.json` and test fresh start
- [ ] Verify intro dialogue appears
- [ ] Check help menu (?) is comprehensive
- [ ] Ensure first death shows feedback link clearly

---

## 📦 PACKAGING FOR ITCH.IO

### 8. **Create release package**

```bash
# Create clean distribution
mkdir RogueSignalProtocol_v0.8.0_Alpha
cd RogueSignalProtocol_v0.8.0_Alpha

# Copy executable and assets
cp ../dist/RogueSignalProtocol.exe .
cp ../dist/*.json .  # After fixing outdated configs!
cp -r ../dist/music .
cp -r ../dist/sound .
cp -r ../dist/main_menu .
cp ../dist/terminal10x16_gs_ro.png .

# Copy documentation
cp ../README.txt .
cp ../LICENSE .

# Create zip
cd ..
zip -r RogueSignalProtocol_v0.8.0_Alpha.zip RogueSignalProtocol_v0.8.0_Alpha/
```

### 9. **Prepare itch.io page**

- [ ] Upload .zip package
- [ ] Copy content from `marketing/itch_io_page_draft.md`
- [ ] Add 3-5 screenshots (gameplay, menus, lore)
- [ ] Set tags: roguelike, stealth, cyberpunk, turn-based, permadeath
- [ ] Set price: Pay what you want ($0 minimum)
- [ ] Mark as "Alpha - In Development"

### 9.5 **Update and verify screenshots**

**CRITICAL - Screenshots need updating for new features:**
- [ ] **Take new screenshot showing pixel explosion effect** (graphics mode)
- [ ] **Take new screenshot showing queue arrows** (the new directional arrow system)
- [ ] Verify `marketing/screenshots/` has at least 3-5 images total
- [ ] Verify images show both ASCII and graphics modes
- [ ] Ensure one screenshot shows the enemy movement queue UI clearly
- [ ] Consider capturing: gameplay, inventory, lore/fragments screen, death screen with feedback link

---

## 📢 LAUNCH STRATEGY

### 10. **Reddit posting**

**Option A: Start with r/roguelikedev (friendlier)**
- Use `marketing/reddit_post_draft.md`
- Post on weekday morning (9-11 AM EST)
- Respond to comments within first 2 hours

**Option B: Wait for r/roguelikes "Sharing Saturday"**
- Every Saturday
- More exposure but more competitive
- Include 2-3 screenshots

### 11. ✅ **Feedback collection** - COMPLETED

- [x] Create Google Form from `marketing/feedback_survey_draft.md`
- [x] Get shareable Google Form URL (short link): https://forms.gle/jbwGdn8VGPa6NG9p9
- [x] Add feedback form URL to all these locations:
  - [x] README.txt - Top section after title (MUST-HAVE)
  - [x] README.txt - "COMMUNITY & FEEDBACK" section (MUST-HAVE)
  - [x] README.md - Add feedback badge/button at top (MUST-HAVE)
  - [x] Itch.io page draft - Prominent "Share Feedback" button (MUST-HAVE)
  - [x] Reddit post draft - In "Where to Get It" section (MUST-HAVE)
  - [ ] In-game death screen - "Help improve the game: [link]" (OPTIONAL)
  - [ ] In-game victory screen (after level 3) (OPTIONAL)
  - [ ] In-game menu - "F: Give Feedback" option (OPTIONAL)

---

## 🐛 KNOWN ISSUES (Document on itch.io)

**Alpha limitations to mention:**
- Windows-only (Linux/Mac planned)
- Single difficulty level (no easy/hard modes yet)
- Graphics mode optional (ASCII is primary)
- No tutorial scenario (help menu is comprehensive)

---

## ✨ OPTIONAL ENHANCEMENTS (Not Blocking)

- [ ] Create cover image for itch.io (315x250 or 630x500)
- [ ] Create banner image (960x540)
- [ ] Record 10-second GIF of gameplay
- [ ] Take 5 screenshots:
  1. Main menu
  2. Stealth gameplay (hiding in shadows)
  3. Combat encounter
  4. Lore/Fragments screen
  5. Inventory screen
- [ ] Write CHANGELOG.md
- [ ] Create Credits screen (mention TCOD, pygame)

---

## 🚀 ESTIMATED TIME TO RELEASE

- **Fix config files:** 15 minutes (DONE)
- **Test EXE:** 30 minutes
- **Update screenshots (pixel explosion + queue arrows):** 30 minutes
- **Package for itch.io:** 30 minutes
- **Create itch.io page:** 30 minutes
- **Post to Reddit:** 15 minutes

**Total: ~2.5 hours** (assuming no major bugs found during testing)

---

## 📋 POST-RELEASE MONITORING

**First 24 hours:**
- Monitor itch.io comments
- Respond to Reddit questions
- Check for crash reports
- Note common feedback themes

**First week:**
- Collect survey responses
- Prioritize bug fixes
- Plan balance tweaks based on feedback
- Consider posting to r/roguelikes if initial reception is good

---

## 🎯 SUCCESS METRICS

**Alpha goals:**
- 50+ downloads in first week
- 10+ pieces of feedback (survey or comments)
- No game-breaking bugs reported
- At least 3 people complete all 3 levels

**Feedback priorities:**
1. Game-breaking bugs (fix immediately)
2. Balance issues (note for v0.9.0)
3. UX confusion (clarify in README or help menu)
4. Feature requests (consider for v1.0)

---

## 🚨 TCOD 19.6.0 UPDATE VERIFICATION (Added Nov 8)

**Update completed:**
- [x] Updated from 19.4.0 → 19.6.0
- [x] All 852 unit tests pass
- [x] Game launches successfully in dev environment
- [x] Graphics look good with new nearest-neighbor scaling

**Still required before release:**
- [ ] **Test the actual EXE build** (not just dev environment!)
- [ ] Verify scaling looks good in built EXE
- [ ] No visual regressions in graphics or ASCII modes
- [ ] Confirm controller crash fix doesn't affect non-controller gameplay

**What changed in 19.6.0:**
- Nearest-neighbor scaling is now default (sharper graphics - good for roguelikes!)
- Fixed controller event crash (even though we don't use controllers yet)
- Fixed key symbol regression (lowercase keys)
- Updated to libtcod 2.2.1
