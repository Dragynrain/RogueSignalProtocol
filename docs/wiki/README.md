# Wiki Content

This directory contains the source markdown files for the Rogue Signal Protocol GitHub wiki.

## Structure

- **Home.md** - Wiki homepage and overview
- **Gameplay-Mechanics.md** - Core gameplay systems (manually maintained)
- **Keybindings.md** - Complete control reference (manually maintained)
- **Development.md** - Developer guide (manually maintained)
- **Enemy-Database.md** - Auto-generated from game_content.json
- **Exploit-Database.md** - Auto-generated from game_content.json
- **Network-Configuration.md** - Auto-generated from game_content.json

## Auto-Generation

Some wiki pages are automatically generated from game JSON files to ensure they stay in sync with game data.

### Automatic Generation (During Builds)

**Wiki pages are automatically regenerated during the build process!**

When you run `build\build.bat alpha` or `build\build.bat release`, the script:
1. Runs `docs\generate_wiki.py` automatically
2. Regenerates Enemy-Database.md, Exploit-Database.md, Network-Configuration.md
3. Continues with the build even if wiki generation fails (with warning)

**This ensures your wiki is always in sync with game data when creating releases.**

### Manual Generation

You can also run the generator manually anytime:

```bash
python docs/generate_wiki.py
```

This will regenerate:
- Enemy-Database.md
- Exploit-Database.md
- Network-Configuration.md

### When to Manually Regenerate

Run the generator manually when:
- Testing wiki changes without building
- Updating wiki during development
- Verifying wiki content before committing

**Note:** If you're building a release, you don't need to manually regenerate - it happens automatically!

### What Gets Generated

Manual pages (Home, Gameplay-Mechanics, Keybindings, Development) should be edited directly and are NOT regenerated.

## Publishing to GitHub Wiki

After updating wiki content (manually or via generation):

1. **Navigate to parent directory:**
   ```bash
   cd ..
   ```

2. **If not already cloned, clone the wiki repo:**
   ```bash
   git clone https://github.com/Dragynrain/RogueSignalProtocol.wiki.git
   ```

3. **Copy updated files:**
   ```bash
   cp RogueSignalProtocol/docs/wiki/*.md RogueSignalProtocol.wiki/
   ```

4. **Commit and push:**
   ```bash
   cd RogueSignalProtocol.wiki
   git add .
   git commit -m "Update wiki content"
   git push
   ```

## Development Workflow

1. **Update game JSON** files as needed
2. **Run generator** if JSON changed: `python docs/generate_wiki.py`
3. **Review changes** in docs/wiki/
4. **Push to wiki** following steps above

## Wiki Links

- **Live Wiki:** https://github.com/Dragynrain/RogueSignalProtocol/wiki
- **Wiki Repo:** https://github.com/Dragynrain/RogueSignalProtocol.wiki.git

## Maintenance Notes

### Auto-Generated Pages
These are overwritten each time the generator runs. Don't manually edit:
- Enemy-Database.md
- Exploit-Database.md
- Network-Configuration.md

### Manual Pages
Edit these directly as needed:
- Home.md - Update for new features or version changes
- Gameplay-Mechanics.md - Update when mechanics change
- Keybindings.md - Update when controls change
- Development.md - Update for new dev processes

### Generator Script
The generator script is located at `docs/generate_wiki.py` and can be modified to:
- Add new auto-generated pages
- Change formatting or structure
- Pull from additional JSON files
- Add new sections or categories
