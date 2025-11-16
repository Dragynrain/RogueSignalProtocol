# Reddit Post - r/roguelikes

---

## Title:

`Rogue Signal Protocol - Stealth roguelike where enemies show their next 3 moves`

---

## Post Body:

I just released **Rogue Signal Protocol** - a traditional turn-based roguelike with stealth mechanics. Turn-based grid combat, permadeath, procedural generation, ASCII mode - all the traditional staples are here.

**YouTube gameplay:** https://youtu.be/URI75uHpOOc

*(Screenshots in comments)*

The core concept: you're a trapped digital consciousness infiltrating hostile corporate networks. I wanted to make a stealth roguelike where you actually have enough information to make smart tactical decisions instead of just guessing where enemies will move.

So enemies show their next 3 planned moves. You can see exactly where they're planning to patrol based on their current state. They'll recalculate if they spot you, but you always see their intent. It turns stealth into this tactical puzzle where you're planning routes around patrols, setting up ambushes when you have the advantage, or just trying to slip past undetected.

The game really pushes you toward stealth over combat. You CAN fight, but it's risky - enemies hit hard and you have limited resources. Hide in blind spots to break line of sight (and get +10 damage if you ambush from there). But if you get detected too much, the Admin Avatar spawns - this 250 HP boss that just hunts you relentlessly with perfect tracking. Very bad times.

Combat has zero RNG - damage is fixed, not dice-rolled. I wanted every death to feel like "I made a bad tactical choice" rather than "the RNG screwed me."

The game has 3 procedurally-generated networks (Corporate, Government, Military), 8 enemy types with different behaviors, and 13 exploits ranging from stealth tools to devastating attacks. All your abilities generate heat though, so you're constantly managing that resource - overheat and you start damaging yourself.

There's also a story woven through it - 20+ narrative fragments scattered across the networks that persist even after you die. Each run you might find a few more pieces of the conspiracy. Permadeath deletes your save file automatically, but the story fragments you've found stick around.

Runs are pretty quick - 10 to 15 minutes to go through all 3 networks if you survive. Good "one more run" length.

The game has dual rendering - you can swap between graphical sprites or classic ASCII glyphs anytime. Also has atmospheric music, sound effects (toggleable), particle explosions, achievements, full keyboard and mouse support.

**Where to get it:**

**Itch.io (free/pay what you want):** https://dragynrain.itch.io/rogue-signal-protocol

**GitHub (open source, MIT license):** https://github.com/Dragynrain/RogueSignalProtocol

**Feedback survey:** https://forms.gle/jbwGdn8VGPa6NG9p9

This is alpha v0.8.0 - feature complete and pretty polished, but I really want feedback on difficulty balance. Does it feel too easy? Too hard? I've been playtesting it for weeks so I honestly can't tell anymore.

Also made bug reporting dead simple - just hit Shift+F12 in-game and it auto-generates a debug package with your saves, logs, and screenshots all zipped up.

Windows 10/11 only right now. About 200 MB download, runs standalone.

Would love to hear what you think if you give it a try!

---

## Comment Template (for posting screenshot gallery):

```
Screenshots: [imgur gallery link]

Gameplay showing enemy movement prediction, ASCII mode, sprite mode, narrative fragments, and combat.
```

---

## IMPORTANT REMINDERS:

**Screenshots:**
- Upload all 5 screenshots to imgur as a gallery
- Post ONE comment with the imgur gallery link

**Posting on r/roguelikes:**
- This counts as your ONE promotional post for the next 3 months
- Must be a "traditional roguelike" (yours qualifies)
- No low-effort posts (yours has substance)
- Be nice in responses

**DO NOT mention:**
- AI development workflow
- How it was built
- Development timeline
- Testing infrastructure

**ONLY IF DIRECTLY ASKED:**
- Then you can mention AI assistance briefly and factually
- Focus answer back on the game experience
