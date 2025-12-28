# RogueBasin Wiki Draft

Copy the wiki markup below:

---

```wiki
{{game-beta
| name = Rogue Signal Protocol
| developer = [[User:Dragynrain|Dragynrain]]
| theme = Cyberpunk, Stealth
| influences =
| released = December 2025 (0.9.0)
| updated = December 2025
| licensing = [[MIT License]]
| language = [[Python]], [[python-tcod]]
| platforms = [[Windows]], [[Linux]]
| interface = Graphical tiles, ASCII
| length = 5-15 minutes
| site = https://dragynrain.itch.io/rogue-signal-protocol
| download = https://dragynrain.itch.io/rogue-signal-protocol
| repository = https://github.com/Dragynrain/RogueSignalProtocol
}}

'''Rogue Signal Protocol''' is a coffee-break turn-based roguelike focused on tactical stealth. The player is a trapped digital consciousness exfiltrating hostile corporate networks, using exploits and stealth to reach the exit of each level.

== Gameplay ==

The core mechanic is '''visible enemy intent''': every enemy displays their next 3 planned moves based on their current AI state (patrol, investigate, chase). The queue only updates when the enemy changes state or a move gets blocked. This transforms stealth into a spatial puzzle where you read patrol routes, find timing windows, and set up ambushes.

Combat uses '''deterministic damage''' with no RNG. Every attack lands, damage values are fixed. Deaths result from tactical mistakes rather than bad luck.

=== Detection System ===

Getting spotted increases a global trace meter. If trace reaches 100%, the Admin Avatar spawns - a powerful boss with 250 HP that ignores normal movement rules and tracks the player perfectly. This creates tension between aggressive play and careful stealth.

=== Heat Management ===

All abilities (called "exploits") generate heat. Overheating causes self-damage, limiting burst potential and requiring resource management throughout each run.

== Features ==

* 3 procedurally generated networks (Corporate, Government, Military)
* 8 enemy types with distinct AI behaviors
* 13 exploits ranging from stealth utilities to attacks
* True permadeath with automatic save deletion
* 20 Ascension difficulty levels for replayability
* 47 achievements
* Dual rendering: switch between graphical tiles and ASCII anytime
* Full gamepad support including Steam Deck
* Keyboard and gamepad remapping

== Story ==

Narrative fragments are scattered across levels and persist between deaths. Each run reveals more of the conspiracy, encouraging multiple playthroughs to piece together the full story.

== Links ==

* [https://dragynrain.itch.io/rogue-signal-protocol Itch.io page] (free/pay what you want)
* [https://github.com/Dragynrain/RogueSignalProtocol GitHub repository] (MIT license)
* [https://www.youtube.com/watch?v=URI75uHpOOc Gameplay video]

[[Category:Beta projects]]
[[Category:Coffeebreak roguelikes]]
[[Category:Futuristic roguelikes]]
[[Category:Handheld roguelikes]]
```

---

## Notes

- Template might be `{{game-beta}}` or `{{Gameinfo}}` - check RogueBasin for exact name
- Categories at the bottom link the game to relevant lists
- Create a user page `[[User:Dragynrain]]` if you want your name linked
- You may need to create the page at: https://www.roguebasin.com/index.php?title=Rogue_Signal_Protocol
