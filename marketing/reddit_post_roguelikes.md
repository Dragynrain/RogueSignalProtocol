# Reddit Post - r/roguelikes / r/roguelikedev

---

## Title:

`Rogue Signal Protocol 1.0 - Stealth roguelike where enemies show their next 3 moves`

---

## Post Body:

I just shipped **1.0** of Rogue Signal Protocol after about a year of betas. Turn-based grid combat, permadeath, procedural generation, ASCII mode - all the traditional staples.

**YouTube gameplay:** https://youtu.be/URI75uHpOOc

*(Screenshots in comments)*

The core concept: you're a trapped digital consciousness sneaking through hostile corporate networks. I wanted a stealth roguelike where you actually have enough information to make smart tactical decisions instead of guessing where enemies will move.

So enemies show their next 3 planned moves. You can see exactly where they're going based on their current state, and they commit to it unless they spot you or get blocked. It turns stealth into a tactical puzzle - planning routes around patrols, setting up ambushes when you have the advantage, or just trying to ghost the level.

The game pushes you toward stealth over combat. You CAN fight, but it's risky - enemies hit hard and you have limited resources. Hide in blind spots to break line of sight and get +10 damage if you ambush from there. Get detected too much and the Admin Avatar spawns - 250 HP boss with perfect tracking and 45 damage per hit. Beatable but expensive. Most runs end better if it never shows up.

Combat has zero RNG - damage is fixed, not dice-rolled. Every death should feel like "I made a bad tactical choice" rather than "the RNG screwed me."

3 procedurally-generated networks (Corporate, Government, Military), 8 enemy types, 13 exploits ranging from stealth tools to attacks. All your abilities generate heat - overheat and you start damaging yourself.

**New in 1.0:**

- Prologue tutorial - 5-section level that teaches the mechanics by making them necessary. No popups. First room has a damaged Scanner blocking the only door so you figure out you can attack because there's no other option.
- Console window no longer flashes behind the game on Windows
- Big polish pass on saves, status bar, audio, pathfinding

There's also a story - 20+ narrative fragments scattered across the networks that persist after you die. Each run you might find a few more pieces of the Project Chimera plot. Permadeath deletes your save automatically, but the fragments stick around.

Runs are 10-15 minutes. Good "one more run" length.

Dual rendering - swap between graphical sprites or ASCII glyphs anytime. Music, sound effects (toggleable), particle explosions, achievements, full keyboard, mouse, and gamepad support (Xbox, PlayStation, Steam Deck native).

**Where to get it:**

- **Itch.io (free):** https://dragynrain.itch.io/rogue-signal-protocol
- **GitHub (MIT):** https://github.com/Dragynrain/RogueSignalProtocol
- **AUR:** `yay -S rogue-signal-protocol-bin`

Windows 10/11 and Linux. About 250 MB. Tested on Steam Deck.

Bug reports and balance feedback go in GitHub Issues: https://github.com/Dragynrain/RogueSignalProtocol/issues

Would love to hear what you think.
