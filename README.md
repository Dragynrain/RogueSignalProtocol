![Rogue Signal Protocol Banner](docs/images/banner.png)

# Rogue Signal Protocol

**Version 0.9.2 Beta** - A coffee break cyberspace stealth roguelike built with Python and TCOD

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Version](https://img.shields.io/badge/version-0.9.2%20Beta-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**[SHARE YOUR FEEDBACK](https://forms.gle/jbwGdn8VGPa6NG9p9)** - Help shape development with this 2-minute survey!

---

## Documentation

**Choose your path:**

### Comprehensive Wiki (All Game Knowledge)
**[Visit the Wiki](https://github.com/Dragynrain/RogueSignalProtocol/wiki)** - Complete game encyclopedia including:
- Gameplay mechanics and systems
- All 26 achievements and how to unlock them
- Complete enemy, exploit, and item databases
- Status effects, code hacks, and progression guides
- UI/HUD explanations and settings reference
- Keybindings and inspection system guides

### For Players
**[README.txt](README.txt)** - Game instructions, controls, and gameplay guide

### For Developers, Modders & Contributors
**[README_DEV.md](docs/README_DEV.md)** - Complete developer guide including:
- Building from source
- Testing and development workflow
- Modding and JSON configuration
- Code architecture and TCOD gotchas
- Contributing guidelines
- Asset creation

---

## Quick Overview

Rogue Signal Protocol is a traditional turn-based coffee break stealth roguelike where you play as an escaped digital consciousness navigating hostile corporate networks. Quick 10-15 minute runs with permadeath - each death teaches lessons, each run reveals more truth.

### Key Features
- **Deterministic Gameplay (no RNG)**: Pure skill-based tactical decisions, no luck involved
- **Enemy Movement Prediction**: See each enemy's next 3 planned moves for tactical planning
- **3 Procedurally-Generated Network Levels**: 8 unique enemy types, 13 exploits, and distinct AI behaviors
- **Dual Rendering Modes**: Switch between graphical sprites or classic ASCII/Unicode glyphs

**Additional Features:**
- **Blind Spot Stealth** - Hide in shadows to avoid detection and manage heat levels
- **Dynamic Threat System** - High detection spawns the Admin Avatar boss with perfect tracking
- **Achievement System** - Persistent tracking across runs with unlockable challenges
- **Rich Narrative** - 20+ story fragments persist across runs, revealing the Project Chimera conspiracy
- **Full Polish** - Atmospheric music, 40+ sound effects, particle explosions, keyboard/mouse support

---

## Screenshots

<p align="center">
  <img src="docs/images/screenshots/screenshot-1.png" width="45%" alt="Gameplay Screenshot 1">
  <img src="docs/images/screenshots/screenshot-2.png" width="45%" alt="Gameplay Screenshot 2">
</p>
<p align="center">
  <img src="docs/images/screenshots/screenshot-3.png" width="30%" alt="Gameplay Screenshot 3">
  <img src="docs/images/screenshots/screenshot-4.png" width="30%" alt="Gameplay Screenshot 4">
  <img src="docs/images/screenshots/screenshot-5.png" width="30%" alt="Gameplay Screenshot 5">
</p>

---

## Community & Links

**Join the community and stay connected:**

[![Discord](https://img.shields.io/badge/Discord-Join%20Us-7289da?logo=discord&logoColor=white)](https://discord.gg/5fykUtECqz)
[![Itch.io](https://img.shields.io/badge/itch.io-Download-fa5c5c?logo=itch.io&logoColor=white)](https://dragynrain.itch.io/rogue-signal-protocol)
[![GitHub](https://img.shields.io/badge/GitHub-Source-181717?logo=github&logoColor=white)](https://github.com/Dragynrain/RogueSignalProtocol/)

- **Discord:** [https://discord.gg/5fykUtECqz](https://discord.gg/5fykUtECqz) - Share feedback, stories, and ideas
- **Itch.io:** [https://dragynrain.itch.io/rogue-signal-protocol](https://dragynrain.itch.io/rogue-signal-protocol) - Download and follow development
- **GitHub:** [https://github.com/Dragynrain/RogueSignalProtocol/](https://github.com/Dragynrain/RogueSignalProtocol/) - Source code and issues
- **Email:** roguesignalprotocol@gmail.com - Direct contact

Share your:
- Epic runs and close calls
- Ideas for features or improvements
- Bug reports
- Fan art and mods

---

## Quick Start

### For Players (Pre-built Executable)
Download the latest release:
- **[Itch.io](https://dragynrain.itch.io/rogue-signal-protocol)** (recommended)
- **[GitHub Releases](https://github.com/Dragynrain/RogueSignalProtocol/releases)** (alternative)

#### Windows SmartScreen Warning
When running the executable for the first time, Windows may display a "Windows protected your PC" warning from **Windows Defender SmartScreen**. This is normal for unsigned executables.

**The game is safe to run.** This warning appears because:
- The executable is not digitally signed with a code signing certificate
- Code signing certificates cost hundreds of dollars annually
- As an indie game, it's not cost-effective to purchase one

**To run the game:**
1. Click **"More info"** on the SmartScreen warning
2. Click **"Run anyway"**

The warning may appear again if you download a new version or move the file to a different location.

#### Linux (Including Steam Deck)

Multiple distribution formats available from **[GitHub Releases](https://github.com/Dragynrain/RogueSignalProtocol/releases)**:

**AppImage (Recommended - works on any distro):**
```bash
chmod +x RogueSignalProtocol-*.AppImage
./RogueSignalProtocol-*.AppImage
```

**Tarball (manual installation):**
```bash
tar xzf RogueSignalProtocol-linux.tar.gz
cd RogueSignalProtocol
./RogueSignalProtocol
```

**Flatpak (via Flathub beta channel):**
```bash
flatpak remote-add --if-not-exists flathub-beta https://flathub.org/beta-repo/flathub-beta.flatpakrepo
flatpak install flathub-beta com.dragynrain.roguesignalprotocol
```

**Arch Linux (AUR):**
```bash
yay -S rogue-signal-protocol-bin
```

**Steam Deck:** The game runs natively in Desktop Mode. Add as a non-Steam game for Gaming Mode. Resolution (1280x800) matches the Deck's screen perfectly. Full gamepad support included.

**Requirements:** SDL2 libraries (usually pre-installed on modern distros).

For detailed Linux packaging information, see [packaging/linux/README.md](packaging/linux/README.md).

### For Developers (From Source)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Dragynrain/RogueSignalProtocol.git
   cd RogueSignalProtocol
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game**
   ```bash
   python RogueSignalProtocol.py
   ```

See **[README_DEV.md](docs/README_DEV.md)** for complete development setup, testing, and building instructions.

---

## Contributing

We welcome contributions! See **[README_DEV.md](docs/README_DEV.md)** for:
- How to contribute
- Development workflow
- Testing requirements
- Code guidelines

---

## License

MIT License - Free and Open Source Software

This permissive license allows maximum freedom for both personal and commercial use. See [LICENSE](LICENSE) for details.

---

## Author

**Adam Forster** ([@Dragynrain](https://github.com/Dragynrain))

Contact: roguesignalprotocol@gmail.com

---

## Credits

- **Design & Programming:** Adam Forster
- **Engine:** Python + TCOD (libtcod)
- **Font:** KreativeSquare by Kreative Software
- **Graphics:** AI-generated sprites (Stable Diffusion, curated & edited)
- **Audio:** AI-generated music & SFX (AudioCraft, curated & edited)

Copyright (C) 2025 Adam Forster
