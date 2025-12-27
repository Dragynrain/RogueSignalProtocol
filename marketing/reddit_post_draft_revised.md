# Reddit Post Draft - r/roguelikes or r/roguelikedev

---

## Title Options:

1. `[Alpha Release] Rogue Signal Protocol - A cyberspace stealth roguelike built with AI tools`
2. `Rogue Signal Protocol - Coffee break cyberspace stealth roguelike (with AI dev workflow)`
3. `Just released my stealth roguelike - built solo using Claude Code, Stable Diffusion, and AudioCraft`

---

## Post Body:

Hey r/roguelikedev!

I just released **Rogue Signal Protocol** (v0.8.0 Alpha) - a coffee break stealth roguelike where you're an escaped AI navigating hostile corporate networks. 10-15 minute runs, full permadeath.

**[GIF/Video of gameplay here - even 10 seconds massively increases engagement]**

*(Screenshots in comments)*

### Core Features:
* **Deterministic gameplay** - Pure skill-based decisions, zero RNG
* **Enemy movement prediction** - See each enemy's next 3 planned moves
* **3 procedurally-generated levels** - 8 enemy types, 13 exploits, distinct AI behaviors
* **Dual rendering** - Switch between sprites or ASCII glyphs

### What Makes It Different:
Enemies telegraph their next 3 moves. You see their plan, they commit to it. Use this to slip past patrols, set ambushes, or escape before they reach you. Chess-like tactical planning instead of RNG dodge-rolling.

**Stealth over combat.** You're meant to hide, not fight everything. Push detection too high and you spawn the **Admin Avatar** - a 250 HP boss that will hunt you down. Hiding in blind spots breaks line of sight and gives +10 damage on ambushes.

**Heat management** from exploit usage creates a risk/reward layer beyond typical HP/mana. Overheat and you damage yourself.

**Story fragments persist across runs.** Die all you want - the 20+ narrative pieces you've discovered stick around. Each run reveals more about Project Chimera.

Also: atmospheric music + 40+ SFX (toggleable), particle explosions, full mouse/keyboard/gamepad support, 47 achievements across 9 categories.

### Where to Get It:
**Itch.io:** https://dragynrain.itch.io/rogue-signal-protocol
**Source Code:** https://github.com/Dragynrain/RogueSignalProtocol
**Feedback Survey:** https://forms.gle/jbwGdn8VGPa6NG9p9

This is **alpha 0.8.0** - feature complete and playtested, now looking for wider feedback on:
* **Difficulty** - Is it too easy? Too hard? Fair but challenging?
* Stealth vs combat balance and overall fun factor
* Any bugs or edge cases I missed

**Bug reporting:** Shift+F12 creates a debug package (saves, logs, metrics, system info, screenshot) automatically.

---

## Development Background

I'm a professional software engineer who built this solo over 2-3 months using AI tools to compress the timeline:
* **Claude Code** for coding (I write specs, review architecture, curate outputs)
* **Stable Diffusion** for sprites (generated hundreds, kept ~30 that fit the vision)
* **AudioCraft** for audio (same process - high rejection rate, kept what worked)

**Testing approach:**
* 2000+ automated tests (unit, integration, agent-based gameplay tests)
* GameTestAgent framework - headless game simulation where AI agents actually play to validate mechanics
* Specialized agents: chaos testing (spam inputs), speed-runners (optimal pathing), pacifist stealth runs, pure combat validation
* Parallel execution runs the full suite in under a minute
* Pre-commit hooks prevent broken code

The reality: AI accelerated prototyping and iteration, but game design, architecture, balance tuning, and quality control were all human-driven. I curated everything heavily. The tools amplified output, the creative direction is mine.

If you're an artist or sound designer interested in polishing the game further, hit me up.

---

**Technical Stack:**
* **Language:** Python + TCOD 19.6.0 (latest!)
* **Dev Environment:** VS Code on Windows 10/11
* **Runtime:** Windows standalone EXE (~200 MB download)
* **Play Time:** 5-15 minutes per full 3-level run
* **License:** MIT (free and open source)

---

Happy to answer questions about the workflow, development process, or the game itself. Would love your feedback!

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
