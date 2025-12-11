# README Structure Explained

## Three README Files - Three Audiences

The project now has a clear documentation structure targeting different audiences:

### 1. README.md (GitHub Landing Page)
**Audience**: Anyone visiting the GitHub repository

**Purpose**: Quick overview and navigation hub

**Content**:
- Project overview
- Quick start for both players and developers
- Links to detailed documentation
- License and author info

**Location**: Project root (GitHub shows this automatically)

---

### 2. README.txt (End-User Documentation)
**Audience**: Players who downloaded the game

**Purpose**: How to play the game

**Content**:
- Game controls and mechanics
- Enemy types and objectives
- System requirements
- Troubleshooting (SmartScreen, antivirus)
- Bug reporting instructions for alpha testers

**Location**:
- Project root (master copy)
- Copied to `dist/` by build script

**When to Edit**: Whenever game mechanics, controls, or help info changes

---

### 3. README_DEV.md (Developer Guide)
**Audience**: Developers, modders, contributors, source builders

**Purpose**: Complete technical documentation

**Content**:
- Development setup
- Testing (test_commands.py)
- Building executables (build types)
- Modding and JSON configuration
- Code architecture and patterns
- TCOD gotchas and important notes
- Development workflow
- Asset creation
- Contributing guidelines

**Location**: Project root

**When to Edit**: Whenever development processes, architecture, or technical details change

---

## Documentation Flow

### For Players
```
GitHub → README.md → Download release
             ↓
         README.txt (in the zip)
```

### For Developers
```
GitHub → README.md → README_DEV.md
                         ↓
                 Complete technical docs
```

### For Modders
```
GitHub → README.md → README_DEV.md → Modding & Configuration section
```

---

## Maintenance

### When to Update Each File

**README.md (GitHub):**
- New features (brief overview)
- Version number changes
- Download links change
- License changes

**README.txt (Players):**
- Game mechanics change
- New controls added
- New enemy types
- Troubleshooting updates
- System requirements change

**README_DEV.md (Developers):**
- Development workflow changes
- New build types
- Architecture changes
- New testing approaches
- Modding capabilities expand
- TCOD gotchas discovered

### Build System Integration

The build script automatically handles README.txt:

```batch
# In build.bat:
copy /Y "README.txt" "dist\README.txt"
```

**No manual copying needed!** Edit README.txt → Build → Automatically in dist/

---

## What Happened to DIST_README.txt?

**Deleted!** It was redundant.

**Before**: Three separate READMEs with duplicated content
- README.md (GitHub)
- README.txt (players)
- build/DIST_README.txt (duplicate technical info)

**After**: Three purpose-specific READMEs
- README.md (GitHub navigation hub)
- README.txt (player guide - **master copy**)
- README_DEV.md (developer/modder guide)

All technical troubleshooting merged into README.txt.

---

## Quick Reference

| File | Audience | Edit When | Auto-Copied |
|------|----------|-----------|-------------|
| README.md | GitHub visitors | Version/features change | No |
| README.txt | Players | Game mechanics change | Yes (to dist/) |
| README_DEV.md | Developers/modders | Technical changes | No |

---

## Best Practices

1. **One master copy per audience** - No duplicates
2. **Edit the source, not the copy** - Edit README.txt in root, not dist/
3. **Cross-reference** - Link between docs when needed
4. **Keep focused** - Each README serves ONE audience
5. **Build script sync** - Build system handles distribution

---

## Example Scenarios

### "I changed the controls"
- Edit `README.txt`
- Build -> Automatically in dist/

### "I added a new build type"
- Edit `README_DEV.md`
- Update build/ docs if needed

### "I released a new version"
- Edit `README.md` (GitHub landing)
- Edit `README.txt` (version mentioned there too)
- Edit `README_DEV.md` (version in header)

### "I want to add troubleshooting"
- Edit `README.txt` (players need it)
- Build -> Automatically distributed

---

## Summary

**Clear separation of concerns**:
- GitHub visitors → README.md (navigation)
- Players → README.txt (how to play)
- Developers → README_DEV.md (how to build/mod)

**No more duplicate maintenance!**
