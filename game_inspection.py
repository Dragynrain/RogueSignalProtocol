#!/usr/bin/env python3
"""
Game Inspection Module
Provides entity inspection for look mode - identifies and describes entities at positions.
"""

from typing import Optional, Dict, Any
from game_entities import Position, Colors
from game_data import GameData
from data_loading import DataLoader


class EntityInspector:
    """Inspects game entities at positions and returns their information."""

    # Cache terrain descriptions from config
    _terrain_descriptions = None

    @classmethod
    def _load_terrain_descriptions(cls):
        """Load terrain descriptions from game_rules.json."""
        if cls._terrain_descriptions is None:
            config = DataLoader.load_config()
            cls._terrain_descriptions = config.get('terrain_descriptions', {})

    @staticmethod
    def get_entity_at_position(game, position: Position) -> Dict[str, Any]:
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
        5. Terrain (wall, shadow, floor)
        """
        EntityInspector._load_terrain_descriptions()

        # Check if position is valid
        if not position.is_valid(game.game_map.width, game.game_map.height):
            return {
                'name': 'Out of Bounds',
                'description': 'Invalid position',
                'entity_type': 'invalid',
                'details': '',
                'color': Colors.DARK_GRAY
            }

        # 1. Check for player
        if game.player.x == position.x and game.player.y == position.y:
            return EntityInspector._inspect_player(game)

        # 2. Check for enemies
        enemy = game.enemy_manager.get_enemy_at_position(position)
        if enemy:
            return EntityInspector._inspect_enemy(enemy)

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
    def _inspect_player(game) -> Dict[str, Any]:
        """Inspect the player."""
        player = game.player

        # Build status effects list
        status_effects = []
        if player.temporary_effects['speed_boost_turns'] > 0:
            status_effects.append(f"Speed Boost ({player.temporary_effects['speed_boost_turns']} turns)")
        if player.temporary_effects['enhanced_vision_turns'] > 0:
            status_effects.append(f"Enhanced Vision ({player.temporary_effects['enhanced_vision_turns']} turns)")
        if player.temporary_effects['exploit_efficiency_turns'] > 0:
            status_effects.append(f"Exploit Efficiency ({player.temporary_effects['exploit_efficiency_turns']} turns)")
        if player.temporary_effects.get('invisible_turns', 0) > 0:
            status_effects.append(f"Invisible ({player.temporary_effects['invisible_turns']} turns)")
        if player.temporary_effects['virus_turns'] > 0:
            status_effects.append(f"VIRUS ({player.temporary_effects['virus_turns']} turns)")
        if player.temporary_effects['movement_slowed_turns'] > 0:
            status_effects.append(f"Slowed ({player.temporary_effects['movement_slowed_turns']} turns)")

        status_text = "; ".join(status_effects) if status_effects else "None"

        details = f"CPU: {player.cpu}/{player.max_cpu} | Heat: {player.heat}/{player.max_heat}\n"
        details += f"RAM: {player.ram_total} | Trace: {player.trace_level}%\n"
        details += f"Status: {status_text}"

        return {
            'name': 'Player (You)',
            'description': 'Your digital infiltration agent',
            'entity_type': 'player',
            'details': details,
            'color': Colors.GREEN
        }

    @staticmethod
    def _inspect_enemy(enemy) -> Dict[str, Any]:
        """Inspect an enemy."""
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
            EnemyMovement.VIRUS: "Unpredictable"
        }.get(enemy_type.movement, "Unknown")

        details += f"Behavior: {movement_desc}"

        return {
            'name': enemy_type.name,
            'description': enemy_type.description,
            'entity_type': 'enemy',
            'details': details,
            'color': color
        }

    @staticmethod
    def _inspect_items(game, position: Position) -> Optional[Dict[str, Any]]:
        """Check for items at position (code hacks, exploits, upgrades, story fragments)."""
        from game_entities import Colors

        # Check for code hack
        code_hack = game.game_map.get_code_hack(position)
        if code_hack:
            # Check if we know the effect
            if code_hack.discovered or code_hack.color_name in game.discovered_code_effects:
                effect_desc = game.code_hack_effects.get(code_hack.color_name, (None, "Unknown effect"))[1]
                description = effect_desc
            else:
                description = "Unknown effect until used"

            # Get color from Colors class (loaded from JSON data_codes)
            code_color = Colors.get_color(code_hack.color_name.upper())

            return {
                'name': f"{code_hack.name}",
                'description': description,
                'entity_type': 'code_hack',
                'details': f"Color: {code_hack.color_name.title()}",
                'color': code_color
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
                    'name': exploit_def.name,
                    'description': exploit_def.description,
                    'entity_type': 'exploit_pickup',
                    'details': details,
                    'color': Colors.EXPLOIT_PICKUP
                }

        # Check for permanent upgrade
        upgrade_key = game.game_map.permanent_upgrades.get((position.x, position.y))
        if upgrade_key:
            from game_data import GameUpgrades
            upgrade_def = GameUpgrades.UPGRADES.get(upgrade_key)
            if upgrade_def:
                details = f"Bonus: +{upgrade_def.bonus_amount} {upgrade_def.stat_type.upper()}"

                return {
                    'name': upgrade_def.name,
                    'description': upgrade_def.description,
                    'entity_type': 'upgrade',
                    'details': details,
                    'color': Colors.UPGRADE
                }

        # Check for story fragment
        story_fragment = game.game_map.story_fragments.get((position.x, position.y))
        if story_fragment:
            return {
                'name': 'Data Fragment',
                'description': 'Piece of hidden lore - collect to read',
                'entity_type': 'story_fragment',
                'details': f"Fragment #{story_fragment.fragment_index}",
                'color': Colors.STORY_FRAGMENT
            }

        return None

    @staticmethod
    def _inspect_special_tiles(game, position: Position) -> Optional[Dict[str, Any]]:
        """Check for special tiles (gateway, nodes)."""

        # Check for gateway
        if game.game_map.gateway and position.x == game.game_map.gateway.x and position.y == game.game_map.gateway.y:
            terrain_desc = EntityInspector._terrain_descriptions.get('gateway', {})
            return {
                'name': terrain_desc.get('name', 'Network Gateway'),
                'description': terrain_desc.get('description', 'Exit to next network level'),
                'entity_type': 'gateway',
                'details': f"Level {game.level} exit",
                'color': Colors.GATEWAY
            }

        # Check for cooling node
        if game.game_map.is_cooling_node(position):
            terrain_desc = EntityInspector._terrain_descriptions.get('cooling_node', {})
            return {
                'name': terrain_desc.get('name', 'Cooling Node'),
                'description': terrain_desc.get('description', 'Reduces heat'),
                'entity_type': 'cooling_node',
                'details': 'Step on to activate',
                'color': Colors.HEAT_RECOVERY
            }

        # Check for CPU recovery node
        if game.game_map.is_cpu_recovery_node(position):
            terrain_desc = EntityInspector._terrain_descriptions.get('cpu_recovery_node', {})
            return {
                'name': terrain_desc.get('name', 'CPU Recovery Node'),
                'description': terrain_desc.get('description', 'Restores CPU'),
                'entity_type': 'cpu_recovery_node',
                'details': 'Step on to activate',
                'color': Colors.CPU_RECOVERY
            }

        # Check for ghost node
        if game.game_map.is_ghost_node(position):
            terrain_desc = EntityInspector._terrain_descriptions.get('ghost_node', {})
            return {
                'name': terrain_desc.get('name', 'Ghost Node'),
                'description': terrain_desc.get('description', 'Reduces trace level'),
                'entity_type': 'ghost_node',
                'details': 'Step on to activate; also acts as shadow',
                'color': Colors.CYAN
            }

        return None

    @staticmethod
    def _inspect_terrain(game, position: Position) -> Dict[str, Any]:
        """Inspect terrain at position."""

        # Check for wall
        if game.game_map.is_wall(position):
            terrain_desc = EntityInspector._terrain_descriptions.get('wall', {})
            return {
                'name': terrain_desc.get('name', 'Security Barrier'),
                'description': terrain_desc.get('description', 'Blocks movement and vision'),
                'entity_type': 'wall',
                'details': '',
                'color': Colors.WALL
            }

        # Check for shadow
        if game.game_map.is_shadow(position):
            terrain_desc = EntityInspector._terrain_descriptions.get('shadow', {})
            return {
                'name': terrain_desc.get('name', 'Shadow Zone'),
                'description': terrain_desc.get('description', 'Reduces enemy vision'),
                'entity_type': 'shadow',
                'details': 'Stealth bonus when hiding here',
                'color': Colors.SHADOW_VISIBLE
            }

        # Default: floor
        terrain_desc = EntityInspector._terrain_descriptions.get('floor', {})
        return {
            'name': terrain_desc.get('name', 'Data Corridor'),
            'description': terrain_desc.get('description', 'Open network pathway'),
            'entity_type': 'floor',
            'details': '',
            'color': Colors.FLOOR
        }
