# Pre-Release Checklist for Alpha 0.8.0

```

### 7. **Test the EXE**

**Basic functionality:**
- [X] Test on clean Windows 10/11 system (no Python installed)
- [X] Verify all config files load correctly
- [X] Play through one complete run (all 3 levels)
- [X] Test save/load functionality
- [X] Verify permadeath deletes save
- [X] Check all 13 exploits work correctly
- [X] Verify keybindings (I=Inventory, L=Look, F=Fragments, ?=Help, V=Achievements)

**CRITICAL: Test with TCOD 19.6.0 changes:**
- [X] Verify nearest-neighbor scaling looks good (graphics sharper, not broken)
- [X] Verify graphics mode toggle in Settings menu works

**Audio verification:**
- [X] Test all 13 exploit sounds play correctly
- [X] Verify music tracks load and loop
- [X] Check Logic Bomb sound (logic_bomb.wav) plays

**Debug tools work in EXE:**
- [X] Shift+F12 creates debug package
- [X] Settings > Export Debug Package works
- [X] Verify package includes saves/logs/metrics from data directory
- [X] Package created in [data directory]/debug_exports/

**Achievement system:**
- [X] Unlock an achievement and verify it persists
- [X] Check achievement popups display correctly
- [X] Verify progress tracking works across deaths

**Edge cases:**
- [X] Test Admin Avatar spawns when trace hits 100%
- [X] Verify permadeath deletes save file completely
- [X] Test look mode (L key) mouse and keyboard interaction
- [X] Check fragments screen (F key) displays all discovered lore

### 7.5 **Create backup before packaging**

- [X] Copy entire `dist/` folder to `dist_backup_v0.8.0/`
- [X] Commit current state to git
- [X] Tag release: `git tag v0.8.0-alpha`
- [X] Push to GitHub: `git push origin v0.8.0-alpha`

### 7.6 **Test new player experience**

- [X] Delete `user_settings.json` and test fresh start
- [X] Verify intro dialogue appears
- [X] Check help menu (?) is comprehensive
- [X] Ensure first death shows feedback link clearly

---

## 📦 PACKAGING FOR ITCH.IO

### 8. ✅ **Prepare release package** - COMPLETED (AUTOMATED)

**The build script already does this!**

```bash
# Run the build script (creates everything automatically)
build\build.bat alpha
```

**What it creates:**
- `dist/` - Executable + all assets
- `releases/RogueSignalProtocol_alpha_YYYY-MM-DD.zip` - Ready-to-upload package

**VERIFIED:** Build script exists at `build/build.bat`, releases folder contains recent builds including RogueSignalProtocol_alpha_2025-11-07.zip

**Optional: Rename for version-based naming:**
```bash
# If you prefer version-based naming over date-based:
copy releases\RogueSignalProtocol_alpha_2025-11-08.zip releases\RogueSignalProtocol_v0.8.0_Alpha.zip
```

**Verify the zip contains:**
- [X] RogueSignalProtocol.exe
- [X] All .json config files (game_content, game_rules, narrative_content, graphics_tiles)
- [X] KreativeSquare.ttf font
- [X] README.txt and LICENSE
- [X] graphics/ folder (includes main_menu backgrounds)
- [X] sound/ folder
- [X] music/ folder
- [X] debug_mode.flag (alpha builds only)

### 9. **Prepare itch.io page**

- [X] Upload .zip package
- [X] Copy content from `marketing/itch_io_page_draft.md`
- [X] Add 3-5 screenshots (gameplay, menus, lore)
- [X] Set tags: roguelike, stealth, cyberpunk, turn-based, permadeath
- [X] Set price: Pay what you want ($0 minimum)
- [X] Mark as "Alpha - In Development"

### 9.5 **Update and verify screenshots** - PARTIALLY COMPLETED

**VERIFIED:** 4 screenshots exist in `marketing/screenshots/` from 2025-11-08:
- Screenshot 2025-11-08 085132.png (1.4M)
- Screenshot 2025-11-08 085255.png (382K)
- Screenshot 2025-11-08 085441.png (6.0M)
- Screenshot 2025-11-08 102149.png (580K)

**Still need manual verification:**
- [X] **Verify screenshots show pixel explosion effect** (graphics mode)
- [X] **Verify screenshots show queue arrows** (the new directional arrow system)
- [X] Verify images show both ASCII and graphics modes
- [X] Ensure one screenshot shows the enemy movement queue UI clearly
- [X] Consider if additional shots needed: gameplay, inventory, lore/fragments screen, death screen with feedback link

### 9.6 **Record new MP4 video for Reddit**

**CRITICAL - Reddit engagement booster:**
- [X] **Record new MP4 video showcasing gameplay** (10-15 seconds)
- [X] Show key features: movement queue arrows, pixel explosions, stealth mechanics
- [X] Keep file size reasonable for Reddit upload (<100 MB)
- [X] Consider showing: player hiding in blind spot → enemy moves past → player escapes
- [X] Test video plays correctly on Reddit before posting

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

---

## 🐛 KNOWN ISSUES (Document on itch.io)

**Alpha limitations to mention:**
- Windows-only 
- Single difficulty level (no easy/hard modes yet)
- Graphics mode optional (ASCII is primary)
- No tutorial scenario (help menu is comprehensive)

---

## ✨ OPTIONAL ENHANCEMENTS (Not Blocking)

- [ ] **Create question mark sprite for last known enemy positions** (graphics/questionmark01.png)
  - Currently missing in graphics mode (works in glyph mode with '?' character)
  - Should be 64x64 pixel sprite to match other tiles
  - Color: dimmed/ghostly to indicate uncertainty
  - Used to mark where player last saw an enemy that's no longer visible
- [X] Create cover image for itch.io (315x250 or 630x500)
- [X] Create banner image (960x540)
- [X] Record 10-second GIF of gameplay
- [X] Take 5 screenshots:
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
- **Record new MP4 video for Reddit:** 20 minutes
- **Package for itch.io:** 5 minutes (automated by build script!)
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
