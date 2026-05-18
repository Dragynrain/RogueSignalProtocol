# RogueBasin Wiki Draft

Copy the wiki markup below:

---

```wiki
{{Gameinfo
| name = Rogue Signal Protocol
| developer = [[User:Dragynrain|Dragynrain]]
| theme = Cyberpunk, Stealth
| influences =
| released = May 2026 (1.0)
| updated = May 2026
| licensing = [[MIT License]]
| language = [[Python]], [[python-tcod]]
| platforms = [[Windows]], [[Linux]]
| interface = Graphical tiles, ASCII
| length = 10-15 minutes
| site = https://dragynrain.itch.io/rogue-signal-protocol
| download = https://dragynrain.itch.io/rogue-signal-protocol
| repository = https://github.com/Dragynrain/RogueSignalProtocol
}}

'''Rogue Signal Protocol''' is a coffee-break turn-based roguelike focused on stealth. The player is a digital consciousness escaping hostile corporate networks, using stealth and exploits to reach the exit of each level.

== Gameplay ==

The central mechanic is '''visible enemy intent''': every enemy displays its next 3 planned moves based on its current AI state (patrol, investigate, chase). The queue only updates when the enemy changes state or a move gets blocked. Stealth becomes a spatial puzzle of patrol routes, timing windows, and ambush positions.

Combat is '''deterministic'''. Every attack lands, damage values are fixed, no dice rolls. Deaths come from positioning and resource mistakes rather than bad luck.

=== Detection System ===

Getting spotted raises a global trace meter. At 100%, the Admin Avatar spawns - 250 HP, perfect tracking, 45 damage per hit. It's beatable but expensive, and most runs end better if it never appears.

=== Heat Management ===

All abilities (called "exploits") generate heat. Overheating causes self-damage, so exploit use has to be paced.

== Features ==

* 3 procedurally generated networks (Corporate, Government, Military)
* 8 enemy types with distinct AI behaviors
* 13 exploits covering stealth, combat, and utility
* Permadeath with automatic save deletion
* 20-level Ascension mode (stacking difficulty modifiers)
* 47 achievements
* Dual rendering: graphical tiles or ASCII, toggle in-game
* Full gamepad support including Steam Deck
* Keyboard and gamepad remapping

== Story ==

20+ narrative fragments are scattered across the levels and persist between deaths. Each run reveals more of the Project Chimera plot.

== Links ==

* [https://dragynrain.itch.io/rogue-signal-protocol Itch.io page] (free/pay what you want)
* [https://github.com/Dragynrain/RogueSignalProtocol GitHub repository] (MIT license)
* [https://github.com/Dragynrain/RogueSignalProtocol/issues Bug tracker] (GitHub Issues)
* [https://www.youtube.com/watch?v=URI75uHpOOc Gameplay video]

[[Category:Coffeebreak roguelikes]]
[[Category:Futuristic roguelikes]]
[[Category:Handheld roguelikes]]
```

---

## Notes

- Template is `{{Gameinfo}}` for stable releases (was `{{game-beta}}` for the 0.9.x drafts)
- "Beta projects" category dropped now that 1.0 has shipped
- Verify exact template/category names against current RogueBasin conventions before posting
- Categories at the bottom link the game to relevant lists
- Create a user page `[[User:Dragynrain]]` if you want your name linked
- You may need to create the page at: https://www.roguebasin.com/index.php?title=Rogue_Signal_Protocol
