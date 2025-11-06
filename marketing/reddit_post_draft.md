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

This is **alpha 0.8.0** - all content is implemented, but I'm looking for feedback on:
* Balance and difficulty curve
* Stealth vs combat feel
* Heat/trace management depth
* Overall progression pacing

---

## The AI Development Workflow

I want to be transparent about how this game was built - this is a **solo dev project built almost entirely using AI tools** across every aspect of development. I think the results speak for themselves, but there are interesting lessons here for other indie devs.

### Tools Used:

**Claude Code (Anthropic)** - Primary development partner
* Wrote ~95% of the codebase through conversational iteration
* Architectural decisions, refactoring, testing, debugging
* Real-time problem solving as issues emerged
* 1580 automated tests, all maintained by Claude

**Stable Diffusion** - All graphical sprites
* Generated base sprites for all enemies, items, environmental objects
* Iterated on style and consistency across ~50+ unique sprites
* Curated and integrated into dual-rendering system (ASCII + graphics modes)

**AudioCraft (Meta)** - Prototype sound effects
* Generated 40+ SFX for movement, combat, UI interactions as placeholders
* All curated and balanced for gameplay feel
* (Note: Background music is human-made, sourced from free-use libraries)

### What Worked (Pros):

**Development Speed:** What would have taken me 6-12 months solo took ~2-3 months of active development. Claude Code handled the tedious parts (testing, refactoring, JSON config systems) while I focused on design.

**Quality Control:** Having AI-generated tests meant every feature was validated. 1580 passing tests gave me confidence to iterate rapidly without breaking things.

**Iteration Velocity:** "I want enemies to show their next 3 moves" → implemented and tested in minutes. Rapid prototyping meant more time polishing mechanics.

**Asset Generation:** Rapidly prototype graphics and audio to experiment with styles and features. Stable Diffusion let me visualize my cyberspace aesthetic and iterate on visual direction. AudioCraft provided placeholder sound effects to test gameplay feel.

### What Didn't Work (Cons):

**Creative Direction Required:** AI tools don't have taste. I had to reject 95%+ of generated sprites and audio until finding the right fit. You still need vision and curation.

**Integration Overhead:** Generated assets don't drop into your game magically. Sprite sizing, color palettes, audio balancing - all manual curation.

**AI Limitations:** Claude Code occasionally introduced bugs or forgot architectural decisions. I had to maintain vigilance and do code reviews. Not autopilot.

**Asset Quality:** AI-generated assets are functional placeholders, but they lack the polish and intentionality that human artists bring. The sprites and sound effects work for alpha testing, but I recognize their limitations.

**Ethical Complexity:** I'm aware of the concerns around AI training data and its impact on creative professionals. These are legitimate issues the industry is still grappling with.

### The Bottom Line:

AI **amplified my capabilities, but didn't replace game design**. I made every design decision, balanced every mechanic, curated every asset, and iterated based on gameplay feel. The tools let me execute faster, but the creative vision is mine.

I'm sharing this workflow because I think it's the future for solo indie devs. The traditional path (learn to code, learn to art, learn to audio) is a 5+ year journey. AI tools compressed that timeline while keeping quality high.

**But the game has to be good.** If it's not fun, being "AI-assisted" won't save it. And if it IS fun, being "AI-assisted" shouldn't disqualify it.

Try it and judge for yourself.

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
