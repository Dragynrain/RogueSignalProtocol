# Contributing to Rogue Signal Protocol

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Ways to Contribute

### 🐛 Report Bugs
Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) to report issues.

### 💡 Suggest Features
Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) to propose new ideas.

### 🔧 Submit Code
Follow the development workflow below to submit code changes.

### 📖 Improve Documentation
Documentation improvements are always welcome!

### 🎨 Create Content
- Story fragments
- Enemy types
- Exploit abilities
- Sound effects or music

---

## Development Setup

### 1. Fork and Clone
```bash
git clone https://github.com/YOUR-USERNAME/RogueSignalProtocol.git
cd RogueSignalProtocol
```

### 2. Set Up Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Run the Game
```bash
python RogueSignalProtocol.py
```

See **[README_DEV.md](README_DEV.md)** for complete development documentation.

---

## Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

### 2. Make Changes
- Follow the coding style (see below)
- Write clear, descriptive commit messages
- Update tests as needed

### 3. Test Your Changes
**ALWAYS test before committing:**
```bash
python test_commands.py full  # Run all tests
```

### 4. Commit
```bash
git add .
git commit -m "Brief description of changes"
```

**Commit Message Guidelines:**
- Use present tense ("Add feature" not "Added feature")
- Keep first line under 50 characters
- Provide detailed description in body if needed

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub.

---

## Coding Guidelines

### Python Style
- Follow PEP 8 style guide
- Use descriptive variable names
- Add docstrings to functions and classes
- Keep functions focused and under ~50 lines when possible

### Game Development
- **Test on Windows** (primary platform)
- **No hardcoded values** - use `game_content.json` and `game_rules.json`
- **Fail fast** on missing config files (except `user_settings.json`)
- **Always bounds-check** array access
- See `.claude/CLAUDE.md` for detailed project rules

### Testing
- Update tests when changing functionality
- Add tests for new features
- Integration tests preferred over mocks
- All tests must pass before PR

---

## Code Review Process

1. **Automated checks**: GitHub Actions will run tests
2. **Review**: Maintainer will review code and suggest changes
3. **Revisions**: Address feedback and push updates
4. **Merge**: Once approved, PR will be merged

---

## JSON Content Contributions

### Adding New Enemies
Edit `game_content.json` → `enemy_types` section:
```json
{
  "type_key": {
    "name": "Display Name",
    "symbol": "A",
    "color": [255, 100, 0],
    "cpu": 30,
    "damage": 10,
    "vision_range": 8,
    "movement": "SEEK",
    "description": "Enemy description"
  }
}
```

### Adding New Exploits
Edit `game_content.json` → `exploits` section:
```json
{
  "exploit_key": {
    "name": "Exploit Name",
    "type": "combat",
    "heat_cost": 20,
    "ram_cost": 2,
    "cooldown": 3,
    "damage": 25,
    "range": 5,
    "description": "What it does"
  }
}
```

See [README_DEV.md](README_DEV.md) for complete modding documentation.

---

## Asset Contributions

### Graphics
- PNG format, transparent backgrounds
- 64x64px for tiles (scaled down from higher res is fine)
- Cyberpunk/digital aesthetic

### Audio
- **Sound Effects:** WAV format, ~1-2 seconds, < 200KB
- **Music:** OGG format, loopable, < 5MB
- Cyberpunk/electronic theme

---

## Questions?

- **Discord:** [https://discord.gg/aUZgmrpU](https://discord.gg/aUZgmrpU)
- **Email:** roguesignalprotocol@gmail.com
- **Discussions:** Use GitHub Discussions for questions

---

## Code of Conduct

Be respectful, constructive, and collaborative. We're all here to make a great game together.

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Rogue Signal Protocol!** 🎮
