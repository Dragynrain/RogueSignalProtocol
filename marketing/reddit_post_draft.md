# Reddit Post Draft - r/roguelikes or r/roguelikedev

---

## Title Options:

1. `[Alpha Release] Rogue Signal Protocol - A cyberspace stealth roguelike built with AI tools`
2. `Rogue Signal Protocol - Coffee break cyberspace stealth roguelike (with AI dev workflow)`
3. `Just released my stealth roguelike - built solo using Claude Code, Stable Diffusion, and AudioCraft`

---

## Post Body:

Hey r/roguelikedev!

I've just released **Rogue Signal Protocol** (v0.8.0 Alpha), a traditional turn-based coffee break stealth roguelike where you play as an escaped digital consciousness navigating hostile corporate networks. Quick 10-15 minute runs with permadeath - each death teaches lessons, each run reveals more truth.

**[GIF/Video of gameplay here - even 10 seconds massively increases engagement]**

*(Screenshots in comments)*

### Core Features:
* **Deterministic gameplay (no RNG)** - Pure skill-based tactical decisions, no luck involved
* **Enemy movement prediction** - See each enemy's next 3 planned moves for tactical planning
* **3 procedurally-generated network levels** with 8 unique enemy types, 13 exploits, and distinct AI behaviors
* **Dual rendering modes** - Switch between graphical sprites or classic ASCII glyphs

### What Makes It Different:
**Enemy movement prediction** shows you each enemy's next 3 planned moves - no guessing, pure tactical planning. It's like playing chess against enemies who show their next moves. Use this intel to slip past patrols, set up ambushes, or plan your escape route.

The **stealth mechanics** are central - you're not meant to fight everything. Hide in blind spots to avoid detection and manage your heat levels carefully. Push your detection too high and the **Admin Avatar** spawns - a powerful boss with perfect tracking and relentless pursuit.

**Heat management** from exploit usage adds another resource layer beyond typical HP/mana. Every move counts in this purely skill-based tactical challenge.

The **story is told through environmental fragments** - 20+ story fragments persist across runs, even death can't erase them. Each run might reveal new pieces of the Project Chimera conspiracy. Permadeath for your character, but persistent narrative discovery means every run brings you closer to the truth.

The game features full audio design with atmospheric music and 40+ sound effects (toggleable), particle effect explosions for visual feedback, and complete keyboard and mouse support. Track your progress across runs with the **Achievement System** - unlock challenges and prove your mastery of stealth tactics.

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

**Testing Infrastructure:**
* **2000+ automated tests** - 1000+ unit tests, 1000+ integration tests, 50+ agent-based gameplay tests
* **GameTestAgent framework** - Headless game simulation where AI agents actually play the game to validate mechanics
* **Specialized test agents:** Chaos agents (spam random inputs to find edge cases), speed-running agents (test optimal pathing), pacifist stealth agents (ensure non-combat paths remain viable), barbarian agents (pure combat validation)
* **Parallel test execution** with custom per-worker file isolation - runs the full suite in under a minute
* **Automated regression testing** - Pre-commit hooks prevent broken code from entering the repository
* Catches mechanical bugs and edge cases that might not surface in manual playtesting

**The reality:** I approached asset generation with high quality control - only keeping outputs that met the game's design vision. AI definitely accelerated the prototyping and iteration cycles, but game design, architecture, balance tuning, and quality standards were all human-driven. **The tools amplified my output, but the creative direction is all human.**

If you're an actual artist or actual sound designer interested in improving the game's polish, I'd love to collaborate. Reach out!

---

**Technical Stack:**
* **Language:** Python + TCOD 19.6.0 (latest!)
* **Dev Environment:** VS Code on Windows 10/11
* **Testing:** Parallel test execution with headless game agents, per-worker file isolation, pre-commit hooks
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
