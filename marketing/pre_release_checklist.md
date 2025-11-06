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

### 1. **Create Logic Bomb sound effect**

**PROBLEM:** Logic Bomb exploit uses placeholder sound (needs dedicated sound file)

**ACTION REQUIRED:**
- Create `exploit_logic_bomb.wav` in sound/ folder
- Should sound like a digital explosion/cascade
- See game_combat.py:595 for reference

---

### 2. **Update dist/ folder with current config files**

**PROBLEM:** The `dist/` folder has **OUTDATED** config files!

```bash
# Current state:
dist/game_data.json    <- OLD version (has "EMP Burst", wrong exploit names)
dist/game_config.json  <- Has outdated welcome message "Press 'L' to view discovered lore"

# Should be:
game_content.json      <- CURRENT version (correct exploits, balance)
game_rules.json        <- CURRENT game rules
```

**ACTION REQUIRED:**
```bash
# Update dist folder with current configs
cp game_content.json dist/game_data.json
cp game_rules.json dist/
cp graphics_tiles.json dist/
cp story_content.json dist/ # (might already be correct)

# Verify game_config.json in dist has correct keybindings
```

**Why this matters:** Players will experience different game balance and broken features if using old config files!

---

### 3. **Fix welcome message in dist/game_config.json**

Line 164 says:
```json
"Press 'L' to view discovered lore"
```

Should be:
```json
"Press 'F' to view discovered lore"
```

---

## ⚠️ IMPORTANT - Should Do Before Release

### 4. **Clean up leftover files**
```bash
# Delete development artifacts
rm game_debug.log
rm graphic-preview.log
rm nul

# Archive scratch code
mkdir .archive
mv preview_layout_new.py .archive/
```

### 5. **Update README.md keybindings**

Line 68 in README.md says:
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

- [ ] Test on clean Windows 10/11 system (no Python installed)
- [ ] Verify all config files load correctly
- [ ] Play through one complete run (all 3 levels)
- [ ] Test save/load functionality
- [ ] Verify permadeath deletes save
- [ ] Check all 12 exploits work correctly
- [ ] Verify keybindings (L=Look, F=Fragments, ?=Help)

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

### 11. **Feedback collection**

- [ ] Create Google Form from `marketing/feedback_survey_draft.md`
- [ ] Add link to itch.io page
- [ ] Add link to README.txt

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

- **Fix config files:** 15 minutes
- **Test EXE:** 30 minutes
- **Package for itch.io:** 30 minutes
- **Create itch.io page:** 30 minutes
- **Screenshots:** 20 minutes
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
