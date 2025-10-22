# Debug Logging Implementation Plan

## Overview
Alpha builds now support DEBUG mode via `debug_mode.flag` file created during build. This plan outlines comprehensive debug logging to add throughout the game for effective alpha playtesting and bug tracking.

**Current State:**
- DEBUG_MODE infrastructure exists in RogueSignalProtocol.py
- Only 14 logging.debug() calls across 7 files (minimal coverage)
- 30 files have logging imported but most unused
- Debug logs write to `game_debug.log` in alpha builds

**Goal:**
Add strategic debug logging to capture gameplay state, AI decisions, combat calculations, and system events that will help diagnose player-reported bugs.

---

## 1. Enemy AI & Movement System

**Files:** `game_enemies.py`, `game_characters.py`

### High Priority
- **Enemy spawning** - Log enemy type, position, initial state, patrol route generation
- **AI state transitions** - IDLE → ALERT → CHASE transitions with reasons
- **Movement queue** - Log queue generation, invalidation reasons, chosen moves
- **Pathfinding** - Log pathfinding attempts, success/failure, path length
- **Alert propagation** - When enemies alert others, who alerted whom
- **Enemy death** - Position, killed by what, loot dropped

### Example Logging Points
```python
# game_enemies.py: spawn_enemy()
logging.debug(f"Spawned {enemy_type} at {position}, movement={enemy.movement_type}, patrol_points={len(enemy.patrol_points) if enemy.patrol_points else 0}")

# game_characters.py: Enemy.update_ai()
logging.debug(f"Enemy {self.char}@{self.position}: state={self.state}, can_see_player={can_see}, distance={distance}")

# game_characters.py: _ensure_queue_full()
logging.debug(f"Enemy {self.char}@{self.position}: Regenerating move queue (old_len={len(self.queued_moves)})")

# game_characters.py: _pathfind_to_player()
if path:
    logging.debug(f"Enemy {self.char}@{self.position}: Pathfinding success, path_length={len(path)}")
else:
    logging.debug(f"Enemy {self.char}@{self.position}: Pathfinding FAILED to player@{player_pos}")
```

---

## 2. Combat & Exploit System

**Files:** `game_combat.py`

### High Priority
- **Exploit usage attempts** - Which exploit, heat cost, overclock status
- **Targeting** - Target position, validation results, range checks
- **Damage calculations** - Base damage, modifiers, final damage, target HP before/after
- **Stun effects** - Who was stunned, duration
- **Status effects** - Application, duration, expiration
- **Heat management** - Heat before/after, overclock damage

### Example Logging Points
```python
# game_combat.py: use_exploit()
logging.debug(f"Player attempting exploit '{exploit_key}': heat={self.game.player.heat}/{self.game.player.max_heat}, cost={heat_cost}")

# game_combat.py: execute_exploit()
logging.debug(f"Executing {exploit.name} on target {target_position}: base_damage={base_damage}, final_damage={final_damage}")

# game_combat.py: _execute_ddos()
logging.debug(f"DDOS on {enemy.char}@{enemy.position}: damage={damage}, stun_turns={stun_turns}, remaining_hp={enemy.cpu}")

# game_combat.py: _calculate_heat_cost()
logging.debug(f"Heat cost for {exploit.name}: base={base_cost}, final={final_cost} (overclocked={is_overclock})")
```

---

## 3. Level Generation

**Files:** `game_level.py`, `game_level_structure.py`, `game_level_features.py`

### High Priority
- **Generation phases** - Start/end of each phase, timing
- **Room creation** - Room count, types, sizes, positions
- **Corridor generation** - MST edges, extra paths, total corridor tiles
- **Feature placement** - Shadows, cover, alcoves, intersections counts
- **Item/node placement** - What was placed where, placement attempts vs successes
- **Gateway placement** - Position, distance from spawn, placement attempts

### Example Logging Points
```python
# game_level.py: generate_level()
logging.debug(f"=== Level {level_num} Generation START (seed={seed}) ===")
logging.debug(f"Level {level_num} complete: rooms={len(rooms)}, corridors={corridor_count}, items={item_count}, enemies={enemy_count}")

# game_level_structure.py: generate_rooms()
logging.debug(f"Room {i}: type={room_type}, bounds=({x},{y},{w},{h}), tiles={tile_count}")

# game_level_features.py: place_gateway()
logging.debug(f"Gateway placement: attempt={attempt}, candidate={pos}, distance_from_spawn={dist:.1f}")
logging.debug(f"Gateway placed at {final_pos}, spawn_distance={final_dist:.1f}")
```

---

## 4. Save/Load System

**Files:** `game_save.py`

### High Priority
- **Save attempts** - When, what triggered save, success/failure
- **Load attempts** - File existence, version compatibility
- **Serialization errors** - Which field failed, value type mismatch
- **Save file deletion** - When and why (player death)
- **Data validation** - Missing fields, type mismatches during load

### Example Logging Points
```python
# game_save.py: save_game()
logging.debug(f"Save attempt {attempt+1}/{GameConfig.MAX_SAVE_ATTEMPTS}: level={game.level}, turn={game.turn}, player_hp={game.player.cpu}")
logging.debug(f"Save successful: {cls.SAVE_FILE}, size={file_size} bytes")

# game_save.py: load_game()
logging.debug(f"Loading save file: version={save_data['version']}, level={save_data['level']}, turn={save_data['turn']}")
logging.debug(f"Load complete: player@({player.x},{player.y}), hp={player.cpu}/{player.max_cpu}, enemies={len(enemies)}")

# game_save.py: delete_save()
logging.debug(f"Deleting save file: {cls.SAVE_FILE} (reason: player death)")
```

---

## 5. Player Actions & State

**Files:** `game_characters.py` (Player class), `game_engine.py`

### High Priority
- **Movement** - Intended position, actual position, blocked/allowed reasons
- **Inventory changes** - Items picked up/dropped, equip/unequip
- **Upgrade applications** - Which upgrade, stat changes before/after
- **Resource changes** - CPU damage/healing, heat gain/cooldown, trace level changes
- **Temporary effects** - Application, duration, expiration

### Example Logging Points
```python
# game_characters.py: Player.move()
logging.debug(f"Player move: from {self.position} to {new_position}, blocked={is_blocked}, reason={block_reason}")

# game_characters.py: Player.apply_permanent_upgrade()
logging.debug(f"Upgrade '{upgrade_key}': {stat_name} {old_value} → {new_value} (cap={cap})")

# game_engine.py: player damage
logging.debug(f"Player took {damage} damage: CPU {old_cpu} → {new_cpu}/{self.player.max_cpu}")

# game_characters.py: Player.update_effects()
logging.debug(f"Effects update: data_mimic={self.temporary_effects['data_mimic_turns']}, enhanced_vision={self.temporary_effects['enhanced_vision_turns']}")
```

---

## 6. Input Handling

**Files:** `game_input.py`, `game_ui.py`

### High Priority
- **Key events** - Which key pressed, current game mode/state
- **Mode transitions** - Entering/exiting targeting, look mode, menus, dialogues
- **Invalid input** - What was attempted, why it was rejected
- **Input context switches** - Normal → dialogue → targeting transitions

### Example Logging Points
```python
# game_input.py: handle_keydown()
logging.debug(f"Key event: {event.sym.name}, game_over={self.game.game_over}, dialogue_active={self.game.dialogue_state.is_active()}")

# game_input.py: _handle_targeting_input()
logging.debug(f"Targeting mode: key={event.sym.name}, cursor={self.game.targeting_cursor}, exploit={self.game.current_exploit}")

# game_input.py: _handle_dialogue_input()
logging.debug(f"Dialogue input: key={event.sym.name}, dialogue_id={self.game.dialogue_state.current_dialogue.id if self.game.dialogue_state.current_dialogue else None}")
```

---

## 7. FOV & Vision System

**Files:** `game_map.py`, `game_characters.py`

### High Priority
- **FOV computation** - Player position, vision range, compute time
- **Vision checks** - Player-to-enemy visibility, shadow interactions
- **Shadow mechanics** - When shadows block/allow vision
- **Line of sight** - LOS checks, wall blocking

### Example Logging Points
```python
# game_map.py: compute_fov()
logging.debug(f"FOV compute: player@{player_pos}, range={radius}, see_through_walls={light_walls}")

# game_characters.py: Player.can_see_enemy()
logging.debug(f"Visibility check: player→{enemy.char}@{enemy.position}, distance={distance:.1f}, in_shadow={in_shadow}, visible={result}")

# game_map.py: can_see_position()
logging.debug(f"LOS check: {start} → {end}, range={max_range}, visible={result}")
```

---

## 8. Turn Processing & Game State

**Files:** `game_state.py`, `game_engine.py`, `game_session.py`

### High Priority
- **Turn start/end** - Turn number, active effects count
- **Heat cooldown** - Heat before/after cooldown
- **Trace level changes** - Why trace changed, new value
- **Effect expiration** - Which effects expired this turn
- **Game state transitions** - Level progression, game over conditions

### Example Logging Points
```python
# game_state.py: TurnProcessor.process_turn()
logging.debug(f"=== Turn {game_state.turn} START: heat={player.heat}, trace={player.trace_level}, active_effects={len(player.temporary_effects)} ===")

# game_state.py: TurnProcessor._process_heat_cooldown()
logging.debug(f"Heat cooldown: {old_heat} → {new_heat} (-{cooldown})")

# game_state.py: TurnProcessor._process_trace_decay()
logging.debug(f"Trace decay: {old_trace} → {new_trace}")

# game_session.py: advance_level()
logging.debug(f"Level advance: {old_level} → {new_level}, dungeon_seed={self.game.game_state.dungeon_seed}")
```

---

## 9. Rendering System

**Files:** `game_rendering_core.py`, `game_rendering_graphics.py`, `game_rendering_glyphs.py`

### High Priority
- **Render mode switches** - ASCII ↔ Graphics mode changes
- **Coordinate conversions** - Console ↔ viewport ↔ pixel conversions
- **Sprite loading** - Which sprites loaded, failures
- **Texture atlas** - Atlas creation, tile dimensions
- **Window resize** - New dimensions, scale factors

### Example Logging Points
```python
# game_rendering_core.py: toggle_graphics_mode()
logging.debug(f"Graphics mode toggle: {old_mode} → {new_mode}")

# game_rendering_graphics.py: _init_sprite_system()
logging.debug(f"Sprite system init: tile_size=({w},{h}), atlas_size=({aw},{ah}), sprites_loaded={count}")

# game_coordinate_helpers.py: coordinate conversions
logging.debug(f"Coord conversion: console({cx},{cy}) → viewport({vx},{vy}) → pixel({px},{py})")
```

---

## 10. Data Loading & Configuration

**Files:** `data_loading.py`, `game_config.py`

### High Priority
- **JSON file loading** - Which files loaded, success/failure
- **Configuration validation** - Missing keys, type mismatches
- **Cache hits/misses** - Data loader cache usage
- **Settings changes** - User settings modifications

### Example Logging Points
```python
# data_loading.py: _load_json_file()
logging.debug(f"Loading JSON: {filename}, key={key}, cached={is_cached}")
logging.debug(f"JSON loaded: {filename}, size={data_size} entries")

# game_config.py: GameSettings modifications
logging.debug(f"Setting changed: {setting_name} = {old_value} → {new_value}")

# data_loading.py: PersistentStorage.save()
logging.debug(f"Saving user settings: {len(data)} entries to {filename}")
```

---

## 11. Error Handling & Exceptions

**Files:** `game_errors.py`, all modules

### High Priority
- **Caught exceptions** - Exception type, context, recovery action
- **Boundary violations** - Out of bounds positions, invalid array access
- **Null/None checks** - When None checks prevent crashes
- **Validation failures** - Invalid data, failed assertions

### Example Logging Points
```python
# Any module with try/except blocks
try:
    # risky operation
except SomeException as e:
    logging.debug(f"Exception caught in {function_name}: {type(e).__name__}: {e}")
    # recovery code

# Boundary checks
if not is_valid_position(pos):
    logging.debug(f"Invalid position rejected: {pos}, bounds=({width},{height})")
    return False
```

---

## 12. Audio System

**Files:** `game_audio.py`

### High Priority (Already has some logging, expand it)
- **Sound loading** - Which sounds loaded, file sizes, failures
- **Music playback** - Track changes, volume adjustments
- **Sound effects** - Which SFX played when, channel usage
- **Audio errors** - Missing files, playback failures

### Example Logging Points
```python
# game_audio.py: load_sound()
logging.debug(f"Sound loaded: {sound_id}, file={filename}, size={file_size}")

# game_audio.py: play_sound()
logging.debug(f"Playing sound: {sound_id}, volume={volume}, loop={loop}")

# game_audio.py: set_music_volume()
logging.debug(f"Music volume: {old_volume} → {new_volume}")
```

---

## Implementation Strategy

### Phase 1: Critical Systems (High Impact)
1. Enemy AI & Movement - Most common bug reports
2. Combat System - Complex calculations need visibility
3. Save/Load - Data corruption issues
4. Player Actions - Core gameplay verification

### Phase 2: Gameplay Systems
5. Level Generation - Verify procedural generation
6. Turn Processing - State management validation
7. FOV & Vision - Stealth mechanics verification

### Phase 3: Support Systems
8. Input Handling - Input validation
9. Rendering - Graphics mode issues
10. Data Loading - Configuration problems
11. Error Handling - Exception tracking
12. Audio - Sound system issues

### Implementation Guidelines

**DO:**
- Use `logging.debug()` for alpha-only logs
- Include relevant state: position, HP, turn number, etc.
- Log state BEFORE and AFTER changes when helpful
- Use clear, searchable prefixes (e.g., "Enemy AI:", "Combat:", "Save:")
- Include identifiers: enemy chars, exploit names, item IDs

**DON'T:**
- Log in tight loops without throttling (e.g., every pixel rendered)
- Log sensitive data (not applicable to this game)
- Log redundant information
- Use print() - always use logging.debug()

**Format Example:**
```python
logging.debug(f"Enemy AI: {self.char}@({self.x},{self.y}) state={self.state} → {new_state}, reason={reason}")
```

### Testing Approach

**After implementing debug logging:**
1. Run alpha build with `debug_mode.flag`
2. Play through typical gameplay scenarios
3. Review `game_debug.log` for:
   - Useful information density
   - Ability to trace bugs from symptoms
   - Performance impact (log file size growth)
4. Adjust logging verbosity as needed

---

## Expected Benefits

1. **Bug Reproduction** - Playtesters can share `game_debug.log` with bug reports
2. **State Reconstruction** - Trace exact game state when bug occurred
3. **AI Debugging** - Understand enemy behavior and pathfinding issues
4. **Balance Tuning** - See actual combat calculations, heat management
5. **Performance** - Identify slow systems (generation times, pathfinding)
6. **Regression Testing** - Compare logs before/after code changes

---

## File Size Considerations

**Mitigation strategies if `game_debug.log` grows too large:**

1. **Log rotation** - Archive old logs, start fresh each session
2. **Selective logging** - Add flags to enable/disable specific subsystems
3. **Log levels** - Use DEBUG for verbose, INFO for important events
4. **Compression** - Compress old logs for bug report submission
5. **Sampling** - Log every Nth occurrence for high-frequency events

**Current approach:** Start comprehensive, refine based on alpha testing feedback.

---

## Next Steps

1. ✅ Plan created (this document)
2. ✅ Implement Phase 1 (Critical Systems) - COMPLETED
   - Enemy AI & Movement System (game_enemies.py, game_characters.py)
   - Combat & Exploit System (game_combat.py)
   - Save/Load System (game_save.py)
   - Player Actions & State (game_characters.py, game_state.py)
3. ⬜ Test with alpha build
4. ⬜ Implement Phase 2 (Gameplay Systems)
5. ⬜ Test with alpha build
6. ⬜ Implement Phase 3 (Support Systems)
7. ⬜ Final alpha test with full logging
8. ⬜ Adjust verbosity based on feedback

---

## Notes

- All logging should check DEBUG_MODE flag where performance matters
- Most logging can be unconditional (logging.debug() is disabled in release)
- Add logging AS you touch systems, not all at once
- Prioritize systems with historical bug reports
- Review logs after each alpha playtest session
