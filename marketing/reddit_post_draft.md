# Reddit Post Draft - r/roguelikes or r/roguelikedev

---

## Title Options:

1. `[Alpha Release] Rogue Signal Protocol - A cyberspace stealth roguelike built with AI tools`
2. `Rogue Signal Protocol - Coffee break cyberspace stealth roguelike (with AI dev workflow)`
3. `Just released my stealth roguelike - built solo using Claude Code, Stable Diffusion, and AudioCraft`

---

## Post Body:

Hey r/roguelikedev!

I've just released **Rogue Signal Protocol** (v0.8.0 Alpha), a coffee break stealth roguelike where you exfiltrate from corporate networks as an escaped digital consciousness. Quick 10-15 minute runs perfect for a gaming break.

**[GIF/Video of gameplay here - even 10 seconds massively increases engagement]**

*(Screenshots in comments)*

### Core Features:
* **Traditional roguelike mechanics** - permadeath, turn-based, procedural generation, tactical gameplay
* **Stealth-first design** - detection spawns a powerful boss enemy (Admin Avatar), hiding in blind spots is key
* **Enemy movement prediction** - See enemies' next 3 planned moves for tactical planning
* **20+ story fragments** revealing a dark conspiracy about uploading human minds to networks
* **8 enemy types** with unique behaviors (static guards, patrols, hunters, viruses, inhibitors)
* **13 exploits** across combat, stealth, and utility categories with heat management
* **Achievement system** - Persistent tracking across runs with unlockable challenges
* **Interactive look mode** - Inspect enemies and terrain with mouse or keyboard
* **Dual rendering modes** - Switch between graphical sprites or classic ASCII/Unicode glyphs
* **Full audio design** - Atmospheric music and 40+ sound effects

### What Makes It Different:
**Enemy movement prediction** shows you the next 3 planned moves - no guessing, pure tactical planning. It's like playing chess against enemies who show their next moves.

The stealth mechanics are central - you're not meant to fight everything. High detection (trace level) spawns an Admin Avatar boss that hunts you relentlessly. Heat management from exploit usage adds another resource layer beyond typical HP/mana.

The story is told through environmental fragments you discover - each run might reveal new pieces of the Project Chimera conspiracy, even if you die. Permadeath for your character, but persistent narrative discovery.

### Where to Get It:
**Itch.io:** https://dragynrain.itch.io/rogue-signal-protocol
**Source Code:** https://github.com/Dragynrain/RogueSignalProtocol
**Feedback Survey:** https://forms.gle/jbwGdn8VGPa6NG9p9

This is **alpha 0.8.0** - feature complete and playtested, now looking for wider feedback on:
* **Difficulty** - Is it too easy? Too hard? Fair but challenging?
* Stealth vs combat balance and overall fun factor
* Any bugs or edge cases I missed

**Bug reporting made easy:** Hit Shift+F12 or use Settings > Export Debug Package to create a comprehensive debug report (saves, logs, metrics, system info, screenshot). Makes bug reporting super simple!

---

## How This Was Built

**Background:** I'm a professional software engineer, so this was built with engineering discipline: architecture reviews, code quality standards, and comprehensive automated testing. I approach Claude Code more like a technical project manager: breaking down requirements, reviewing architecture decisions, curating outputs, and ensuring quality.

This game was built using AI tools (Claude Code for code, Stable Diffusion for sprites and images, AudioCraft for SFX), compressing the timeline from 6-12 months to 2-3 months.

**Testing approach:** Beyond typical unit tests, I built a **GameTestAgent framework** - headless AI agents that actually play the game to validate mechanics. These include chaos agents that spam random inputs to find edge cases, speed-running agents to test optimal pathing, and pacifist stealth agents to ensure non-combat paths remain viable. They catch mechanical bugs and edge cases that might not surface in manual playtesting.

**The reality:** I approached asset generation with high quality control - only keeping outputs that met the game's design vision. AI definitely accelerated the prototyping and iteration cycles, but game design, architecture, balance tuning, and quality standards were all human-driven. **The tools amplified my output, but the creative direction is all human.**

If you're an actual artist or actual sound designer interested in improving the game's polish, I'd love to collaborate. Reach out!

---

**Technical Stack:**
* **Language:** Python + TCOD 19.6.0 (latest!)
* **Dev Environment:** VS Code on Windows 10/11
* **Testing:** Automated test suite with GameTestAgent framework (AI agents that play the game headless to validate mechanics)
* **Runtime:** Windows standalone EXE (~200 MB download)
* **Play Time:** 5-15 minutes per full 3-level run
* **License:** MIT (free and open source)

---

**Happy to answer any questions about the workflow** - what worked, what didn't, where AI helped vs. where it fell short, or anything about the development process. And of course, would love feedback on the game itself!

---

*[Post 3-4 screenshots in comments after submitting - gameplay, inventory, lore screen, maybe a death screen showing feedback link]*

---

## Posting Strategy:

**Target Subreddit:** r/roguelikedev (more dev-focused, better reception for AI transparency)
**Alternative:** r/roguelikes (if roguelikedev goes well, cross-post 1 week later)

**Best Practices:**
* **Include:** 3-4 screenshots showing ASCII mode, graphics mode, and gameplay
* **Respond actively** to comments in first 2-3 hours (critical for visibility)
* **Acknowledge criticism** about AI respectfully - don't get defensive
* **Emphasize the game first** - "try it and judge for yourself"
* **Be ready for:** Both fascinated developers asking workflow questions AND immediate "AI slop" dismissals

**What to Expect:**
* Some devs will be genuinely curious about the workflow
* Some players will refuse to try it based on AI mention alone
* Could get picked up by gaming news sites (good or bad coverage)
* Likely to spark debate in comments (engagement = visibility)

**If It Goes Badly:**
* Don't delete the post - own it
* Learn from the feedback
* Consider making a "lessons learned" follow-up post

**If It Goes Well:**
* Engage with everyone asking workflow questions
* Consider doing an AMA or detailed dev blog
* This could become a case study for AI-assisted indie dev
