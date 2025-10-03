# Rogue Signal Protocol

**Version 0.8.0 Alpha** - A cyberpunk stealth roguelike built with Python and TCOD

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Version](https://img.shields.io/badge/version-0.8.0%20Alpha-orange.svg)
![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)

## 🎮 Game Overview

Rogue Signal Protocol is a stealth-focused cyberpunk roguelike where you infiltrate corporate networks as a digital ghost. Navigate procedurally generated levels, avoid sophisticated AI security systems, and discover the dark secrets hidden in the corporate data vaults.

### Key Features

- **🕵️ Stealth-Focused Gameplay**: Hide in shadows, avoid detection, and use cunning over brute force
- **🤖 8 Unique Enemy Types**: From basic Scanners to the terrifying Admin Avatar
- **⚡ 12 Powerful Exploits**: Combat and utility abilities including Buffer Overflow, Shadow Step, and EMP Burst
- **🌐 3 Network Environments**: Corporate Network, Government System, and Military Backbone
- **📚 Rich Narrative**: Discover 20+ story fragments revealing the conspiracy behind Project Chimera
- **🎵 Enhanced Audio**: Full sound effects and atmospheric music
- **💾 Persistent Progression**: Story discoveries and settings carry between runs
- **⚙️ Permadeath Mechanics**: Save files deleted on death - every decision matters

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- Windows 10/11 (primary support)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Dragynrain/RogueSignalProtocol.git
   cd RogueSignalProtocol
   ```

2. **Set up virtual environment** (recommended)
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game**
   ```bash
   .venv\Scripts\python.exe RogueSignalProtocol.py
   ```

## 🎯 How to Play

### Objective
Navigate through 3 increasingly dangerous network levels, reach the gateway (>) on each level, and uncover the truth behind the Omni-Lyra Cognitive Resilience Initiative.

### Controls
- **Movement**: Arrow Keys, WASD, or Numpad
- **Exploits**: 1-5 keys to use equipped exploits
- **Inventory**: I key to manage codes and exploits
- **Lore**: L key to view discovered story fragments
- **Pause**: ESC key

### Core Mechanics

- **Stealth**: Hide in shadows (*) to avoid enemy detection
- **Heat Management**: Exploit usage generates heat; overheating causes damage
- **Detection System**: High detection levels spawn the Admin Avatar
- **Resource Management**: Balance CPU (health), RAM (exploit capacity), and Heat

### Enemy Types

| Symbol | Name | HP | Vision | Behavior | Damage |
|--------|------|----|---------|---------| -------|
| S | Scanner | 35 | 4 | Static | 0 |
| P | Patrol | 40 | 4 | Patrol Routes | 15 |
| B | Bot | 25 | 3 | Random Movement | 8 |
| F | Firewall | 80 | 5 | Static Guardian | 0 |
| H | Hunter | 50 | 6 | Seeks Players | 22 |
| V | Virus | 35 | 4 | Applies Virus | 0 |
| I | Inhibitor | 30 | 4 | Slows Movement | 5 |
| A | Admin Avatar | 250 | 8 | Perfect Tracking | 45 |

## 🛠️ Development

### Tech Stack
- **Engine**: Python with python-tcod (19.4.0+)
- **Audio**: pygame (2.6.1+)
- **Architecture**: Modular component system
- **Testing**: pytest with 700+ test coverage

### Project Structure
```
RogueSignalProtocol/
├── RogueSignalProtocol.py    # Main entry point
├── game_*.py                 # Core game modules
├── data_loading.py           # Configuration management
├── game_config.json          # Game settings
├── game_data.json           # Enemy/exploit definitions
├── story_content.json       # Narrative fragments
├── tests/                   # Test suite
├── sound/                   # Audio effects
├── music/                   # Background music
└── saves/                   # Save game data
```

### Key Features for Developers
- **Comprehensive Testing**: 700+ unit and integration tests
- **Modular Design**: Clean separation of concerns
- **JSON-Driven**: Easy configuration through JSON files
- **Error Handling**: Robust error reporting and recovery
- **Save System**: Complete game state persistence

## 🎨 Game Features

### Exploit System
Choose from 12 different exploits across 4 categories:

**Combat**: Buffer Overflow, Code Injection, System Crash, EMP Burst
**Stealth**: Shadow Step, Data Mimic, Noise Maker
**Utility**: Threat Scan, Network Scan, Log Wiper, Antivirus
**Special**: Memory Leak

### Procedural Generation
- **Dynamic Level Layouts**: Each run features unique room arrangements
- **Balanced Enemy Placement**: Intelligent spawn systems for fair challenge
- **Resource Distribution**: Strategic placement of upgrades and pickups

### Story Integration
Discover the dark truth through environmental storytelling:
- **Project Chimera**: Uncover the real purpose behind the "testing"
- **Dr. Aris Thorne**: Learn about the obsessed lead researcher
- **Digital Consciousness**: Explore themes of mind uploading and identity

## 🚧 Alpha Status

This is an **Alpha release** focusing on core gameplay and feedback collection.

### What's Implemented
- ✅ Complete stealth gameplay loop
- ✅ All 8 enemy types with unique behaviors
- ✅ Full exploit system with 12 abilities
- ✅ 3-level campaign with escalating difficulty
- ✅ Save/load system with permadeath
- ✅ Audio system with music and SFX
- ✅ Complete story content (20 fragments)

### Known Limitations
- Windows-focused (Linux/Mac compatibility planned)
- Terminal graphics (advanced graphics being considered beyond title screens)

## 🤝 Contributing

We welcome contributions! Please feel free to:
- Report bugs through GitHub Issues
- Suggest gameplay improvements
- Submit pull requests for bug fixes
- Share feedback on game balance

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

**GPL v3 Summary**: This software is free and open source. You can use, modify, and distribute it, but any modifications must also be released under GPL v3. This ensures the game remains free and open for everyone.

Key freedoms under GPL v3:
- ✅ Freedom to run the program for any purpose
- ✅ Freedom to study how the program works and modify it
- ✅ Freedom to redistribute copies
- ✅ Freedom to distribute modified versions

Any derivative works must also be licensed under GPL v3, ensuring the game and its derivatives remain free software forever.

## 👨‍💻 Author

**Adam Forster** ([@Dragynrain](https://github.com/Dragynrain))

## 🙏 Acknowledgments

- Built with [python-tcod](https://github.com/libtcod/python-tcod) - Excellent roguelike development library
- Inspired by classic stealth games and cyberpunk fiction
- Special thanks to the roguelike development community
