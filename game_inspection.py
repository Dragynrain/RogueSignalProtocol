#!/usr/bin/env python3
"""
Rogue Signal Protocol - Entity Inspection Module

Provides entity inspection for look mode with priority-based entity identification.
EntityInspector examines positions and returns formatted entity information.
Loads terrain descriptions from game_rules.json. Used by inspection panel rendering.
"""

from typing import Any

from data_loading import DataLoader
from game_data import GameData
from game_entities import Colors, Position


class EntityInspector:
    """Inspects game entities at positions and returns their information."""

    # Cache terrain descriptions from config
    _terrain_descriptions = None

    @classmethod
    def _load_terrain_descriptions(cls):
        """Load terrain descriptions from game_rules.json."""
        if cls._terrain_descriptions is None:
            config = DataLoader.load_config()
            cls._terrain_descriptions = config["terrain_descriptions"]

    @staticmethod
    def get_entity_at_position(game, position: Position) -> dict[str, Any]:
        """
        Get information about the entity at the specified position.

        Returns a dictionary with:
        - name: Display name of the entity
        - description: Description text
        - entity_type: Type of entity (player, enemy, item, terrain, etc.)
        - details: Additional context-specific information
        - color: Color to display the name in

        Priority order:
        1. Player
        2. Enemies
        3. Items (code hacks, exploits, upgrades, story fragments)
        4. Special tiles (gateway, nodes)
        5. Terrain (wall, blind spot, floor)
        """
        EntityInspector._load_terrain_descriptions()

        # Check if position is valid
        if not position.is_valid(game.game_map.width, game.game_map.height):
            return {
                "name": "Out of Bounds",
                "description": "Invalid position",
                "entity_type": "invalid",
                "details": "",
                "color": Colors.DARK_GRAY,
            }

        # 1. Check for player
        if game.player.x == position.x and game.player.y == position.y:
            return EntityInspector._inspect_player(game)

        # 2. Check for enemies
        enemy = game.enemy_manager.get_enemy_at_position(position)
        if enemy:
            return EntityInspector._inspect_enemy(enemy, game)

        # 3. Check for items
        item_info = EntityInspector._inspect_items(game, position)
        if item_info:
            return item_info

        # 4. Check for special tiles
        special_tile_info = EntityInspector._inspect_special_tiles(game, position)
        if special_tile_info:
            return special_tile_info

        # 5. Check terrain
        return EntityInspector._inspect_terrain(game, position)

    @staticmethod
    def _inspect_player(game) -> dict[str, Any]:
        """Inspect the player."""
        player = game.player

        # Build status effects list
        status_effects = []
        if player.temporary_effects["speed_boost_turns"] > 0:
            status_effects.append(
                f"Speed Boost ({player.temporary_effects['speed_boost_turns']} turns)"
            )
        if player.temporary_effects["enhanced_vision_turns"] > 0:
            status_effects.append(
                f"Enhanced Vision ({player.temporary_effects['enhanced_vision_turns']} turns)"
            )
        if player.temporary_effects["exploit_efficiency_turns"] > 0:
            status_effects.append(
                f"Exploit Efficiency ({player.temporary_effects['exploit_efficiency_turns']} turns)"
            )
        if player.temporary_effects.get("invisible_turns", 0) > 0:
            status_effects.append(
                f"Invisible ({player.temporary_effects['invisible_turns']} turns)"
            )
        if player.temporary_effects["virus_turns"] > 0:
            status_effects.append(f"VIRUS ({player.temporary_effects['virus_turns']} turns)")
        if player.temporary_effects["movement_slowed_turns"] > 0:
            status_effects.append(
                f"Slowed ({player.temporary_effects['movement_slowed_turns']} turns)"
            )

        status_text = "; ".join(status_effects) if status_effects else "None"

        details = f"CPU: {player.cpu}/{player.max_cpu} | Heat: {player.heat}/{player.max_heat}\n"
        details += f"RAM: {player.ram_total} | Trace: {player.trace_level}%\n"
        details += f"Status: {status_text}"

        return {
            "name": "Player (You)",
            "description": "Your digital infiltration agent",
            "entity_type": "player",
            "details": details,
            "color": Colors.GREEN,
        }

    @staticmethod
    def _inspect_enemy(enemy, game=None) -> dict[str, Any]:
        """
        Inspect an enemy and show damage preview if in targeting mode.

        Args:
            enemy: Enemy to inspect
            game: Optional GameEngine instance (for damage preview in targeting mode)
        """
        enemy_type = enemy.type_data

        # Determine color based on state
        from game_entities import EnemyState

        if enemy.state == EnemyState.UNAWARE:
            color = Colors.ENEMY_UNAWARE
            state_text = "Unaware"
        elif enemy.state == EnemyState.ALERT:
            color = Colors.ENEMY_ALERT
            state_text = "Alert"
        else:  # HOSTILE
            color = Colors.ENEMY_HOSTILE
            state_text = "Hostile"

        # Build details
        details = f"State: {state_text} | CPU: {enemy.cpu}/{enemy.max_cpu}\n"
        details += f"Vision: {enemy_type.vision} | Damage: {enemy_type.damage}\n"

        if enemy.disabled_turns > 0:
            details += f"Disabled for {enemy.disabled_turns} turns\n"

        # Add movement pattern info
        from game_entities import EnemyMovement

        movement_desc = {
            EnemyMovement.STATIC: "Static guard",
            EnemyMovement.PATROL: "Patrols route",
            EnemyMovement.RANDOM: "Random movement",
            EnemyMovement.SEEK: "Actively hunting",
            EnemyMovement.ADMIN: "Relentless pursuer",
            EnemyMovement.TRACK: "Tracking target",
            EnemyMovement.VIRUS: "Unpredictable",
        }.get(enemy_type.movement, "Unknown")

        details += f"Behavior: {movement_desc}"

        # Add damage preview if in targeting mode with equipped exploits
        if game and game.targeting_mode and game.targeting_exploit:
            damage_preview = EntityInspector._calculate_damage_preview(game, enemy)
            if damage_preview:
                details += f"\n\n{damage_preview}"

        return {
            "name": enemy_type.name,
            "description": enemy_type.description,
            "entity_type": "enemy",
            "details": details,
            "color": color,
        }

    @staticmethod
    def _calculate_damage_preview(game, enemy) -> str | None:
        """
        Calculate compact damage preview for current targeting exploit.

        Shows damage calculation in 2-3 lines:
        - Line 1: [Exploit Name]
        - Line 2: Damage calculation -> Result

        Examples:
        - "25 dmg -> 25/50 CPU"
        - "25+10 -> ELIMINATED" (shadow bonus)
        - "40 (-50%) -> 230/250 CPU" (admin resist)

        Returns:
            Formatted damage preview string, or None if exploit doesn't deal damage
        """
        exploit = GameData.EXPLOITS.get(game.targeting_exploit)
        if not exploit or exploit.damage == 0:
            return None  # Non-damaging exploit

        # Calculate base damage
        base_damage = exploit.damage

        # Check for shadow bonus (+10 if attacking from blind spots or while invisible)
        player_in_shadow = (
            game.game_map.is_blind_spot(game.player.position) or game.player.is_invisible()
        )
        shadow_bonus = 10 if player_in_shadow else 0
        total_damage = base_damage + shadow_bonus

        # Apply admin resistance if needed
        final_damage = total_damage
        resist_text = ""
        if enemy.type == "admin":
            final_damage = max(5, total_damage // 2)  # 50% resistance, min 5
            resist_text = " (-50%)"

        # Calculate result
        remaining_cpu = enemy.cpu - final_damage

        # Format compact preview (2-3 lines max)
        preview = f"[{exploit.name}]\n"

        # Build damage line
        if shadow_bonus > 0:
            dmg_text = f"{base_damage}+{shadow_bonus}{resist_text}"
        else:
            dmg_text = f"{base_damage}{resist_text}"

        # Build result
        if remaining_cpu <= 0:
            result_text = "ELIMINATED"
        else:
            result_text = f"{remaining_cpu}/{enemy.max_cpu} CPU"

        preview += f"{dmg_text} -> {result_text}"

        return preview

    @staticmethod
    def _inspect_items(game, position: Position) -> dict[str, Any] | None:
        """Check for items at position (code hacks, exploits, upgrades, story fragments)."""
        from game_entities import Colors

        # Check for code hack
        code_hack = game.game_map.get_code_hack(position)
        if code_hack:
            # Check if we know the effect
            if code_hack.discovered or code_hack.color_name in game.discovered_code_effects:
                effect_desc = game.code_hack_effects.get(
                    code_hack.color_name, (None, "Unknown effect")
                )[1]
                description = effect_desc
            else:
                description = "Unknown effect until used"

            # Get color from Colors class (loaded from JSON data_codes)
            code_color = Colors.get_color(code_hack.color_name.upper())

            return {
                "name": f"{code_hack.name}",
                "description": description,
                "entity_type": "code_hack",
                "details": f"Color: {code_hack.color_name.title()}",
                "color": code_color,
            }

        # Check for exploit pickup
        exploit_pickup = game.game_map.get_exploit_pickup(position)
        if exploit_pickup:
            exploit_def = GameData.EXPLOITS.get(exploit_pickup.exploit_key)
            if exploit_def:
                details = f"Category: {exploit_def.category.title()}\n"
                details += f"RAM: {exploit_def.ram} | Heat: {exploit_def.heat}"
                if exploit_def.damage > 0:
                    details += f" | Damage: {exploit_def.damage}"

                return {
                    "name": exploit_def.name,
                    "description": exploit_def.description,
                    "entity_type": "exploit_pickup",
                    "details": details,
                    "color": Colors.EXPLOIT_PICKUP,
                }

        # Check for permanent upgrade
        upgrade_key = game.game_map.permanent_upgrades.get((position.x, position.y))
        if upgrade_key:
            from game_data import GameUpgrades

            upgrade_def = GameUpgrades.UPGRADES.get(upgrade_key)
            if upgrade_def:
                details = f"Bonus: +{upgrade_def.bonus_amount} {upgrade_def.stat_type.upper()}"

                return {
                    "name": upgrade_def.name,
                    "description": upgrade_def.description,
                    "entity_type": "upgrade",
                    "details": details,
                    "color": Colors.UPGRADE,
                }

        # Check for story fragment
        story_fragment = game.game_map.story_fragments.get((position.x, position.y))
        if story_fragment:
            return {
                "name": "Data Fragment",
                "description": "Piece of hidden lore - collect to read",
                "entity_type": "story_fragment",
                "details": f"Fragment #{story_fragment.fragment_index}",
                "color": Colors.STORY_FRAGMENT,
            }

        return None

    @staticmethod
    def _inspect_special_tiles(game, position: Position) -> dict[str, Any] | None:
        """Check for special tiles (gateway, nodes)."""

        # Check for gateway
        if (
            game.game_map.gateway
            and position.x == game.game_map.gateway.x
            and position.y == game.game_map.gateway.y
        ):
            terrain_desc = EntityInspector._terrain_descriptions.get("gateway", {})
            return {
                "name": terrain_desc.get("name", "Network Gateway"),
                "description": terrain_desc.get("description", "Exit to next network level"),
                "entity_type": "gateway",
                "details": f"Level {game.level} exit",
                "color": Colors.GATEWAY,
            }

        # Check for cooling node
        if game.game_map.is_cooling_node(position):
            terrain_desc = EntityInspector._terrain_descriptions.get("cooling_node", {})
            return {
                "name": terrain_desc.get("name", "Cooling Node"),
                "description": terrain_desc.get("description", "Reduces heat"),
                "entity_type": "cooling_node",
                "details": "Step on to activate",
                "color": Colors.HEAT_RECOVERY,
            }

        # Check for CPU recovery node
        if game.game_map.is_cpu_recovery_node(position):
            terrain_desc = EntityInspector._terrain_descriptions.get("cpu_recovery_node", {})
            return {
                "name": terrain_desc.get("name", "CPU Recovery Node"),
                "description": terrain_desc.get("description", "Restores CPU"),
                "entity_type": "cpu_recovery_node",
                "details": "Step on to activate",
                "color": Colors.CPU_RECOVERY,
            }

        # Check for ghost node
        if game.game_map.is_ghost_node(position):
            terrain_desc = EntityInspector._terrain_descriptions.get("ghost_node", {})
            return {
                "name": terrain_desc.get("name", "Ghost Node"),
                "description": terrain_desc.get("description", "Reduces trace level"),
                "entity_type": "ghost_node",
                "details": "Step on to activate; also acts as blind spot",
                "color": Colors.CYAN,
            }

        return None

    @staticmethod
    def _inspect_terrain(game, position: Position) -> dict[str, Any]:
        """Inspect terrain at position."""

        # Check for wall
        if game.game_map.is_wall(position):
            terrain_desc = EntityInspector._terrain_descriptions.get("wall", {})
            return {
                "name": terrain_desc.get("name", "Security Barrier"),
                "description": terrain_desc.get("description", "Blocks movement and vision"),
                "entity_type": "wall",
                "details": "",
                "color": Colors.WALL,
            }

        # Check for blind spot
        if game.game_map.is_blind_spot(position):
            terrain_desc = EntityInspector._terrain_descriptions.get("blind_spot", {})
            return {
                "name": terrain_desc.get("name", "Blind Spot"),
                "description": terrain_desc.get("description", "Reduces enemy vision"),
                "entity_type": "blind_spot",
                "details": "Stealth bonus when hiding here",
                "color": Colors.BLIND_SPOT_VISIBLE,
            }

        # Default: floor
        terrain_desc = EntityInspector._terrain_descriptions.get("floor", {})
        return {
            "name": terrain_desc.get("name", "Data Corridor"),
            "description": terrain_desc.get("description", "Open network pathway"),
            "entity_type": "floor",
            "details": "",
            "color": Colors.FLOOR,
        }
