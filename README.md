![Rogue Signal Protocol Banner](docs/images/banner.png)

# Rogue Signal Protocol

**Version 0.8.0 Alpha** - A coffee break cyberspace stealth roguelike built with Python and TCOD

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Version](https://img.shields.io/badge/version-0.8.0%20Alpha-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**📋 [SHARE YOUR FEEDBACK](https://forms.gle/jbwGdn8VGPa6NG9p9)** - Help shape development with this 2-minute survey!

---

## 📖 Documentation

**Choose your path:**

### 📚 Comprehensive Wiki (All Game Knowledge)
**[📖 Visit the Wiki](https://github.com/Dragynrain/RogueSignalProtocol/wiki)** - Complete game encyclopedia including:
- Gameplay mechanics and systems
- All 26 achievements and how to unlock them
- Complete enemy, exploit, and item databases
- Status effects, code hacks, and progression guides
- UI/HUD explanations and settings reference
- Keybindings and inspection system guides

### 🎮 For Players
**[README.txt](README.txt)** - Game instructions, controls, and gameplay guide

### 🔧 For Developers, Modders & Contributors
**[README_DEV.md](README_DEV.md)** - Complete developer guide including:
- Building from source
- Testing and development workflow
- Modding and JSON configuration
- Code architecture and TCOD gotchas
- Contributing guidelines
- Asset creation

---

## 🎮 Quick Overview

Rogue Signal Protocol is a coffee break stealth-focused cyberspace roguelike where you exfiltrate from corporate networks as a digital ghost. Complete runs in 10-15 minutes as you navigate procedurally generated levels, avoid sophisticated AI security systems, and discover the dark secrets hidden in the corporate data vaults.

### Key Features
- **🎲 Deterministic Gameplay**: No randomness or luck - pure skill-based tactical decisions
- **🤖 8 Unique Enemy Types**: Scanners, Hunters, Viruses, Firewalls, and Admin Avatar boss
- **⚡ 13 Powerful Exploits**: Combat, stealth, and utility abilities with heat management
- **🎯 Enemy Movement Prediction**: See enemies' next 3 planned moves for tactical advantage
- **🕵️ Blind Spot Stealth Mechanics**: Hide in shadows to avoid detection
- **⚠️ Dynamic Threat System**: High detection spawns the Admin Avatar boss
- **🏆 Achievement System**: Track progress across runs with persistent unlocks
- **📚 Rich Narrative**: Discover 20+ story fragments revealing Project Chimera
- **🎨 Dual Rendering Modes**: Switch between graphical sprites or classic ASCII/Unicode glyphs
- **💥 Particle Effect Explosions**: Visual feedback for combat and exploits
- **🎵 Full Audio**: Sound effects and atmospheric music (toggleable)
- **🖱️ Keyboard or Mouse**: Playable with full support for both input methods
- **💾 True Permadeath**: Saves deleted on death, auto-save on exit

---

## 📸 Screenshots

<p align="center">
  <img src="docs/images/screenshots/screenshot-1.png" width="45%" alt="Gameplay Screenshot 1">
  <img src="docs/images/screenshots/screenshot-2.png" width="45%" alt="Gameplay Screenshot 2">
</p>
<p align="center">
  <img src="docs/images/screenshots/screenshot-3.png" width="45%" alt="Gameplay Screenshot 3">
  <img src="docs/images/screenshots/screenshot-4.png" width="45%" alt="Gameplay Screenshot 4">
</p>

---

## 💬 Community & Links

**Join the community and stay connected:**

[![Discord](https://img.shields.io/badge/Discord-Join%20Us-7289da?logo=discord&logoColor=white)](https://discord.gg/aUZgmrpU)
[![Itch.io](https://img.shields.io/badge/itch.io-Download-fa5c5c?logo=itch.io&logoColor=white)](https://dragynrain.itch.io/rogue-signal-protocol)
[![GitHub](https://img.shields.io/badge/GitHub-Source-181717?logo=github&logoColor=white)](https://github.com/Dragynrain/RogueSignalProtocol/)

- **💬 Discord:** [https://discord.gg/aUZgmrpU](https://discord.gg/aUZgmrpU) - Share feedback, stories, and ideas
- **🎮 Itch.io:** [https://dragynrain.itch.io/rogue-signal-protocol](https://dragynrain.itch.io/rogue-signal-protocol) - Download and follow development
- **🔧 GitHub:** [https://github.com/Dragynrain/RogueSignalProtocol/](https://github.com/Dragynrain/RogueSignalProtocol/) - Source code and issues
- **📧 Email:** roguesignalprotocol@gmail.com - Direct contact

Share your:
- 🎮 Epic runs and close calls
- 💡 Ideas for features or improvements
- 🐛 Bug reports
- 🎨 Fan art and mods

---

## 🚀 Quick Start

### For Players (Pre-built Executable)
Download the latest release:
- **[Itch.io](https://dragynrain.itch.io/rogue-signal-protocol)** (recommended)
- **[GitHub Releases](https://github.com/Dragynrain/RogueSignalProtocol/releases)** (alternative)

#### ⚠️ Windows SmartScreen Warning
When running the executable for the first time, Windows may display a "Windows protected your PC" warning from **Windows Defender SmartScreen**. This is normal for unsigned executables.

**The game is safe to run.** This warning appears because:
- The executable is not digitally signed with a code signing certificate
- Code signing certificates cost hundreds of dollars annually
- As an indie game, it's not cost-effective to purchase one

**To run the game:**
1. Click **"More info"** on the SmartScreen warning
2. Click **"Run anyway"**

The warning may appear again if you download a new version or move the file to a different location.

### For Developers (From Source)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Dragynrain/RogueSignalProtocol.git
   cd RogueSignalProtocol
   ```

2. **Set up virtual environment**
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
   python RogueSignalProtocol.py
   ```

See **[README_DEV.md](README_DEV.md)** for complete development setup, testing, and building instructions.

---

## 🤝 Contributing

We welcome contributions! See **[README_DEV.md](README_DEV.md)** for:
- How to contribute
- Development workflow
- Testing requirements
- Code guidelines

---

## 📝 License

MIT License - Free and Open Source Software

This permissive license allows maximum freedom for both personal and commercial use. See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Adam Forster** ([@Dragynrain](https://github.com/Dragynrain))

📧 Contact: roguesignalprotocol@gmail.com

---

## 🎨 Credits

- **Design & Programming:** Adam Forster
- **Engine:** Python + TCOD (libtcod)
- **Font:** KreativeSquare by Kreative Software
- **Graphics:** AI-generated sprites (Stable Diffusion, curated & edited)
- **Audio:** AI-generated music & SFX (AudioCraft, curated & edited)

Copyright (C) 2025 Adam Forster
