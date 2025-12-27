# Pre-Release Checklist for Beta 0.9.0

## 📝 PRE-BUILD PREPARATION

### 1. **Update Documentation**

- [ ] Review and update CHANGELOG.md with all changes since last release
- [ ] Update itch.io page content (marketing/itch_io_page.html) with new features
- [ ] Sync wiki pages with game data (achievements, exploits, enemies, keybindings)
- [ ] Update version numbers in README files
- [ ] Verify all URLs are correct (grep for discord.gg, itch.io - don't hallucinate!)

---

## 🧪 TESTING

### 2. **Test the EXE**

**Basic functionality:**
- [ ] Test on clean Windows 10/11 system (no Python installed)
- [ ] Verify all config files load correctly
- [ ] Play through one complete run (all 3 levels)
- [ ] Test save/load functionality
- [ ] Verify permadeath deletes save
- [ ] Check all 13 exploits work correctly
- [ ] Verify keybindings (I=Inventory, L=Look, F=Fragments, ?=Help, V=Achievements, N=Ascension)

**Audio verification:**
- [ ] Test all 13 exploit sounds play correctly
- [ ] Verify music tracks load and loop
- [ ] Check Logic Bomb sound (logic_bomb.wav) plays

**Debug tools work in EXE:**
- [ ] Shift+F12 creates debug package
- [ ] Settings > Export Debug Package works
- [ ] Verify package includes saves/logs/metrics from data directory
- [ ] Package created in [data directory]/debug_exports/

**Achievement system:**
- [ ] Unlock an achievement and verify it persists
- [ ] Check achievement popups display correctly
- [ ] Verify progress tracking works across deaths

**Edge cases:**
- [ ] Test Admin Avatar spawns when trace hits 100%
- [ ] Verify permadeath deletes save file completely
- [ ] Test look mode (L key) mouse and keyboard interaction
- [ ] Check fragments screen (F key) displays all discovered lore

### 3. **Test Gamepad Support (NEW in 0.9.0)**

**Controller connection:**
- [ ] Test Xbox controller connects and is recognized
- [ ] Test PlayStation controller connects (if available)
- [ ] Verify hotplug works (connect/disconnect during gameplay)

**Gameplay controls:**
- [ ] Left stick/D-pad movement works with proper time-gating
- [ ] Right stick auto-look mode works
- [ ] LB/RB cycle through exploits
- [ ] RT fires selected exploit
- [ ] A=wait, B=cancel, Y=inventory, Start=menu, Select=help

**Menu navigation:**
- [ ] D-pad/stick navigates menus
- [ ] A=confirm, B=back works consistently
- [ ] LB/RB page through achievements/help

**Control remapping:**
- [ ] Settings > Controls > Gamepad Bindings accessible
- [ ] Can rebind gamepad buttons
- [ ] Bindings persist after restart

### 4. **Test Ascension System (NEW in 0.9.0)**

- [ ] Complete a run to unlock Ascension
- [ ] Press N to open Ascension viewer
- [ ] Verify unlock popup appears on first unlock
- [ ] Test A1 modifier (Scanner Vision +1)
- [ ] Verify Ascension level persists across runs
- [ ] Check Ascension achievements unlock at A5/A10/A15/A20

### 5. **Test Linux/Steam Deck (NEW in 0.9.0)**

- [ ] Test on Linux Mint (or Ubuntu)
- [ ] Verify Steam Deck detection works (if available)
- [ ] Test UI Scale setting (compact mode)
- [ ] Test Music Boost setting
- [ ] Verify gamepad works on Linux

### 6. **Create backup before packaging**

- [ ] Copy entire `dist/` folder to `dist_backup_v0.9.0/`
- [ ] Commit current state to git
- [ ] Tag release: `git tag v0.9.0-beta`
- [ ] Push to GitHub: `git push origin v0.9.0-beta`

### 7. **Test new player experience**

- [ ] Delete `user_settings.json` and test fresh start
- [ ] Verify intro dialogue appears
- [ ] Check help menu (?) is comprehensive - verify gamepad page (Page 4)
- [ ] Ensure first death shows feedback link clearly

---

## 📦 PACKAGING FOR ITCH.IO

### 8. **Prepare release package** (AUTOMATED)

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
copy releases\RogueSignalProtocol_beta_2025-12-27.zip releases\RogueSignalProtocol_v0.9.0_Beta.zip
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

- [ ] Upload .zip package (Windows and Linux builds)
- [ ] Update page description from `marketing/itch_io_page.html` (copy HTML content)
- [ ] Post devlog from `marketing/itch_090_beta_announcement.md`
- [ ] Update screenshots if needed (gamepad controls, ascension UI)
- [ ] Set tags: roguelike, stealth, cyberpunk, turn-based, permadeath, controller-support
- [ ] Mark as "Beta - In Development"

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

### 11. **Feedback collection** - COMPLETED

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

**Beta limitations to mention:**
- Windows and Linux only (no macOS yet)
- Ascension system provides difficulty scaling (no easy mode)
- Graphics mode optional (ASCII is primary)
- No tutorial scenario (help menu is comprehensive)
- Steam Deck support is experimental

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
- [X] Write CHANGELOG.md
- [ ] Create Credits screen (mention TCOD, pygame)
- [ ] Update screenshots to show gamepad controls/ascension UI

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

**Beta goals:**
- 100+ downloads in first week
- 15+ pieces of feedback (survey or comments)
- No game-breaking bugs reported
- At least 5 people complete all 3 levels
- At least 2 people try Ascension mode

**Feedback priorities:**
1. Game-breaking bugs (fix immediately)
2. Gamepad/controller issues (high priority for 0.9.x)
3. Balance issues (note for v1.0)
4. UX confusion (clarify in README or help menu)
5. Feature requests (consider for v1.0)

---
