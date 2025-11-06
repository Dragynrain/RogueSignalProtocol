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
* **21 story fragments** revealing a dark conspiracy about uploading human minds to networks
* **8 enemy types** with unique behaviors (static guards, patrols, hunters, viruses, inhibitors)
* **12 exploits** across combat, stealth, and utility categories
* **Dual rendering modes** - Classic ASCII or graphical sprites
* **Full audio design** - atmospheric music and 40+ sound effects

### What Makes It Different:
The stealth mechanics are central - you're not meant to fight everything. High detection (trace level) spawns an Admin Avatar boss that hunts you relentlessly. Heat management from exploit usage adds another resource layer beyond typical HP/mana.

The story is told through environmental fragments you discover - each run might reveal new pieces of the Project Chimera conspiracy, even if you die. Permadeath for your character, but persistent narrative discovery.

### Where to Get It:
**Itch.io:** [INSERT LINK]
**Source Code:** https://github.com/Dragynrain/RogueSignalProtocol
**Feedback Survey:** [INSERT GOOGLE FORM LINK]

This is **alpha 0.8.0** - feature complete and playtested, now looking for wider feedback on:
* How the stealth/combat balance feels
* Whether difficulty progression feels fair across the 3 levels
* Any bugs or edge cases I missed
* Overall fun factor and replayability

---

## The AI Development Workflow

I want to be transparent: this is a **solo dev project built using AI tools** across code, art, and audio. I think the results speak for themselves, but there are interesting lessons for other indie devs.

### Tools Used:

**Claude Code** - ~95% of codebase, 1580 automated tests, architectural decisions
**Stable Diffusion** - All sprite prototypes (~50+ assets, heavily curated)
**AudioCraft** - Placeholder sound effects (music is human-made from free libraries)

### What Worked:

**Rapid Prototyping** - This is AI's killer feature. Going from "what if enemies showed their next 3 moves?" to *playing it* and feeling if it's fun took minutes instead of days. Fail fast on bad ideas, polish the good ones.

**Development Speed** - 2-3 months instead of 6-12 months for a solo project of this scope.

### What Didn't Work:

**Curation Required** - 95%+ rejection rate on generated assets. AI doesn't have taste - you still need creative direction and lots of manual polish.

**Asset Quality** - The sprites and SFX work for alpha testing, but lack the polish that human artists bring. I recognize these limitations.

**Ethical Complexity** - I'm aware of the concerns around AI training data and impact on creative professionals. These are legitimate issues.

### The Bottom Line:

AI amplified my capabilities but didn't replace game design. Every mechanic, balance decision, and curated asset came from human judgment. The tools compressed the timeline while I focused on making it fun.

**The game has to be good.** If it's not fun, being "AI-assisted" won't save it. And if it IS fun, being "AI-assisted" shouldn't disqualify it. Try it and judge for yourself.

---

### Open to Collaboration

If you're an artist or sound designer interested in improving the game's visuals or audio, I'd love to hear from you! The AI-generated assets serve as functional placeholders, but I'm absolutely open to working with human creators who want to contribute to the project. Reach out if you're interested.

---

**Technical Details:**
* Windows-only for now (standalone EXE, ~30 MB download)
* Built with Python + TCOD
* Runs take 10-20 minutes for full 3-level campaign
* Free and open source (GPL v3)

Would love to hear thoughts from other devs on AI workflows, and feedback from players on the game itself!

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
