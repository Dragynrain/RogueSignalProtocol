# RogueTemple Forum Post - v0.9.0

---

## Thread Title:

Rogue Signal Protocol - Stealth roguelike with visible enemy movement queues (v0.9.0)

---

## Post Body:

Hi RogueTemple,

Rogue Signal Protocol is a coffee-break turn-based roguelike focused on tactical stealth. The central mechanic: enemies display their next 3 planned moves based on current AI state. The queue only updates when they change state (patrol to investigate to chase) or when a move gets blocked.

**Roguelike elements:**
- Turn-based grid movement
- Permadeath with automatic save deletion
- Procedural level generation
- Zero combat RNG - fixed damage values, no hit chance
- Graphical Tiles or ASCII mode

**Design decisions I'd like feedback on:**

*Deterministic combat* - No dice rolls. Every hit lands, damage is fixed. Deaths should feel like tactical mistakes, not bad luck. Makes combat more predictable and puzzle-y. Does this work for you, or does it remove tension?

*Detection accumulation* - Get spotted too often and a boss spawns that ignores all the usual rules. This punishes sloppy play but also creates an "abort run" decision point. Too harsh? Not harsh enough? Can it be killed?

*Heat management* - All abilities generate heat. Overheat and you take self-damage. This limits burst potential but feels more like resource management than a tactical choice. Wondering if there's a better approach.

**What's in 0.9.0:**
- Linux support (AppImage, Flatpak pending Flathub review)
- Full gamepad support
- Steam Deck support!!!
- Keyboard and gamepad remapping
- 20 Ascension difficulty levels
- 47 achievements

**Links:**

Itch.io: https://dragynrain.itch.io/rogue-signal-protocol

GitHub (MIT): https://github.com/Dragynrain/RogueSignalProtocol

Feedback form: https://forms.gle/jbwGdn8VGPa6NG9p9

Runs last 5-15 minutes. Windows and Linux. About 200 MB.

Interested in design critique as much as bug reports.

---

## BBCode Version (try this first - most forums use BBCode):

```
Hi RogueTemple,

[b]Rogue Signal Protocol[/b] is a coffee-break turn-based roguelike focused on tactical stealth. The central mechanic: enemies display their next 3 planned moves based on current AI state. The queue only updates when they change state (patrol to investigate to chase) or when a move gets blocked.

[b]Roguelike elements:[/b]
[list]
[*] Turn-based grid movement
[*] Permadeath with automatic save deletion
[*] Procedural level generation
[*] Zero combat RNG - fixed damage values, no hit chance
[*] Graphical Tiles or ASCII mode
[/list]

[b]Design decisions I'd like feedback on:[/b]

[i]Deterministic combat[/i] - No dice rolls. Every hit lands, damage is fixed. Deaths should feel like tactical mistakes, not bad luck. Makes combat more predictable and puzzle-y. Does this work for you, or does it remove tension?

[i]Detection accumulation[/i] - Get spotted too often and a boss spawns that ignores all the usual rules. This punishes sloppy play but also creates an "abort run" decision point. Too harsh? Not harsh enough? Can it be killed?

[i]Heat management[/i] - All abilities generate heat. Overheat and you take self-damage. This limits burst potential but feels more like resource management than a tactical choice. Wondering if there's a better approach.

[b]What's in 0.9.0:[/b]
[list]
[*] Linux support (AppImage, Flatpak pending Flathub review)
[*] Full gamepad support
[*] Steam Deck support!!!
[*] Keyboard and gamepad remapping
[*] 20 Ascension difficulty levels
[*] 47 achievements
[/list]

[b]Links:[/b]
[url=https://dragynrain.itch.io/rogue-signal-protocol]Itch.io[/url] (free/pay what you want)
[url=https://github.com/Dragynrain/RogueSignalProtocol]GitHub[/url] (MIT license)
[url=https://forms.gle/jbwGdn8VGPa6NG9p9]Feedback form[/url]

Runs last 5-15 minutes. Windows and Linux. About 200 MB.

Interested in design critique as much as bug reports.
```
