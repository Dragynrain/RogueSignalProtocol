# Rogue Signal Protocol - Trailer Plan (v1, Gameplay-First)

Quick-turnaround trailer built entirely from real gameplay. No AI cinematic required.
Target length: **~30 seconds**. The WAN2 cinematic (see `TRAILER_PLAN.md`) can drop
into the cold-open slot later without re-editing the rest, becoming a v2.

## Why gameplay-first, why 30 seconds

- The unique, legible hook is enemy movement prediction. A tight cut that lands that
  one idea beats a longer trailer that wanders.
- A gameplay-only cut removes AI-provenance risk from the most public asset, which
  matters for the Linux / open-source / hidden-gem outlets we are targeting.
- 30s holds attention on Reddit, itch, and YouTube autoplay better than 45s. The 45s
  version is kept below as an optional extended cut.

## Compression technique

Full-screen text cards eat seconds. In the 30s cut, only two moments get a hard card:
the RNG hook and the save-delete punchline. Every other line rides as an overlay
(lower-third or fade-in) over footage that keeps playing.

## Beat Sheet (30s primary)

| Time | Footage | Text | Audio |
|------|---------|------|-------|
| 0.0-3.0 | Cold open on a tense board: enemy prediction arrows visible, player one tile from a patrol's planned path. Not black. | Overlay fades in: `Detection means deletion.` | Ambient (`level1_stealth`), low |
| 3.0-9.0 | The read (keystone beat): player waits, patrol arrows advance, player slips into a blind spot, patrol passes through where the player was. This is the "oh, I get it" moment - let it breathe. | none | Soft build |
| 9.0-11.0 | Hard cut / brief hold | Full card: `NO COMBAT RNG. READ THE NEXT 3 TURNS.` | Beat hit |
| 11.0-17.0 | Stealth-read payoff first: a blind-spot takedown. Then one exploit with targeting and the particle explosion. HUD heat/RAM tick up. | Optional lower-third: `Exploits cost RAM. Exploits cost heat.` | Build |
| 17.0-21.0 | Escalation: trace meter climbing, alert text flashing, Admin Avatar appears and begins pursuit. | Overlay: `HIGH TRACE SUMMONS THE ADMIN AVATAR` | Tension; `level3_core` enters |
| 21.0-24.0 | Death hit lands first (player deleted), then hold on the save-delete moment. | Overlay after the hit: `THE RUN ENDS. THE SAVE IS DELETED.` | Drop to near silence |
| 24.0-27.5 | Breadth: 2-3 different network looks (fast), a story fragment flash, then an ASCII match cut on the SAME scene, graphics to glyphs, so it reads as dual rendering rather than a glitch. | Optional tiny label: `Dual rendering` | Swell resumes |
| 27.5-30.0 | Logo, then CTA. | `Make your signal count.` then `Name your own price on itch.io  |  Windows + Linux  |  Steam Deck  |  MIT open source` | Resolve |

Timings are flexible by roughly half a second per beat for feel. The death beat at 3s
is tight; steal from the counterplay montage if it needs to land harder.

## Corrections baked in

- Card reads `NO COMBAT RNG. READ THE NEXT 3 TURNS.` The feature is enemy movement
  prediction (each enemy shows its next 3 planned moves), not the player's future or
  all outcomes. Avoid "every move."
- One clean stealth-read-payoff comes before the big explosion. Exploits and explosions
  are counterplay, not the whole game. The core loop is: hide in blind spots, manage
  heat, pick your moments.
- Cold open on a live dangerous board state, not pure black, so the WAN2 cinematic can
  replace that slot later.
- Death shows first, then the punchline card. The silence lands harder after the hit.
- ASCII is a match cut from the same scene (graphics to glyphs), not a random glitch.
- Breadth beat sells tight, replayable tactical runs across 3 procedural network levels,
  not large biome variety.
- Final CTA includes Windows. The itch page presents a Windows/Linux download with
  Steam Deck support.

## Shots to capture (record these clean)

Record deliberately: no fumbling, no menu-hunting. Short clean clips cut together read
as more polished than one long real session.

1. Hook: a clean slip past a patrol using the prediction arrows (the keystone).
2. Blind-spot takedown.
3. One exploit with targeting reticle and the particle explosion, HUD heat/RAM visible.
4. Trace rising to alert, then the Admin Avatar spawning / pursuing.
5. Player death and the save-delete moment.
6. 2-3 short pans of different network layouts, plus one story fragment on screen.
7. The same scene rendered in graphics and in ASCII, framed identically for a match cut.
8. Optional: an achievement unlock or Ascension mode flash for the breadth beat.

## Tooling

- **Editor:** DaVinci Resolve (free). Handles the timeline, text cards/overlays, audio
  ducking, and a glitch/fade transition. An evening to learn enough for this.
- **Music:** use the game's own tracks. `level1_stealth.ogg` for the ambient open,
  rising into `level3_core.ogg` at escalation and the breadth swell. These are already
  on-brand and copyright-clean, so no royalty-free hunting.
- **Existing footage:** `gameplay_full.mp4` (65s, 1080p30) and `gameplay_short.mp4`
  (15s) are usable as a source for a rough assembly, but the captures above will look
  better than carving from a single meandering session.

## Export specs

- YouTube / primary: 1920x1080, 30fps, H.264.
- itch.io: 1920x1080 or 1280x720, under the size cap.
- Social (Reddit/X): 1280x720; consider a 1:1 or 9:16 crop for mobile feeds.

## Extended cut (optional 45s)

If a longer cut is wanted later, expand rather than restructure:
- Lengthen the counterplay montage and the escalation beat.
- Promote the trace/Admin and dual-rendering overlays to short full-screen cards.
- Add the WAN2 cinematic as a 4-7s cold open in the 0.0s slot; the rest of the timeline
  is unchanged.

## Handoff

A rough proof-of-concept assembly can be built with ffmpeg from the existing two
captures plus text cards and `level1_stealth.ogg`, to sanity-check the structure before
recording the clean clips above.
