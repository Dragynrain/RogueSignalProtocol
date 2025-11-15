# Reddit Post Draft - r/roguelikedev

---

## Title Options:

1. `Rogue Signal Protocol - Cyberspace stealth roguelike (with AI dev workflow)`

---

## Post Body:

Hey r/roguelikedev!

I've lurked here for many years and attempted creating several roguelike games in the past to no great success. However, today I've just released **Rogue Signal Protocol** (v0.8.0 Alpha), a traditional turn-based coffee break stealth roguelike (that's a mouthful!) where you play as an escaped digital consciousness navigating hostile corporate networks. Quick 10-15 minute runs with permadeath - each death teaches lessons, each run reveals more truth.

*(Screenshots in comments)*

### Core Features:
* **Deterministic gameplay (no RNG)** - Pure skill-based tactical decisions, no luck involved
* **Enemy movement prediction** - See each enemy's next 3 planned moves for tactical planning
* **3 procedurally-generated network levels** with 8 unique enemy types, 13 exploits, and distinct AI behaviors
* **Dual rendering modes** - Switch between graphical sprites or classic ASCII glyphs

### What Makes It Different:
**Enemy movement prediction** shows you each enemy's next 3 planned moves - no guessing, pure tactical planning. It's like playing chess against enemies who show their next moves. Use this intel to slip past patrols, set up ambushes, or plan your escape route.

The **stealth mechanics** are central - you're not meant to fight everything. Hide in blind spots to avoid detection and manage your heat levels carefully. Push your detection too high and the **Admin Avatar** spawns - a powerful boss with perfect tracking and relentless pursuit.

**Heat management** from exploit usage and bump attacks adds another resource layer beyond typical HP/mana. Every move counts in this purely skill-based tactical challenge.

The **story is told through environmental fragments** - 20+ story fragments persist across runs, even death can't erase them. Each run might reveal new pieces of the Project Chimera conspiracy. Permadeath for your character, but persistent narrative discovery means every run brings you closer to the truth.

The game features full audio with atmospheric music and 40+ sound effects, particle effect explosions for enemy death, and complete keyboard and mouse support. Track your progress across runs with the **Achievement System** - unlock challenges and prove your mastery of stealth tactics.

### Where to Get It:
**Itch.io:** https://dragynrain.itch.io/rogue-signal-protocol
**Source Code:** https://github.com/Dragynrain/RogueSignalProtocol
**Feedback Survey:** https://forms.gle/jbwGdn8VGPa6NG9p9
**Youtube Link:** https://youtu.be/URI75uHpOOc

This is **alpha 0.8.0** - feature complete and playtested, now looking for wider feedback on:
* **Difficulty** - Is it too easy? Too hard? Fair but challenging?
* Stealth vs combat balance and overall fun factor
* Any bugs or edge cases I missed

**Bug reporting made easy:** Hit Shift+F12 or use Settings > Export Debug Package to create a comprehensive debug report (saves, logs, metrics, system info, screenshot). Makes bug reporting super simple!

---

## How This Was Built

**Background:** I'm a professional software engineer, so this was built with engineering discipline: architecture reviews, code quality standards, and comprehensive automated testing. 

This game was built with the assistance of AI tools (Claude Code for code, Stable Diffusion for sprites and images, AudioCraft for SFX), compressing the timeline from probably 6-12+ months to closer to 3 months. I did use some wonderful human-created music for the soundtrack!

I approached this project more like a technical project manager: breaking down requirements, reviewing architecture decisions, curating outputs, and ensuring quality. This is my first project with AI. I definitely learned a lot about coding with AI assistance and how best to use Claude Code and how to maximize my time spent on the fun things like designing game systems! 

**The reality:** I approached asset generation with most of my time spent on quality control - only keeping outputs that fit the game's design vision. Thousands of sprites and images were discarded before settling on the ones I did. AI definitely accelerated the prototyping and iteration cycles, but game design, architecture, balance tuning, and quality standards were all human-driven. **The tools amplified my output, but the creative direction is all human.**

There's a Graphics Preview option in the main menu that has dozens of sprites I created and lets you preview them together (walls, floors, enemies, player, etc.) to see how well they match, which is how I chose the default sprite set. I'm not a real artist by any means though! If you think you can do choose better from among my sprites send me your set (the previewer will actually save what you have chosen to a log file).

If you are an actual artist or actual sound designer interested in improving the game's polish, I'd love to collaborate. Reach out!

**Testing Infrastructure:** This game is supported by a massive testing infrastructure to alleviate the need for as much manual testing.
* **2000+ automated tests** - 1000+ unit tests, 1000+ integration tests, 50+ agent-based gameplay tests
* **GameTestAgent framework** - Headless game simulation where AI agents actually play the game to validate mechanics
* **Specialized test agents:** Chaos agents (spam random inputs to find edge cases), speed-running agents (test optimal pathing), pacifist stealth agents (ensure non-combat paths remain viable), barbarian agents (pure combat validation)
* **Parallel test execution** with custom per-worker file isolation - runs the full suite in under a minute
* **Automated regression testing** - Pre-commit hooks prevent broken code from entering the repository
* Catches mechanical bugs and edge cases that might not surface in manual playtesting

I learned so much more about testing methodologies, processes, and patterns building this all out!

---

**Technical Stack:**
* **Language:** Python + TCOD 19.6.0 (latest!)
* **Dev Environment:** VS Code on Windows 11
* **Testing:** Parallel test execution with headless game agents, per-worker file isolation, pre-commit hooks
* **Runtime:** Windows standalone EXE (~200 MB download)
* **Play Time:** 5-15 minutes per full 3-level run
* **License:** MIT (free and open source)

---

**Happy to answer any questions about the workflow** - what worked, what didn't, where AI helped vs. where it fell short, or anything about the development process. And of course, would love feedback on the game itself!

I feel like the game is way too easy in its current state and I want to ratchet up the difficulty and add an Ascension system and gamepad support. But I also wrote the game and know how all the systems work so of course it feels easy to me! What do you think??
