# Test Coverage Improvement Plan

**Document Version:** 2.0
**Created:** 2025-11-09
**Updated:** 2025-11-10
**Status:** Planning Phase

---

## Executive Summary

After the recent test suite purge that eliminated ~3,340 lines of redundant tests, this plan addresses the **critical gaps** in test coverage. Analysis revealed **22 major coverage gaps** across core game systems, with emphasis on untested modules, integration weaknesses, and missing smoke tests.

**Current State:**
- 98 test files, 1,582 passing tests
- Strong agent framework (GameTestAgent, ChaosAgent, etc.)
- Good fixture library (standard_patterns, real_game_data)
- Well-covered: stealth, combat, AI, save/load, config validation

**Critical Findings:**
- 🔴 **5 core modules have ZERO test coverage** (particle system, victory screen, tile dimensions, visibility manager)
- 🟡 **End-to-end smoke tests missing** (no full playthrough validation)
- 🟡 **Graphics mode switching weakly tested** (crashes possible)
- 🟢 **Agent framework underutilized** (7 new agents proposed)

---

## Phases

**Phase 1: CRITICAL GAPS - Game-Breaking Issues**
Complexity: High | Priority: P0 - Blocks release
Dependencies: None

**Phase 2: HIGH PRIORITY - Important Systems**
Complexity: Medium-High | Priority: P1 - Should have for quality
Dependencies: None (can start in parallel with Phase 1)

**Phase 3: MEDIUM PRIORITY - Confidence Builders**
Complexity: Medium | Priority: P2 - Nice to have
Dependencies: Phase 1 complete

**Phase 4: LOW PRIORITY - Polish & Edge Cases**
Complexity: Low-Medium | Priority: P3 - Future improvement
Dependencies: Phases 1-2 complete

---

## Phase 1: CRITICAL GAPS - Game-Breaking Issues

**Goal:** Eliminate bugs that crash the game or break core gameplay

### 1.1 Particle System - ZERO COVERAGE
**Module:** `game_particle_system.py`
**Complexity:** Straightforward
**Risk Level:** 🔴 CRITICAL

**What's Missing:**
- Visual effects for exploits (bullets, explosions, sparks)
- Performance under heavy particle load (100+ particles)
- Particle lifecycle management (spawn → update → cleanup)
- Memory leaks from unreleased particles
- Rendering integration with game loop

**Why Critical:**
- Performance degradation over time (memory leaks)
- Visual glitches during combat (particles don't clear)
- Crashes when many particles spawn simultaneously
- Every exploit uses particles - high usage feature

**Tests Needed:**
```
Unit Tests (straightforward):
- test_particle_spawn_with_valid_params
- test_particle_update_lifecycle
- test_particle_cleanup_after_ttl
- test_particle_memory_management

Integration Tests (straightforward):
- test_exploit_triggers_particles
- test_particles_render_without_lag
- test_multiple_exploits_particle_overlap

Performance Tests (straightforward):
- test_spawn_100_particles_performance
- test_particle_cleanup_prevents_leak
- test_long_session_no_particle_buildup
```

**Acceptance Criteria:**
- ✓ All particle types spawn correctly
- ✓ Particles clean up automatically (no leaks)
- ✓ 100+ particles maintain 60 FPS
- ✓ Memory usage stable over 1000+ turn session

---

### 1.2 Victory Screen - ZERO COVERAGE
**Module:** `game_victory_screen.py`
**Complexity:** Trivial
**Risk Level:** 🔴 CRITICAL

**What's Missing:**
- Victory screen rendering and layout
- Victory animation/particle effects
- Victory screen input handling (dismiss, view stats)
- Transition from level 3 gateway to victory screen
- Victory music/audio integration
- Victory stats display (turns, enemies defeated, etc.)

**Why Critical:**
- Victory is THE PAYOFF MOMENT - bugs here ruin player experience
- Victory screen crash after beating game = terrible UX
- Stats not displaying correctly = lost sense of accomplishment
- Can't restart/quit from victory screen = player stuck in game

**Tests Needed:**
```
Integration Tests (trivial):
- test_level_3_gateway_triggers_victory
- test_victory_screen_renders_correctly
- test_victory_stats_display_accurate
- test_victory_screen_accepts_input
- test_victory_music_plays

Smoke Test (trivial):
- test_full_game_victory_flow
  Level 3 completion → Victory screen → Stats → Dismiss → Main menu
```

**Acceptance Criteria:**
- ✓ Level 3 completion triggers victory screen
- ✓ Victory screen renders without errors
- ✓ Stats display correctly (turns, enemies, items)
- ✓ Player can dismiss and return to main menu
- ✓ Victory music/audio plays

---

### 1.3 Tile Dimension Calculator - ZERO COVERAGE
**Module:** `game_tile_dimension_calculator.py`
**Complexity:** Trivial
**Risk Level:** 🔴 CRITICAL

**What's Missing:**
- Dynamic tile sizing for different resolutions
- Aspect ratio calculations for widescreen/ultrawide
- Font scaling for graphics mode
- Window resize handling
- Edge cases (tiny windows, 4K/8K displays)

**Why Critical:**
- Rendering bugs affect EVERY SINGLE FRAME
- Wrong tile sizes = broken graphics mode (unplayable)
- Bad calculations = text/sprites misaligned
- Resolution changes = crashes or visual corruption

**Tests Needed:**
```
Unit Tests (trivial - pure math):
- test_tile_size_1920x1080
- test_tile_size_1280x720
- test_tile_size_3840x2160_4k
- test_tile_size_7680x4320_8k
- test_ultrawide_aspect_ratio
- test_tiny_window_minimum_size
- test_font_scaling_calculation
- test_window_resize_recalculates
```

**Acceptance Criteria:**
- ✓ Common resolutions (1080p, 1440p, 4K) calculate correctly
- ✓ Ultrawide monitors supported (21:9, 32:9)
- ✓ Minimum window size enforced (no crash on tiny window)
- ✓ Font scaling proportional to resolution
- ✓ Window resize triggers recalculation

---

### 1.4 Visibility Manager - ZERO COVERAGE
**Module:** `game_visibility_manager.py`
**Complexity:** Straightforward
**Risk Level:** 🔴 CRITICAL

**What's Missing:**
- FOV calculations (TCOD integration)
- Explored tiles persistence across turns
- Performance with large FOV radius
- Edge cases (corners, long hallways, blind spots)
- FOV updates on player movement
- Vision range modifications (enhanced vision upgrade)

**Why Critical:**
- Vision = CORE GAMEPLAY MECHANIC (stealth game)
- FOV bugs = player blind or sees through walls (game-breaking)
- Performance issues = game stutters every move (unplayable)
- Explored tiles not saving = confusing map navigation

**Tests Needed:**
```
Unit Tests (straightforward):
- test_fov_calculation_accuracy
- test_fov_blocked_by_walls
- test_fov_radius_scaling
- test_fov_corner_edge_cases
- test_explored_tiles_persist
- test_fov_performance_large_radius

Integration Tests (straightforward):
- test_fov_updates_on_movement
- test_fov_with_blind_spots
- test_enhanced_vision_expands_fov
- test_fov_with_enemy_detection
- test_explored_tiles_save_load
```

**Acceptance Criteria:**
- ✓ FOV accurately reflects line-of-sight
- ✓ Walls block vision correctly
- ✓ Explored tiles persist across turns
- ✓ FOV calculation < 1ms per update
- ✓ Enhanced vision upgrade extends FOV correctly

---

### 1.5 Graphics Mode Switching - WEAK COVERAGE
**Modules:** `game_graphics.py`, `game_tile_manager.py`, rendering pipeline
**Complexity:** Complex
**Risk Level:** 🔴 CRITICAL (high-risk - multiple systems)

**What's Missing:**
- Switching between glyph/graphics modes DURING gameplay (not just startup)
- State preservation across mode changes
- Tile manager initialization and cleanup
- Rendering pipeline switch without artifacts
- Mouse coordinate conversion after mode switch
- Memory cleanup from unloaded tiles

**Why Critical:**
- Players switch modes frequently (F11 hotkey)
- Mode switch crash = lost progress (no autosave)
- Rendering artifacts after switch = broken visuals
- Mouse clicks misaligned after switch = unplayable
- Memory leaks from unloaded tiles

**Tests Needed:**
```
Integration Tests (complex - multiple systems):
- test_mode_switch_glyph_to_graphics
- test_mode_switch_graphics_to_glyph
- test_multiple_mode_switches
- test_mode_switch_preserves_game_state
- test_mode_switch_mouse_coordinates_update
- test_mode_switch_during_combat
- test_mode_switch_with_menu_open
- test_mode_switch_memory_cleanup
- test_mode_switch_rendering_no_artifacts
```

**Acceptance Criteria:**
- ✓ Mode switch completes without crash
- ✓ Game state preserved (position, enemies, items)
- ✓ Mouse coordinates recalculate correctly
- ✓ No rendering artifacts after switch
- ✓ Memory usage stable after multiple switches

---

### 1.6 VictoryRunAgent - NEW AGENT
**Type:** Test Agent
**Complexity:** Moderate (extends existing agent pattern)
**Risk Level:** 🔴 CRITICAL

**What's Missing:**
- Automated agent that plays through entire game to victory
- Tests full game loop without manual intervention
- Validates level progression, combat, items, victory screen
- Performance testing over long session

**Why Critical:**
- Integration bugs only show up in long sessions (500+ turns)
- Memory leaks accumulate over time
- State corruption manifests after multiple level transitions
- Victory screen bugs won't be caught without full playthrough

**Implementation:**
```python
class VictoryRunAgent(GameTestAgent):
    """
    Plays optimally through all 3 levels to reach victory screen.

    Strategy:
    - Level 1: Explore, collect items, find gateway
    - Level 2: Upgrade weapons, defeat enemies, progress
    - Level 3: Final push to gateway, trigger victory

    Validates:
    - Level transitions work correctly
    - Items/upgrades carry between levels
    - Enemy scaling per level
    - Victory screen triggers and displays
    - No crashes over 500-1000 turn session
    """
```

**Tests Using Agent:**
```
- test_victory_run_completes_without_crash
- test_victory_run_all_levels
- test_victory_run_memory_stable
- test_victory_run_performance_acceptable
- test_victory_stats_accurate
```

**Acceptance Criteria:**
- ✓ Agent completes full game 100% of time
- ✓ Victory screen reached within reasonable turn count
- ✓ Memory usage remains stable throughout run
- ✓ No crashes, errors, or warnings
- ✓ Victory stats match actual gameplay

---

### 1.7 Full Playthrough Smoke Tests
**Type:** Integration Smoke Tests
**Complexity:** Straightforward (uses existing agent framework)
**Risk Level:** 🔴 CRITICAL

**What's Missing:**
- "First 5 Minutes of Gameplay" smoke test
- Complete game flow validation (start → victory)
- All exploits usage smoke test
- All menus navigation smoke test

**Why Critical:**
- Catches most common player-facing bugs
- Validates entire game loop integrity
- Ensures player experience is smooth
- Regression detection for major features

**Tests Needed:**
```
Smoke Test 1: First 5 Minutes (straightforward)
- test_first_5_minutes_new_game
  New game → Move around → Kill enemy → Find item → Open menu → Close menu
  Validates: Basic gameplay loop, no early crashes

Smoke Test 2: Complete Victory Run (straightforward)
- test_complete_game_smoke
  Start → Level 1 → Level 2 → Level 3 → Victory screen
  Validates: Full game progression, all systems working together

Smoke Test 3: All Exploits (trivial)
- test_all_exploits_smoke
  Equip each exploit type, use successfully once
  Validates: No exploit definition errors, all exploits work

Smoke Test 4: All Menus (trivial)
- test_all_menus_smoke
  Open every menu, navigate, close cleanly
  Validates: No menu crashes, navigation works

Smoke Test 5: Graphics Mode Switch (straightforward)
- test_graphics_mode_switch_smoke
  Start glyph → Play 100 turns → Switch to graphics → Play 100 turns → Switch back
  Validates: Mode switching during gameplay
```

**Acceptance Criteria:**
- ✓ First 5 min smoke completes without errors
- ✓ Complete victory run succeeds
- ✓ All exploits fire successfully
- ✓ All menus open/close cleanly
- ✓ Graphics mode switches work mid-game

---

## Phase 2: HIGH PRIORITY - Important Systems

**Goal:** Robust coverage of important game systems

### 2.1 Enemy Queue System Edge Cases - WEAK
**Module:** Enemy movement queue (3-length tactical prediction)
**Complexity:** Moderate
**Risk Level:** 🟡 HIGH

**What's Missing:**
- Queue invalidation scenarios (state change mid-queue)
- Blocked movement in queue (obstacle appears)
- Queue regeneration logic timing
- Concurrent queue updates (multiple enemies moving)
- Queue display vs actual movement mismatch

**Why Important:**
- Queue bugs = unpredictable enemy behavior
- Enemies freeze, teleport, or act randomly
- Queue shows wrong moves (breaks tactical planning)
- Player can't predict enemy actions = broken core mechanic

**Tests Needed:**
```
Integration Tests (moderate complexity):
- test_queue_invalidation_on_state_change
- test_queue_invalidation_on_blocked_path
- test_queue_regeneration_logic
- test_multiple_enemy_queue_updates
- test_queue_display_matches_movement
- test_queue_with_pathfinding_timeout
- test_queue_preserved_on_save_load
```

**Acceptance Criteria:**
- ✓ Queue invalidates on all state changes
- ✓ Blocked movements regenerate queue
- ✓ Queue always shows accurate next 3 moves
- ✓ Multiple enemies update independently
- ✓ Queue persists through save/load

---

### 2.2 Exploit Edge Cases - PARTIAL COVERAGE
**Module:** Exploit system, targeting, execution
**Complexity:** Moderate
**Risk Level:** 🟡 HIGH

**What's Missing:**
- Exploit usage when player is low HP/heat
- Exploit targeting with cursor at edge of range
- Multiple exploits used in same turn (speed boost active)
- Exploit + item use in same turn (valid?)
- Area exploits hitting walls/empty space
- Exploit + enemy death timing (exploit fires, enemy dies mid-animation)
- Exploit overheating (heat exceeds max)
- Exploit with insufficient resources (not enough RAM)

**Why Important:**
- Exploits are PRIMARY COMBAT MECHANIC
- Edge case bugs = exploit doesn't work when needed most
- Crash during exploit = lost tactical advantage
- Unexpected behavior = player confusion/frustration

**Tests Needed:**
```
Integration Tests (moderate - many scenarios):
- test_exploit_usage_low_health
- test_exploit_usage_high_heat
- test_exploit_targeting_edge_of_range
- test_exploit_targeting_out_of_range
- test_multiple_exploits_speed_boost
- test_exploit_and_item_same_turn
- test_area_exploit_hits_walls
- test_area_exploit_empty_space
- test_exploit_enemy_dies_during
- test_exploit_overheat_prevention
- test_exploit_insufficient_ram
- test_exploit_targeting_moving_enemy
```

**Acceptance Criteria:**
- ✓ Exploits work correctly at all health/heat levels
- ✓ Range targeting validated before execution
- ✓ Multiple exploits in one turn handled
- ✓ Area exploits handle obstacles correctly
- ✓ Resource checks prevent invalid usage

---

### 2.3 Inventory Full/Overflow - WEAK
**Module:** Inventory management, item pickup
**Complexity:** Straightforward
**Risk Level:** 🟡 HIGH

**What's Missing:**
- Inventory at max capacity, try to pick up item
- Inventory overflow error handling
- Equipping exploit when slots full (need to swap?)
- Dropping items behavior and validation
- Item stack limits (if stackable items exist)
- Inventory state on save/load with full inventory

**Why Important:**
- Inventory bugs = lost items or crashes
- Pick up item with full inventory → crash = very bad
- Item disappears into void = player loses progress
- Can't equip despite having space = frustrating

**Tests Needed:**
```
Integration Tests (straightforward):
- test_pickup_item_inventory_full
- test_equip_exploit_slots_full
- test_inventory_overflow_handling
- test_drop_item_from_full_inventory
- test_max_capacity_validation
- test_full_inventory_save_load
- test_inventory_display_when_full
```

**Acceptance Criteria:**
- ✓ Attempting pickup when full shows message
- ✓ No crashes on full inventory operations
- ✓ Items don't disappear
- ✓ Equipping with full slots swaps correctly
- ✓ Full inventory persists through save/load

---

### 2.4 Menu Navigation Flows - PARTIAL
**Module:** Menu system, menu stack, UI navigation
**Complexity:** Moderate
**Risk Level:** 🟡 HIGH

**What's Missing:**
- Complete menu navigation paths (all menus → all submenus)
- Menu stack management (open inventory → help → lore → back → back → back)
- Menu + game state interaction (open menu mid-exploit animation)
- Menu rendering with achievement popup overlap
- Menu mouse regions on different resolutions
- Menu + dialogue system interaction
- Menu escape key handling at all levels

**Why Important:**
- Menus are CORE UX (players use constantly)
- Can't close menu = stuck in menu (requires restart)
- Menu stack corrupt = game state broken
- Menu overlaps obscure critical gameplay info

**Tests Needed:**
```
Integration Tests (moderate complexity):
- test_inventory_navigation_complete
- test_help_menu_navigation_complete
- test_lore_viewer_navigation_complete
- test_achievements_menu_navigation
- test_settings_menu_navigation
- test_menu_stack_depth_handling
- test_menu_during_exploit_animation
- test_menu_with_achievement_popup
- test_menu_with_dialogue_active
- test_menu_mouse_regions_all_resolutions
- test_menu_escape_key_all_levels
```

**Acceptance Criteria:**
- ✓ All menus open and close correctly
- ✓ Menu stack handles deep nesting
- ✓ Escape key consistently closes top menu
- ✓ Menus don't interfere with gameplay
- ✓ Mouse regions correct at all resolutions

---

### 2.5 Performance/Stress Tests - MISSING
**Type:** Performance validation
**Complexity:** Straightforward (extend agent framework)
**Risk Level:** 🟡 HIGH

**What's Missing:**
- Long-running game session (5000+ turns)
- Many enemies on screen (20+ enemies simultaneously)
- Particle spam (100+ particles active)
- Rapid exploit usage (100 exploits in 100 turns)
- Large explored map (explore 80%+ of level)
- Memory leak detection over time

**Why Important:**
- Performance degrades over time (hard to notice in short tests)
- Memory leaks compound and eventually crash game
- FPS drops after extended play (bad UX)
- Game becomes unresponsive after long session

**Tests Needed:**
```
Performance Tests (straightforward):
- test_long_session_5000_turns
- test_many_enemies_20_plus
- test_particle_spam_100_active
- test_rapid_exploit_usage
- test_large_explored_area
- test_memory_leak_detection
- test_fps_stability_long_session
```

**Acceptance Criteria:**
- ✓ 5000 turn session completes without crash
- ✓ 20+ enemies maintain 60 FPS
- ✓ 100+ particles maintain 30+ FPS
- ✓ Memory usage stable over time (< 10% growth)
- ✓ No FPS degradation after 1000+ turns

---

### 2.6 Autowalk Interruption - WEAK
**Module:** Autowalk pathfinding, interruption logic
**Complexity:** Trivial
**Risk Level:** 🟡 MEDIUM-HIGH

**What's Missing:**
- Autowalk interrupted by enemy spotting player
- Autowalk interrupted by player taking damage
- Autowalk interrupted by exploit usage
- Autowalk interrupted by menu opening
- Autowalk path invalidation (wall/obstacle appears mid-walk)
- Autowalk cancel via user input (any key)

**Why Important:**
- Autowalk bugs = player walks into danger
- Walk into enemy = unwanted combat/death
- Walk into trap = unintended damage
- Can't cancel autowalk = loss of control

**Tests Needed:**
```
Integration Tests (trivial):
- test_autowalk_interrupted_by_enemy
- test_autowalk_interrupted_by_damage
- test_autowalk_interrupted_by_exploit
- test_autowalk_interrupted_by_menu
- test_autowalk_path_invalidated
- test_autowalk_cancel_any_key
- test_autowalk_end_reached
```

**Acceptance Criteria:**
- ✓ Autowalk cancels on all interruption conditions
- ✓ Player maintains control after cancel
- ✓ No autowalk into danger scenarios
- ✓ Any key cancels autowalk immediately
- ✓ Path invalidation handled gracefully

---

### 2.7 New Test Agents: StealthAgent & CombatAgent
**Type:** Test Agents
**Complexity:** Moderate (extends existing pattern)
**Risk Level:** 🟡 MEDIUM-HIGH

**StealthAgent (moderate complexity):**
```python
class StealthAgent(GameTestAgent):
    """
    Avoids detection entire level, tests stealth mechanics.

    Strategy:
    - Use blind spots for cover
    - Track enemy patrol routes
    - Time movements between patrols
    - Use stealth items (if available)
    - Reach gateway without detection

    Validates:
    - Blind spots actually block detection
    - Enemy FOV accurate
    - Patrol routes predictable
    - Stealth mechanics working
    """
```

**CombatAgent (moderate complexity):**
```python
class CombatAgent(GameTestAgent):
    """
    Aggressive playstyle, kills all enemies on level.

    Strategy:
    - Seek out enemies actively
    - Use exploits optimally
    - Manage heat/HP carefully
    - Test all combat scenarios

    Validates:
    - Combat system robustness
    - Exploit effectiveness
    - Enemy AI reactions
    - Resource management
    """
```

**Tests Using Agents:**
- test_stealth_agent_completes_level_undetected
- test_combat_agent_defeats_all_enemies
- test_stealth_agent_blind_spot_usage
- test_combat_agent_exploit_variety

---

## Phase 3: MEDIUM PRIORITY - Confidence Builders

**Goal:** Edge case coverage and quality improvements

### 3.1 Trace Level Management
**Module:** Trace level system
**Complexity:** Trivial
**Risk Level:** 🟢 MEDIUM

**What's Missing:**
- Trace level decay rate validation
- Trace level floor (minimum trace, never 0?)
- Trace level + ghost node interaction timing
- Trace level + exploit usage (does exploit use increase trace?)
- Trace level + level transition (reset? carry over?)

**Tests Needed:**
- test_trace_decay_rate_accurate
- test_trace_floor_minimum_value
- test_trace_ghost_node_interaction
- test_trace_exploit_usage_effect
- test_trace_level_transition

---

### 3.2 Heat Management Edge Cases
**Module:** Heat system, overheat mechanics
**Complexity:** Trivial
**Risk Level:** 🟢 MEDIUM

**What's Missing:**
- Heat at max, use exploit (overheat prevention?)
- Heat + cooling node timing (immediate or next turn?)
- Heat + death (does heat matter when dead?)
- Heat decay over turns (passive cooling)
- Heat + speed boost (multiple actions affect heat?)

**Tests Needed:**
- test_heat_at_max_exploit_usage
- test_heat_cooling_node_timing
- test_heat_on_death
- test_heat_passive_decay
- test_heat_speed_boost_interaction

---

### 3.3 Dialogue System Edge Cases
**Module:** Dialogue system
**Complexity:** Trivial
**Risk Level:** 🟢 MEDIUM

**What's Missing:**
- Dialogue during combat (interruption?)
- Dialogue preferences persistence (save/load)
- Dialogue wrapping at different resolutions (text overflow?)
- Multiple dialogues queued (queue system working?)
- Dialogue + achievement popup overlap

**Tests Needed:**
- test_dialogue_during_combat
- test_dialogue_preferences_persist
- test_dialogue_text_wrapping
- test_dialogue_queue_multiple
- test_dialogue_achievement_popup_overlap

---

### 3.4 Audio System Edge Cases
**Module:** Audio system, sound manager
**Complexity:** Trivial
**Risk Level:** 🟢 MEDIUM

**What's Missing:**
- Audio volume 0 (verify no crashes, just silence)
- Audio file missing/corrupt (graceful degradation)
- Rapid audio events (100 sounds in 1 second - prevent spam)
- Music transition timing (fade in/out smooth)
- Audio + game loop performance (audio doesn't block gameplay)

**Tests Needed:**
- test_audio_volume_zero
- test_audio_missing_file
- test_audio_rapid_events
- test_music_transition_smooth
- test_audio_performance_no_block

---

### 3.5 Map Generation Extremes
**Module:** Level generation, BSP, seed validation
**Complexity:** Straightforward (fuzzing)
**Risk Level:** 🟢 MEDIUM

**What's Missing:**
- Seed that generates unwinnable level (gateway unreachable)
- Seed that generates player in wall (invalid spawn)
- Seed that generates no enemies (empty level)
- Seed that generates tiny rooms (min size validation)
- Seed that generates massive open area (performance)

**Tests Needed:**
- test_map_generation_fuzzing_1000_seeds
- test_map_generation_gateway_reachable
- test_map_generation_valid_player_spawn
- test_map_generation_enemy_count_valid
- test_map_generation_room_size_limits

---

### 3.6 Enemy Type Coverage Matrix
**Module:** Enemy types in various scenarios
**Complexity:** Moderate (many combinations)
**Risk Level:** 🟢 MEDIUM

**What's Missing:**
- Admin enemy in stealth scenarios (most dangerous enemy + stealth)
- Virus enemy in combat scenarios (DoT mechanics + combat)
- Inhibitor enemy in multi-enemy scenarios (disable mechanics + multiple enemies)
- Hunter enemy in level progression (fast enemy + gateway rushing)

**Tests Needed:**
- test_admin_stealth_scenario
- test_virus_combat_scenario
- test_inhibitor_multi_enemy_scenario
- test_hunter_level_progression_scenario
- test_all_enemy_types_spawn_correctly
- test_enemy_type_balance_per_level

---

### 3.7 Additional Fixtures Library
**Type:** Test infrastructure improvement
**Complexity:** Straightforward
**Risk Level:** 🟢 LOW-MEDIUM

**Missing Fixtures:**
1. **Full Inventory Fixture** - Player with max items, all exploits equipped
2. **Level 2/3 Fixtures** - Pre-configured level 2/3 state (avoid tedious progression)
3. **Victory Scenario Fixture** - Player at level 3 gateway (one step from victory)
4. **Surrounded Fixture Enhanced** - More variations (different enemy types/counts)
5. **Performance Test Fixture** - Scenario designed to stress test (many enemies, particles)

**Implementation:**
```python
# fixtures/scenario_fixtures.py

def full_inventory_fixture():
    """Player with max items and exploits equipped."""

def level_2_start_fixture():
    """Player starting level 2 with level 1 progress."""

def victory_ready_fixture():
    """Player at level 3 gateway, one step from victory."""

def surrounded_by_enemy_type_fixture(enemy_type, count):
    """Player surrounded by N enemies of specific type."""

def performance_stress_fixture():
    """Many enemies + particles + large explored area."""
```

---

## Phase 4: LOW PRIORITY - Polish & Edge Cases

**Goal:** Complete coverage of edge cases

### 4.1 Debug Mode Features
**Module:** Debug mode, debug export
**Complexity:** Trivial
**Risk Level:** 🟢 LOW

**What's Missing:**
- Debug export in various game states (menu open, mid-combat, etc.)
- Debug mode console commands (if any)
- Debug flag edge cases (debug mode + release build?)

**Tests Needed:**
- test_debug_export_all_game_states
- test_debug_mode_flags
- test_debug_console_commands

---

### 4.2 Achievement Trigger Timing
**Module:** Achievement system triggers
**Complexity:** Trivial
**Risk Level:** 🟢 LOW

**What's Missing:**
- Achievement unlocked at exact moment of death (race condition?)
- Multiple achievements unlock same turn (queue handling)
- Achievement during victory screen (timing)
- Achievement persistence through save/load

**Tests Needed:**
- test_achievement_unlock_on_death
- test_multiple_achievements_same_turn
- test_achievement_during_victory
- test_achievement_save_load_persist

---

### 4.3 Color Theme Edge Cases
**Module:** Color theme system
**Complexity:** Trivial
**Risk Level:** 🟢 LOW

**What's Missing:**
- Color theme switching during gameplay (not just startup)
- Invalid color values in config (validation/defaults)
- Color theme + graphics mode interaction (do themes apply to sprites?)

**Tests Needed:**
- test_color_theme_switch_during_game
- test_invalid_color_values
- test_color_theme_graphics_mode

---

### 4.4 Settings Validation
**Module:** Settings persistence, user_settings.json
**Complexity:** Trivial
**Risk Level:** 🟢 LOW

**What's Missing:**
- Invalid settings values (out of range, wrong type)
- Settings file corrupt (recovery to defaults)
- Settings persistence after crash (write timing)
- Settings migration (old format → new format)

**Tests Needed:**
- test_invalid_settings_values
- test_corrupt_settings_file
- test_settings_persist_after_crash
- test_settings_migration

---

### 4.5 Additional Test Agents
**Type:** Test agent library expansion
**Complexity:** Moderate (extends agent pattern)
**Risk Level:** 🟢 LOW-MEDIUM

**ItemCollectorAgent (straightforward):**
```python
class ItemCollectorAgent(GameTestAgent):
    """
    Finds and collects all items on level.
    Validates item spawn distribution and pickup mechanics.
    """
```

**MenuNavigatorAgent (straightforward):**
```python
class MenuNavigatorAgent(GameTestAgent):
    """
    Randomly navigates all menus, stresses menu system.
    Validates menu robustness and crash prevention.
    """
```

**PerformanceAgent (moderate complexity):**
```python
class PerformanceAgent(GameTestAgent):
    """
    Runs 5000+ turns, tracks memory/FPS over time.
    Detects performance degradation and memory leaks.
    """
```

**EdgeCaseAgent (moderate complexity):**
```python
class EdgeCaseAgent(GameTestAgent):
    """
    Deliberately triggers rare scenarios and edge cases.
    Tests boundary conditions and error handling.
    """
```

---

## Success Criteria

### Phase 1 Success Metrics:
- ✅ All CRITICAL modules have test coverage (particle, victory, tile, visibility)
- ✅ Graphics mode switching works reliably (no crashes)
- ✅ VictoryRunAgent completes game 100% of time
- ✅ Full playthrough smoke tests pass
- ✅ Zero P0 bugs remain

### Phase 2 Success Metrics:
- ✅ Enemy queue system robust (all edge cases covered)
- ✅ Exploit system tested thoroughly (8+ edge cases)
- ✅ Inventory overflow handled gracefully
- ✅ Menu navigation complete coverage
- ✅ Performance stable over long sessions (5000+ turns)

### Phase 3 Success Metrics:
- ✅ All game systems have edge case coverage
- ✅ Enemy type matrix complete (all types × all scenarios)
- ✅ Fixture library expanded (5+ new fixtures)
- ✅ Confidence in rare scenario handling

### Phase 4 Success Metrics:
- ✅ All modules have some test coverage
- ✅ Edge case coverage comprehensive
- ✅ Test agent library mature (7+ agents)
- ✅ Zero known test gaps

---

## Test Suite Health Metrics

**Target Metrics After Plan Completion:**

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Test Coverage (modules) | 60/94 (64%) | 90/94 (96%) | 🟡 Needs work |
| Integration Tests | Good | Excellent | 🟡 Needs work |
| Smoke Tests | Weak | Strong | 🔴 Critical gap |
| Agent Tests | 4 agents | 11 agents | 🟡 Needs work |
| Zero-coverage modules | 5 modules | 0 modules | 🔴 Critical gap |
| Performance tests | None | Comprehensive | 🔴 Critical gap |

**Overall Test Suite Health:**
Current: 🟡 **GOOD** (strong foundation, critical gaps)
Target: 🟢 **EXCELLENT** (comprehensive, production-ready)

---

## Immediate Quick Wins

**Highest ROI tasks to start immediately:**

1. **Victory Screen Tests** (trivial) - Blocks victory experience
2. **Tile Dimension Tests** (trivial) - Affects all rendering
3. **Visibility Manager Tests** (straightforward) - Core gameplay
4. **First 5 Min Smoke Test** (straightforward) - Catches common bugs

---

## Appendix: Test Organization

### Recommended Test File Structure:
```
tests/
├── unit/
│   ├── test_particle_system.py          [NEW - Phase 1.1]
│   ├── test_tile_dimension_calculator.py [NEW - Phase 1.3]
│   ├── test_visibility_manager.py        [NEW - Phase 1.4]
│   └── test_victory_screen.py            [NEW - Phase 1.2]
├── integration/
│   ├── test_graphics_mode_switching.py   [NEW - Phase 1.5]
│   ├── test_exploit_edge_cases.py        [NEW - Phase 2.2]
│   ├── test_inventory_overflow.py        [NEW - Phase 2.3]
│   ├── test_menu_navigation_complete.py  [NEW - Phase 2.4]
│   ├── test_performance_stress.py        [NEW - Phase 2.5]
│   └── test_enemy_queue_edge_cases.py    [NEW - Phase 2.1]
├── smoke/
│   ├── test_first_5_minutes.py           [NEW - Phase 1.7]
│   ├── test_complete_victory_run.py      [NEW - Phase 1.7]
│   ├── test_all_exploits_smoke.py        [NEW - Phase 1.7]
│   └── test_all_menus_smoke.py           [NEW - Phase 1.7]
├── agents/
│   ├── test_victory_run_agent.py         [NEW - Phase 1.6]
│   ├── test_stealth_agent.py             [NEW - Phase 2.7]
│   ├── test_combat_agent.py              [NEW - Phase 2.7]
│   ├── test_item_collector_agent.py      [NEW - Phase 4.5]
│   ├── test_menu_navigator_agent.py      [NEW - Phase 4.5]
│   └── test_performance_agent.py         [NEW - Phase 4.5]
└── fixtures/
    └── scenario_fixtures.py              [ENHANCE - Phase 3.7]
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-09 | Initial plan created after test purge |
| 2.0 | 2025-11-10 | **Removed all time estimates** per planning guide; replaced with complexity/risk labels |

---

**END OF PLAN**
