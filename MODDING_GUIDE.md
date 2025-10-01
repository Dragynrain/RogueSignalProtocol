# Rogue Signal Protocol - Modding Guide

This guide explains how to modify the JSON configuration files to customize game balance, add new content, and create mods for Rogue Signal Protocol.

## JSON Data Files Overview

### 1. `game_data.json` - Core Game Content

Contains all the primary game content and balance values that can be easily modified for balancing or modding.

#### Enemy Types

Located in the `enemy_types` section. Each enemy has these properties:

- `symbol`: Single character displayed on map (A-Z reserved for enemies)
- `cpu`: Health points of the enemy
- `vision`: How far the enemy can see (in tiles)
- `movement`: AI behavior type (`STATIC`, `RANDOM`, `SEEK`, `TRACK`, `PATROL`, `LINEAR`)
- `name`: Display name
- `damage`: Damage dealt to player on contact
- `description`: Flavor text for UI

Example:
```json
"scanner": {
  "symbol": "S",
  "cpu": 35,
  "vision": 4,
  "movement": "STATIC",
  "name": "Scanner",
  "damage": 0,
  "description": "High vision, no attack - pure detection"
}
```

#### Exploits (Player Abilities)

Located in the `exploits` section. Each exploit has these properties:

- `name`: Display name
- `ram`: RAM cost to equip
- `heat`: Heat cost to use
- `range`: Range in tiles (0 = self-target)
- `category`: Category for UI sorting (`stealth`, `combat`, `utility`, `emergency`)
- `damage`: Base damage dealt
- `targeting`: Target mode (`NONE`, `SINGLE`, `AREA`)
- `description`: Effect description

Example:
```json
"shadow_step": {
  "name": "Shadow Step",
  "ram": 3,
  "heat": 30,
  "range": 6,
  "category": "stealth",
  "damage": 0,
  "targeting": "SINGLE",
  "description": "Teleport to any shadow zone within range (6 tiles)"
}
```

#### Upgrades

Located in the `upgrades` section. Permanent stat boosts found throughout levels:

- `name`: Display name
- `symbol`: Character displayed on map
- `color`: RGB color array [r, g, b] (0-255)
- `stat_type`: Which stat to boost (`ram`, `cpu`, `heat`)
- `bonus_amount`: How much to increase the stat

#### Network Configs (Level Settings)

Located in the `network_configs` section. Defines level-specific spawning and generation:

- `enemies`: Number of enemies to spawn
- `shadow_coverage`: Percentage of map covered by shadows (0.0-1.0)
- `name`: Level name for UI
- `background_detection`: Passive detection increase rate
- `cooling_nodes`: Number of heat recovery nodes
- `cpu_nodes`: Number of CPU recovery nodes
- `ghost_nodes`: Number of ghost nodes (temporary invisibility)
- `data_patches`: Number of code hack items
- `exploit_pickups`: Number of exploit items
- `permanent_upgrades`: Number of permanent upgrade items

#### Balance Configuration

Located in the `balance` section. Contains fine-tuning values for game mechanics:

**Player Stats:**
- `starting_cpu`, `max_cpu`: Player health values
- `starting_heat`, `max_heat`: Heat system limits
- `starting_ram`: Initial RAM capacity
- `base_vision_range`: How far player can see

**Temporary Effects:**
- `data_mimic_duration`: Invisibility duration in turns
- `exploit_efficiency_multiplier`: Heat cost reduction when boosted
- `virus_damage_per_turn`: Damage from virus effect

**Combat:**
- `enemy_elimination_cpu_reward`: CPU restored when defeating enemies
- `disable_duration_*`: How long various disable effects last

**Code Patches (Consumable Items):**
- `cpu_restore_min/max`: Random CPU restoration range
- `heat_reduction_instant`: Heat reduced by cooling items
- `detection_reduction`: Detection reduced by stealth items

### 2. `game_config.json` - UI and System Settings

Contains display, interface, and system configuration:

#### Screen & Map
- `screen`: Display dimensions (`width`, `height`)
- `map`: Game world dimensions (`width`, `height`)

#### UI Layout
- `ui`: Interface layout settings (panel sizes, spacing)

#### Colors
- `colors`: RGB color definitions for all game elements
- Organized by category: `basic`, `game_elements`, `enemies`, `ui`, etc.

#### Symbols & Characters
- `symbols`: Numeric codes for special characters
- `characters`: ASCII characters for walls and decorations

### 3. `story_content.json` - Narrative Content

Contains the story fragments discovered during gameplay:

- `fragments`: Array of story text strings
- `metadata`: Information about fragment count and version

### 4. `user_settings.json` - Player Preferences

Player-specific settings that persist between sessions:

- `master_volume`: Overall volume (0.0-1.0)
- `sfx_volume`: Sound effects volume (0.0-1.0)
- `music_volume`: Background music volume (0.0-1.0)
- `graphics_mode`: Display mode (`terminal`, `graphics`, `ascii`)

## Modding Tips

### Balance Modifications

1. **Enemy Difficulty**: Adjust `cpu`, `vision`, and `damage` values in enemy types
2. **Player Power**: Modify exploit `heat`, `damage`, and `range` values
3. **Resource Economy**: Change `ram` costs and heat generation/recovery rates
4. **Level Progression**: Adjust `network_configs` for different level difficulties

### Adding New Content

#### New Enemy Type
1. Add entry to `enemy_types` section
2. Use unique symbol (A-Z recommended for enemies)
3. Choose appropriate movement type for desired behavior
4. Balance stats relative to existing enemies

#### New Exploit
1. Add entry to `exploits` section
2. Choose appropriate category and targeting mode
3. Balance RAM, heat, and damage costs
4. Provide clear description of effect

#### New Level Configuration
1. Add numbered entry to `network_configs`
2. Scale enemy count and item spawns appropriately
3. Adjust shadow coverage for desired stealth difficulty

### Color Themes

Modify the `colors` section in `game_config.json` to create custom visual themes:

- `game_elements`: Core gameplay object colors
- `enemies`: Enemy state indication colors  
- `ui`: Interface and text colors
- `message_log`: Message type colors

### Validation

Always run data validation after making changes:

```bash
python data_validation.py
```

This will check for:
- Missing required fields
- Invalid value ranges
- Incorrect data types
- Structural issues

## Backup and Safety

1. **Always backup** original JSON files before modifying
2. **Test changes incrementally** - modify one thing at a time
3. **Use the validation tool** to catch errors early
4. **Keep notes** of what you changed for troubleshooting

## Advanced Modding

### Custom Balance Profiles

Create different JSON file sets for different gameplay experiences:
- `game_data_easy.json` - Lower difficulty settings
- `game_data_hardcore.json` - Extreme challenge mode
- `game_data_speedrun.json` - Optimized for fast completion

### Community Sharing

When sharing mods:
1. Document what you changed and why
2. Include validation test results
3. Provide installation instructions
4. Test thoroughly across different scenarios

## Troubleshooting

**Game won't start after changes:**
- Run `data_validation.py` to check for syntax errors
- Verify all numeric values are within reasonable ranges
- Check that all required fields are present

**Balancing issues:**
- Enemies too easy/hard: Adjust `cpu`, `vision`, `damage`
- Player too weak/strong: Modify exploit costs and effects
- Levels too empty/crowded: Change spawn counts in network configs

**Visual issues:**
- Colors not displaying: Check RGB values are 0-255
- Symbols missing: Verify character codes are valid
- UI layout broken: Check dimension values in screen/map settings

For more help, check the game's issue tracker or community forums.