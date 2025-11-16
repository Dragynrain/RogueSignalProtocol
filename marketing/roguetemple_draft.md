# RogueTemple Forum Post

---

## Thread Title:

[Alpha] Rogue Signal Protocol - Tactical stealth roguelike with deterministic enemy movement queues

---

## Post Body:

Hello RogueTemple community,

I'd like to share **Rogue Signal Protocol**, a coffee-break traditional turn-based roguelike I've been developing that focuses on tactical stealth mechanics. The game centers around a core question: what if enemies showed you their next 3 planned moves before executing them?

**Core Roguelike Elements:**
- Turn-based grid combat with strict turn ordering
- True permadeath (save file deletion on death)
- Procedurally generated network levels
- Resource management and tactical decision-making
- Zero RNG in combat (fixed damage values, no chance to hit)
- Pure ASCII mode available alongside graphical tiles

**YouTube gameplay demonstration:** https://youtu.be/URI75uHpOOc

**The Movement Queue System:**

Every enemy displays a 3-move queue showing exactly where they plan to move based on their current AI state (patrol, investigate, chase). This queue invalidates only when their state changes or a move gets blocked. The goal was to give players enough information to make informed tactical decisions rather than guessing enemy behavior.

This transforms stealth into a spatial puzzle where you're analyzing patrol patterns, identifying safe paths, and planning ambushes. You can see a guard will patrol away from the exit in exactly 2 turns, giving you a window to slip past.

**Tactical Depth:**

The game strongly incentivizes stealth over direct combat. Fighting is possible but risky - enemies deal significant damage and resources are limited. You can hide in blind spots (marked with special glyphs) to break line of sight, which grants +10 ambush damage if you strike from concealment.

Detection accumulates across the level. Get spotted too many times and the Admin Avatar spawns - a 250 HP boss that hunts you with perfect tracking and no movement queue. This creates a nice tension where you're weighing risk versus reward for each detection.

All abilities (called "exploits" in the game's fiction) generate heat. Overheat and you start taking self-damage, so there's constant resource management even during stealth.

**Content:**
- 3 procedurally generated network levels (Corporate, Government, Military)
- 8 enemy types with distinct AI behaviors
- 13 exploits ranging from stealth utilities to high-damage attacks
- 20+ narrative fragments that persist across deaths
- Runs typically last 10-15 minutes

**Setting:**

You're a trapped digital consciousness exfiltrating hostile corporate networks. The narrative unfolds through data fragments randomly discovered - permadeath wipes your progress but story discoveries persist, encouraging multiple runs to piece together the full conspiracy.

**Technical Details:**
- Built with Python and python-tcod
- Dual rendering: swap between graphical sprites and ASCII glyphs anytime
- Full keyboard and mouse support
- Windows 10/11 (standalone, ~200 MB)
- Open source (MIT license)

**Current Status:**

This is alpha v0.8.0 - feature complete and reasonably polished. I'm particularly seeking feedback on difficulty balance, as I've been playtesting for weeks and have lost all objective perspective!!

The game includes atmospheric music and sound effects (toggleable), particle effects, achievements, and a debug reporting system (Shift+F12 auto-generates a full diagnostic package).

**Download Links:**

**Itch.io (free/pay what you want):** https://dragynrain.itch.io/rogue-signal-protocol

**GitHub (source code):** https://github.com/Dragynrain/RogueSignalProtocol

**Feedback survey:** https://forms.gle/jbwGdn8VGPa6NG9p9

I'd genuinely appreciate any feedback from this community. RogueTemple has always been my go-to resource for understanding roguelike design principles, so getting input from folks here would be invaluable!

Happy to answer any questions about design decisions or implementation details.

