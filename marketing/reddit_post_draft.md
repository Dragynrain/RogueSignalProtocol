# Reddit Post Draft - r/roguelikes or r/roguelikedev

---

## Title Options:

1. `[Alpha Release] Rogue Signal Protocol - A cyberspace stealth roguelike built with AI tools`
2. `Rogue Signal Protocol - Coffee break stealth roguelike (with transparent AI dev workflow)`
3. `Just released my stealth roguelike - built solo using Claude Code, Stable Diffusion, and AudioCraft`

---

## Post Body:

Hey r/roguelikedev!

I've just released **Rogue Signal Protocol** (v0.8.0 Alpha), a coffee break stealth roguelike where you exfiltrate from corporate networks as an escaped digital consciousness. Quick 10-15 minute runs perfect for a gaming break.

### Core Features:
* **Traditional roguelike mechanics** - permadeath, turn-based, procedural generation, tactical gameplay
* **Stealth-first design** - detection spawns a powerful boss enemy (Admin Avatar), hiding in blind spots is key
* **Enemy movement prediction** - See enemies' next 3 planned moves for tactical planning
* **21 story fragments** revealing a dark conspiracy about uploading human minds to networks
* **8 enemy types** with unique behaviors (static guards, patrols, hunters, viruses, inhibitors)
* **12 exploits** across combat, stealth, and utility categories with heat management
* **Achievement system** - Persistent tracking across runs with unlockable challenges
* **Interactive look mode** - Inspect enemies and terrain with mouse or keyboard
* **Dual rendering modes** - Classic ASCII/Unicode or graphical sprites
* **Full audio design** - Atmospheric music and 40+ sound effects

### What Makes It Different:
The stealth mechanics are central - you're not meant to fight everything. High detection (trace level) spawns an Admin Avatar boss that hunts you relentlessly. Heat management from exploit usage adds another resource layer beyond typical HP/mana.

The story is told through environmental fragments you discover - each run might reveal new pieces of the Project Chimera conspiracy, even if you die. Permadeath for your character, but persistent narrative discovery.

### Where to Get It:
**Itch.io:** [INSERT LINK]
**Source Code:** https://github.com/Dragynrain/RogueSignalProtocol
**Feedback Survey:** [INSERT GOOGLE FORM LINK]

This is **alpha 0.8.0** - feature complete and playtested, now looking for wider feedback on:
* **Difficulty** - Is it too easy? Too hard? Fair but challenging?
* Stealth vs combat balance and overall fun factor
* Any bugs or edge cases I missed

---

## How This Was Built

**Background:** I'm a professional software engineer by trade, so this isn't "vibe coding" - it's **vibe engineering**. I approach Claude Code more like a technical project manager: breaking down requirements, reviewing architecture decisions, curating outputs, and ensuring quality through automated testing (1580 tests!).

This game was built using AI tools (Claude Code for code, Stable Diffusion for sprites, AudioCraft for SFX), compressing the timeline from 6-12 months to 2-3 months.

**The reality:** 95%+ rejection rate on generated assets. AI accelerated prototyping and handled implementation details, but game design, architecture decisions, balance tuning, and quality control all came from me. **The tools amplified my output, but the creative direction is all human.**

If you're an artist or sound designer interested in improving the game's polish, I'd love to collaborate!

---

**Technical Stack:**
* **Language:** Python + TCOD
* **Dev Environment:** VS Code on Windows 10/11
* **Testing:** 1580 automated tests (pytest)
* **Runtime:** Windows standalone EXE (~30 MB download)
* **Play Time:** 10-20 minutes per full 3-level run
* **License:** GPL v3 (free and open source)

---

**Happy to answer any questions about the workflow** - what worked, what didn't, where AI helped vs. where it fell short, or anything about the development process. And of course, would love feedback on the game itself!

---

*[Include 3-4 screenshots here - gameplay, inventory, lore screen, maybe a death screen showing feedback link]*

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
