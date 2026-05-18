# RogueTemple Forum Post - v1.0

---

## Thread Title:

Rogue Signal Protocol 1.0 - Stealth roguelike with visible enemy movement queues

---

## Post Body:

Hi RogueTemple,

Rogue Signal Protocol is a coffee-break turn-based roguelike focused on tactical stealth. The central mechanic: enemies display their next 3 planned moves based on current AI state. The queue only updates when they change state (patrol to investigate to chase) or when a move gets blocked.

1.0 just shipped after a year of beta. Posting because I'd value design feedback as much as bug reports.

**Roguelike elements:**
- Turn-based grid movement
- Permadeath with automatic save deletion
- Procedural level generation
- Zero combat RNG - fixed damage values, no hit chance
- Graphical tiles or ASCII mode

**Design decisions I'd like feedback on:**

*Deterministic combat* - No dice rolls. Every hit lands, damage is fixed. Deaths should feel like tactical mistakes, not bad luck. Makes combat more predictable and puzzle-y. Does this work for you, or does it remove tension?

*Detection accumulation* - Get spotted too often and a boss spawns that ignores most of the usual rules (250 HP, perfect tracking, 45 damage per hit). This punishes sloppy play but also creates an "abort run" decision point. Too harsh? Not harsh enough?

*Heat management* - All abilities generate heat. Overheat and you take self-damage. This limits burst potential but feels more like resource accounting than a tactical choice. Wondering if there's a better approach.

*Prologue tutorial (new in 1.0)* - A 5-section hand-designed level that teaches mechanics by making them necessary. No popups. First section has a damaged Scanner blocking the only door so the player figures out they can attack because there's no other option. Curious if this works for new players or feels too constrained.

**What's in 1.0:**
- Prologue tutorial
- Console window no longer flashes behind game on Windows
- Linux support (AppImage, tarball, AUR; Flatpak pending Flathub)
- Full gamepad support including Steam Deck
- Keyboard and gamepad remapping
- 20 Ascension difficulty levels
- 47 achievements
- Save system, status bar, audio, and pathfinding polish

**Links:**

Itch.io: https://dragynrain.itch.io/rogue-signal-protocol

GitHub (MIT): https://github.com/Dragynrain/RogueSignalProtocol

Bug tracker: https://github.com/Dragynrain/RogueSignalProtocol/issues

Runs last 10-15 minutes. Windows and Linux. About 250 MB.

Interested in design critique as much as bug reports.

---

## BBCode Version (try this first - most forums use BBCode):

```
Hi RogueTemple,

[b]Rogue Signal Protocol[/b] is a coffee-break turn-based roguelike focused on tactical stealth. The central mechanic: enemies display their next 3 planned moves based on current AI state. The queue only updates when they change state (patrol to investigate to chase) or when a move gets blocked.

1.0 just shipped after a year of beta. Posting because I'd value design feedback as much as bug reports.

[b]Roguelike elements:[/b]
[list]
[*] Turn-based grid movement
[*] Permadeath with automatic save deletion
[*] Procedural level generation
[*] Zero combat RNG - fixed damage values, no hit chance
[*] Graphical tiles or ASCII mode
[/list]

[b]Design decisions I'd like feedback on:[/b]

[i]Deterministic combat[/i] - No dice rolls. Every hit lands, damage is fixed. Deaths should feel like tactical mistakes, not bad luck. Makes combat more predictable and puzzle-y. Does this work for you, or does it remove tension?

[i]Detection accumulation[/i] - Get spotted too often and a boss spawns that ignores most of the usual rules (250 HP, perfect tracking, 45 damage per hit). This punishes sloppy play but also creates an "abort run" decision point. Too harsh? Not harsh enough?

[i]Heat management[/i] - All abilities generate heat. Overheat and you take self-damage. This limits burst potential but feels more like resource accounting than a tactical choice. Wondering if there's a better approach.

[i]Prologue tutorial (new in 1.0)[/i] - A 5-section hand-designed level that teaches mechanics by making them necessary. No popups. First section has a damaged Scanner blocking the only door so the player figures out they can attack because there's no other option. Curious if this works for new players or feels too constrained.

[b]What's in 1.0:[/b]
[list]
[*] Prologue tutorial
[*] Console window no longer flashes behind game on Windows
[*] Linux support (AppImage, tarball, AUR; Flatpak pending Flathub)
[*] Full gamepad support including Steam Deck
[*] Keyboard and gamepad remapping
[*] 20 Ascension difficulty levels
[*] 47 achievements
[*] Save system, status bar, audio, and pathfinding polish
[/list]

[b]Links:[/b]
[url=https://dragynrain.itch.io/rogue-signal-protocol]Itch.io[/url] (free)
[url=https://github.com/Dragynrain/RogueSignalProtocol]GitHub[/url] (MIT license)
[url=https://github.com/Dragynrain/RogueSignalProtocol/issues]Bug tracker[/url] (GitHub Issues)

Runs last 10-15 minutes. Windows and Linux. About 250 MB.

Interested in design critique as much as bug reports.
```
