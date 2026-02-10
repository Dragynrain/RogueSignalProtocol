# Rogue Signal Protocol - Trailer Plan

## Overview

- **Title:** Rogue Signal Protocol
- **Taglines:**
  1. "A cyberspace stealth roguelike where detection means deletion." (PRIMARY)
  2. "Become the signal they can't delete."
  3. "Three firewalls. No second chances. One way out."
- **Target Length:** ~45-50 seconds
- **Music:** Ambient synth chiptunes
- **Voiceover:** None (text + music only)

---

## Trailer Structure

### CINEMATIC HOOK (21 seconds)
AI-generated footage using WAN 2.2 I2V

| Section | Duration | Description |
|---------|----------|-------------|
| Digitization | 0-7s | Person zapped by electricity, dissolving into pixels/data |
| Matrix Arrival | 7-14s | Reforming inside the network, confused, examining digital self |
| Threat Detected | 14-21s | Reacting to danger, diving to cover |

### TRANSITION (1-2 seconds)
- Glitch/pixelate effect
- Or text flash: "SIGNAL DETECTED" / "DETECTION MEANS DELETION"

### GAMEPLAY SHOWCASE (20-24 seconds)
Real game footage with title cards

| Title Card | Duration | Footage |
|------------|----------|---------|
| "TACTICAL STEALTH GAMEPLAY" | 5-6s | Reading enemy patrol patterns, hiding in blindspots |
| "EVERY MOVE MATTERS" | 5-6s | Tense decision moment, using enemy prediction system |
| "PERMADEATH" | 5-6s | Death sequence / save deleted / restart |
| "PROCEDURALLY GENERATED" | 4-5s | Different map layouts, variety |

### TITLE CARD (3-5 seconds)
- Logo: **ROGUE SIGNAL PROTOCOL**
- Tagline: "Detection means deletion."
- "Coming 2026" / "Available Now" / "Wishlist Now"
- Platform icons (itch.io, Steam if applicable)

---

## Cinematic Footage Details

### Source Images by Scene

| Scene | Location | Description |
|-------|----------|-------------|
| Scene 1 | `D:\aiart\SwarmUI_video\SwarmUI\Input` | Shadowy silhouette in chair with lightning strikes |
| Scene 2 | `D:\aiart\SwarmUI_video\SwarmUI\Input\2` | Neon wireframe humanoid in cyberpunk corridor |
| Scene 3 | *Last frame of Scene 2 video* | Action/threat detected (extracted from Scene 2 output) |

### Scene 3 Workflow (Last Frame Extraction)
To use the last frame of a Scene 2 video as Scene 3 input:
1. Use VHS `Load Video (Path)` node to load the Scene 2 video
2. Connect to VHS `Select Images` node with indexes: `-1` (selects last frame)
3. Feed the single frame into WAN 2.2 I2V node

### Original Image Prompt (Scene 1)
```
A wide-angle cinematic frontal shot of a genderless shadowy silhouette facing the camera,
sitting centered in a computer chair. The shot is taken from a distance showing the full
body from head to toe, including the figure's feet on the floor. The silhouette's chest
and knees are oriented toward the viewer, with the backrest of the chair hidden behind
their shoulders. The figure is surrounded by a complex server corridor filled with high
tech lab equipment, medical machinery, and glowing monitors displaying technical noise
and digital readouts with no brand names. A chaotic <random:blue,green,red,purple,pink,yellow,white>
<random:branching lightning strikes,light beams,lasers,electricity> strikes the top of
their head. Style: hyper-realistic, 8K, in the style of <random:1980's cyberpunk,retro futuristic,The Matrix movies,the 1982 Tron movie>
```

---

## WAN 2.2 Video Prompts

### Scene 1: Digitization (Original Workflow Prompt - for reference)
```
[Subject] A high-fidelity digital avatar with glowing wireframe patterns on its palms.
[Scene] Standing in a sleek, futuristic server corridor, bathed in volumetric yellow
and green neon rim lighting with glowing data racks in the background.
[Motion] The avatar's head snaps around rapidly with disoriented movements; it raises
its hands to eye level, closely examining the detailed wireframe light on its palms
with a visible expression of uncertainty and confusion.
[Camera] Smooth cinematic dolly-in toward the avatar's face, professional cinematography,
4K detail, temporal consistency.
```

### Scene 1: Digitization (NEW - Pixel Disintegration)
```
[Subject] A genderless shadowy silhouette seated in a computer chair, being struck by
intense electrical energy from above.
[Scene] A dark server corridor lined with glowing monitors, high-tech equipment, and
pulsing data racks casting cyan and orange light.
[Motion] The figure convulses violently as their body fragments into thousands of glowing
pixels and data particles; the pixels cascade outward from the head downward, spiraling
in a vortex before imploding toward the chest; electricity crackles continuously as the
silhouette dissolves into scattered light.
[Camera] Static wide-angle frontal shot, cinematic composition, 4K detail, temporal consistency.
```

### Scene 1: Digitization (ALT - Matrix Upload)
```
[Subject] A dark silhouette figure sitting in a chair, electricity surging into the top
of their head.
[Scene] Futuristic server room corridor with rows of glowing monitors and technical
equipment, volumetric lighting in cyan and orange tones.
[Motion] The silhouette glitches and distorts as energy intensifies; the body pixelates
and breaks apart into streams of luminous data particles that flow upward like reverse
rain; fragments accelerate upward until the chair sits empty with only floating sparks
remaining.
[Camera] Locked wide shot facing the subject, no camera movement, hyper-realistic VFX,
cinematic lighting.
```

### Scene 1: Digitization (ALT - Implosion Burst)
```
[Subject] A shadowy humanoid silhouette seated in an office chair receiving a massive
electrical discharge.
[Scene] A symmetrical high-tech server corridor with banks of glowing screens and orange
data lights on both sides.
[Motion] Lightning crackles and the figure's body shatters into millions of cubic pixels
that hover momentarily then violently implode toward center mass; a shockwave of digital
particles ripples outward; monitors flicker and glitch as the last fragments spiral into
a point of light and vanish.
[Camera] Static cinematic wide shot, frontal angle, professional cinematography, temporal
consistency.
```

### Scene 2: Matrix Arrival / Confusion
Source images in `Input/2` folder - neon wireframe humanoid in cyberpunk corridor

```
[Subject] A glowing humanoid figure composed of neon wireframe geometry and translucent
digital mesh, standing in a cyberpunk corridor.
[Scene] A vibrant neon-lit corridor with purple, cyan, and pink lighting; reflective
floor surfaces mirror the glowing figure; holographic data panels and geometric patterns
line the walls.
[Motion] The figure looks down at their translucent wireframe hands in confusion, turning
them slowly to examine the glowing circuitry patterns; they look around disoriented,
head turning left then right; their body flickers between solid and pixelated states.
[Camera] Medium shot, slight push-in toward subject, cinematic lighting, temporal consistency.
```

### Scene 2: Matrix Arrival (ALT - Awakening)
```
[Subject] A luminous wireframe humanoid with glowing neon circuitry patterns across their body.
[Scene] Futuristic corridor bathed in purple and cyan neon light; geometric architecture
with reflective surfaces; floating holographic interface elements in the background.
[Motion] The figure's eyes open as they become aware; they stumble slightly, reaching
out to touch the nearest wall; their hand passes partially through the surface revealing
their digital nature; data particles swirl around their form as they stabilize.
[Camera] Static medium shot, no camera movement, hyper-realistic digital VFX, temporal consistency.
```

### Scene 3: Threat Detected / Action
Input: Last frame extracted from Scene 2 video (using VHS SelectImages with index `-1`)

```
[Subject] A glowing wireframe humanoid figure in a neon cyberpunk corridor, alert and tense.
[Scene] The same vibrant corridor from Scene 2; suddenly red warning lights begin flashing;
a hostile scanning beam sweeps across the space; geometric security barriers emerge.
[Motion] The figure's head snaps to the side detecting danger; they drop into a crouch
and press against the wall; a threatening red scan beam passes inches from their position;
they hold perfectly still as the danger passes; their body flickers with distortion from
the close call.
[Camera] Same framing as Scene 2 end, slight zoom during scan beam pass, cinematic tension,
temporal consistency.
```

### Scene 3: Threat Detected (ALT - Dive to Cover)
```
[Subject] A luminous digital humanoid with neon wireframe patterns, standing in a corridor.
[Scene] Cyberpunk corridor with purple and cyan lighting that suddenly shifts to red alarm
state; security drones or hostile code patterns emerge from the walls.
[Motion] The figure spots the threat approaching; their expression shifts to alarm; they
dive to the side and roll behind geometric cover; they peek around the edge watching the
danger pass; their body distorts and pixelates from the rapid movement.
[Camera] Dynamic push-in as threat approaches, hold on figure behind cover, temporal consistency.
```

---

## Workflow Location

- **Workflow File:** `D:\aiart\SwarmUI_video\SwarmUI\dlbackend\comfy\ComfyUI\user\default\workflows\BATCH 03_video_wan2_2_14B_i2v_FOLDER_ITERATOR.json`
- **Input Folder:** `D:\aiart\SwarmUI_video\SwarmUI\Input`
- **Custom Node:** `D:\aiart\SwarmUI_video\SwarmUI\dlbackend\comfy\ComfyUI\custom_nodes\image_folder_iterator.py`

### Workflow Settings
- **Length:** 113 frames
- **FPS:** 16
- **Duration:** ~7 seconds per video
- **Resolution:** 1280x720 (set in WanImageToVideo node)

### How to Use - Scene 1 & 2
1. Place source images in appropriate Input folder:
   - Scene 1: `D:\aiart\SwarmUI_video\SwarmUI\Input`
   - Scene 2: `D:\aiart\SwarmUI_video\SwarmUI\Input\2`
2. Load the FOLDER_ITERATOR workflow
3. Update the folder path in LoadImageFromFolder node to match scene
4. Set your video prompt in the positive prompt node
5. Select "Run (Instant)" to generate continuously
6. Videos output to ComfyUI output folder

### How to Use - Scene 3 (Last Frame Method)
1. Select the best Scene 2 video output
2. Create a workflow variation that:
   - Uses VHS `Load Video (Path)` to load the Scene 2 video file
   - Connects to VHS `Select Images` with indexes: `-1`
   - Feeds the single last frame into WAN 2.2 I2V
3. Set the Scene 3 video prompt
4. Generate Scene 3 video

---

## Production Checklist

### Cinematic Footage
- [ ] Generate Scene 1: Digitization videos (multiple variations)
- [x] Source images for Scene 2 ready (`Input/2` folder)
- [ ] Generate Scene 2: Matrix Arrival videos
- [ ] Extract last frames from best Scene 2 videos for Scene 3 input
- [ ] Generate Scene 3: Threat Detected videos (using Scene 2 last frames)
- [ ] Select best takes from each scene
- [ ] Review for temporal consistency and quality

### Gameplay Footage
- [ ] Capture stealth gameplay (avoiding patrols, using prediction)
- [ ] Capture tense decision moment
- [ ] Capture death sequence
- [ ] Capture variety of procedural layouts
- [ ] Capture both ASCII and graphical modes (if showing both)

### Post-Production
- [ ] Edit cinematic footage together (21 seconds)
- [ ] Create transition effect (glitch/pixelate)
- [ ] Edit gameplay footage with title cards
- [ ] Add title card / logo
- [ ] Add music track
- [ ] Add sound effects (zap, digital sounds, glitch)
- [ ] Final timing pass
- [ ] Export in multiple formats (YouTube, itch.io, social)

---

## Technical Notes

### Video Specs for Export
- **YouTube/Primary:** 1920x1080, 30fps, H.264
- **itch.io:** 1920x1080 or 1280x720, under 500MB
- **Social (Twitter/X):** 1280x720, under 512MB, 2:20 max
- **Social (Instagram):** 1080x1080 (square) or 1080x1920 (stories)

### Music Sync Points (estimate)
- 0s: Music starts soft/ambient
- 3-4s: Build begins (electricity intensifying)
- 7s: First hit/drop (dissolution moment)
- 14s: Second beat (arrival in matrix)
- 21s: Transition beat (cut to gameplay)
- 42-45s: Final swell/resolve (title card)

---

## Reference Links

- **WAN 2.2 Tutorial:** https://docs.comfy.org/tutorials/video/wan/wan2_2
- **Marketing Plan:** `D:\projects\RogueSignalProtocol\marketing\marketing_plan_2026.md`
- **Marketing Assets:** `D:\projects\RogueSignalProtocol\marketing\marketing_assets.txt`
