# Rogue Signal Protocol - Development Checklist

## Month 1: Core Foundation ✓ = Complete, ◐ = In Progress, ◯ = Not Started

### Week 1: Project Setup
- [ ] ◯ Initialize git repository
- [ ] ◯ Set up Python virtual environment
- [ ] ◯ Install tcod and dependencies
- [ ] ◯ Create project directory structure
- [ ] ◯ Set up basic logging system
- [ ] ◯ Implement main.py entry point
- [ ] ◯ Create basic tcod console window
- [ ] ◯ Implement player movement (arrow keys)
- [ ] ◯ Basic map rendering (walls/floors)

**Milestone**: Player can move around a static map

### Week 2: Basic Game Loop
- [ ] ◯ Implement turn-based system
- [ ] ◯ Create basic map generation (rooms + corridors)
- [ ] ◯ Add enemy entities (static placement)
- [ ] ◯ Implement field of view (tcod FOV)
- [ ] ◯ Basic collision detection
- [ ] ◯ Game state management
- [ ] ◯ Input handling system
- [ ] ◯ Basic UI framework

**Milestone**: Player can explore generated levels with enemies

### Week 3: Combat Foundation
- [ ] ◯ Implement HP system
- [ ] ◯ Basic bump-to-attack combat
- [ ] ◯ Damage calculation
- [ ] ◯ Enemy death handling
- [ ] ◯ Combat feedback (messages)
- [ ] ◯ Basic inventory system
- [ ] ◯ CPU cycles as currency
- [ ] ◯ Simple item pickup

**Milestone**: Player can fight enemies and collect rewards

### Week 4: Save System & Polish
- [ ] ◯ Implement save/load system
- [ ] ◯ Settings framework (JSON config)
- [ ] ◯ ASCII rendering improvements
- [ ] ◯ Basic error handling
- [ ] ◯ Game over/restart mechanics
- [ ] ◯ Performance profiling setup
- [ ] ◯ Unit test framework
- [ ] ◯ Debug mode implementation

**Milestone**: Stable, saveable roguelike foundation

---

## Month 2: Stealth Core

### Week 1: Vision System
- [ ] ◯ Implement enemy vision ranges
- [ ] ◯ Line of sight calculations
- [ ] ◯ Vision blocking by obstacles
- [ ] ◯ Player visibility detection
- [ ] ◯ Enemy color states (green/yellow/red)
- [ ] ◯ Basic stealth mechanics
- [ ] ◯ Vision range visualization
- [ ] ◯ Player vision limiting (fog of war)

**Milestone**: Stealth detection system working

### Week 2: Cover System
- [ ] ◯ Network obstacle placement
- [ ] ◯ Line of sight blocking by obstacles
- [ ] ◯ Cover-based hiding mechanics
- [ ] ◯ Obstacle types (data clusters, nodes, etc.)
- [ ] ◯ Strategic obstacle placement
- [ ] ◯ Hiding feedback to player
- [ ] ◯ Obstacle sprites/visuals
- [ ] ◯ Pathfinding around obstacles

**Milestone