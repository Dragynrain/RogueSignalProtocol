# PLAN: Flathub Submission (build-from-source) + miniaudio audio backend

Current-state plan. Git tracks history; do not add revision logs here.

## Goal
Get Rogue Signal Protocol onto Flathub under app-id `info.aforster.roguesignalprotocol`,
built entirely from source (Flathub requirement), superseding the closed beta PR
flathub/flathub#7414.

## Key decisions (settled)
1. Flathub requires building from source. The PyInstaller-binary manifest is invalid and
   must be rewritten. Binary wheels are NOT allowed; every C-extension dep compiles from sdist.
2. Audio: replace pygame with `miniaudio` (Path A). miniaudio is a single self-contained
   from-source dependency (bundled public-domain C, decodes WAV/OGG, plays back), no
   shared-modules, no second SDL stack. tcod 19.6 is SDL3; pygame is SDL2, so keeping pygame
   would drag a separate SDL2 stack - rejected.
3. One audio backend for all platforms (no fork). The change debuts on Flatpak but ships to
   Windows/itch/AUR at the next sync release.
4. Versioning: Flatpak ships as 1.0.1 (contains miniaudio). Windows/itch/AUR stay on their
   published 1.0.0 binaries. Next real update = 1.0.2, rebuilt from one tag to all platforms,
   resyncing everyone on the new backend.
5. Published v1.0.0 artifacts are NOT re-cut for the README fix; corrected README.txt rides
   with 1.0.2 (re-cutting v1.0.0 would break the AUR sha256 pin).

## Runtime dependency set (the real subset; rest of requirements.txt is dev tooling)
- platformdirs (universal wheel), freetype-py (universal wheel)
- cffi, pillow (sdist, link libs present in runtime)
- numpy (sdist; needs meson/meson-python/ninja/Cython vendored as build deps)
- tcod 19.6 (sdist; compiles libtcod via cffi, links SDL3 from runtime)
- miniaudio (sdist; self-contained, replaces pygame)
- DROP: pygame and all PyInstaller/test/lint tooling

## Work items

### A. Audio rewrite (pygame -> miniaudio) - cross-platform, TDD
Rewrite `src/rsp/systems/audio.py` behind the UNCHANGED `SoundManager` public interface
(`preload_sounds`, `load_sound`, `play_sound`, `play_music`, `stop_music`, `is_music_playing`,
`update`, `update_volumes`, `set_sound_cooldown`, `cleanup`, plus `NullSoundManager`).
- Decode: WAV via stdlib `wave` (or miniaudio), OGG via miniaudio.
- Mixer: one miniaudio PlaybackDevice; mix active sounds as int16 numpy frames in the callback.
  Implement 16-channel mixing, per-sound volume, priority channel-stealing, 50ms dedup,
  music streaming with looping + fade in/out, master/music/sfx volume + Linux music boost.
- Keep behavior identical to current pygame version (same call sites elsewhere unchanged).

### B. Remove other pygame uses (found beyond audio.py)
- `core/file_paths.py` `show_fatal_error_and_exit()`: pygame error window -> tcod-based dialog
  (must stay a visible GUI on Windows where console is hidden).
- `core/loop.py:567`: replace `pygame.display.get_surface()` headless check with non-pygame check.
- `core/loop.py:586`: replace `pygame.mixer.music.get_busy()` with `is_music_playing()`.
- `utils/debug_export.py:155`: report miniaudio version instead of pygame version.
- Update tests: test_audio_system.py, test_audio_edge_cases.py, test_main_game_loop.py,
  test_game_file_paths.py.
- Update `requirements.txt` (drop pygame, add miniaudio), `docs/dependencies.json`, `ci.yml`.

### C. Flatpak manifest rewrite (on dragserver)  [IN PROGRESS]
- DONE: packaging/linux/requirements-flatpak.txt (runtime deps only).
- DONE: flatpak-pip-generator (runtime org.freedesktop.Sdk//25.08) produced two committed files:
  - packaging/linux/python3-modules.json - tcod/numpy/pillow/platformdirs/miniaudio/freetype-py,
    all compiled pkgs as SDIST (Flathub-compliant), pure-python as universal wheels.
  - packaging/linux/python3-build-deps.json - meson-python (+pyproject-metadata) vendored, because
    numpy 2.3.2 builds with --no-build-isolation and the 25.08 SDK lacks meson-python. The SDK
    DOES have meson, ninja, cython, setuptools, wheel, packaging (so pillow/cffi/tcod/miniaudio/
    freetype build on setuptools without extra vendoring; only numpy needed meson-python).
  - 25.08 SDK Python is 3.13.13 (NOT 3.12). Install prefix is /app/lib/python3.13/site-packages;
    manifest sets PYTHONPATH there so numpy's no-build-isolation build finds meson-python.
  - KNOWN: python3-modules.json duplicates numpy/cffi across submodules (tcod pulls them, and they
    are also top-level). Wasteful build time; dedup later. Not blocking.
- IN PROGRESS: offline deps-only build (deps-test.yml on dragserver) to prove numpy/tcod/miniaudio
  compile in the SDK with no network. Manifest module order: build-deps -> modules.
  - numpy compiles cleanly once meson-python is vendored. CONFIRMED.
  - tcod build initially produced version 0.0.0: its backend is setuptools.build_meta with
    setuptools_scm dynamic version, but setuptools_scm is NOT in the SDK, so setuptools defaulted
    to 0.0.0 and pip rejected it. FIX: vendor setuptools_scm (+vcs_versioning) in build-deps; modern
    setuptools_scm reads the version from the sdist PKG-INFO (19.6.0). build-deps now =
    meson-python + setuptools-scm (+vcs_versioning).
  - DO NOT set a global SETUPTOOLS_SCM_PRETEND_VERSION: it pins ALL setuptools_scm packages to
    that version (freetype-py wrongly became 19.6.0). Vendoring setuptools_scm alone is correct -
    it reads each package's real version from its own sdist PKG-INFO (tcod 19.6.0, freetype 2.5.1).
  - Manifest build-options.env keeps only PYTHONPATH=/app/lib/python3.13/site-packages.
  - tcod's native _libtcod extension did NOT build at first: tcod uses cffi's setuptools hook
    (cffi_modules=) to compile _libtcod, but with --no-build-isolation cffi was not importable at
    tcod build time, so setuptools ignored cffi_modules ("Unknown distribution option: cffi_modules")
    and produced a pure-python none-any wheel with no _libtcod. FIX: vendor cffi in build-deps too
    (built before tcod, on PYTHONPATH). SDL3 is present in the 25.08 SDK (libSDL3.so, pkg-config
    sdl3 = yes), which is what tcod 19.6 links.
  - tcod build also imports pcpp, requests, attrs (its build-system.requires); all vendored.
  - tcod build_sdl.py finds SDL3 headers via `pkg-config sdl3 --cflags`, but pkg-config suppresses
    the default /usr/include, emitting only -I/usr/include/libdecor-0 -> tcod could not find
    SDL3/SDL.h and asserted. FIX: set PKG_CONFIG_ALLOW_SYSTEM_CFLAGS=1 (makes pkg-config emit
    -I/usr/include). Added to manifest build-options.env.
  - Final build-deps set: meson-python, setuptools-scm, cffi, pcpp, requests, attrs (+transitive).
  - tcod _libtcod C compile failed on `implicit declaration of function 'memset'` (cffi-generated
    C lacks <string.h>; SDK GCC 14 treats implicit decls as errors). FIX: CFLAGS=
    -Wno-implicit-function-declaration (downgrades to warning; memset links from libc).
    Also hit -Wint-conversion on libtcod tileset_fallback.c (fmemopen). GCC 14 promoted three
    warnings to default errors; clear all with CFLAGS=
    "-Wno-implicit-function-declaration -Wno-int-conversion -Wno-implicit-int".
  - Final manifest build-options.env: PYTHONPATH=/app/lib/python3.13/site-packages,
    PKG_CONFIG_ALLOW_SYSTEM_CFLAGS=1,
    CFLAGS="-Wno-implicit-function-declaration -Wno-int-conversion -Wno-implicit-int".
- DONE / PROVEN: deps-only build is green. tcod (_libtcod.abi3.so + SDL3), numpy, miniaudio, PIL,
  cffi, freetype, platformdirs all build from source offline in 25.08 SDK and import in the sandbox
  (verified: import tcod/tcod.sdl.audio/numpy/miniaudio/PIL/cffi/freetype/platformdirs, tcod.lib loads).
  The hard part of the Flathub from-source requirement is solved. Final dep files in packaging/linux/:
  python3-build-deps.json + python3-modules.json. Build env flags above are required.
- DONE / PROVEN: full Flatpak (deps + game module) builds offline; SELF-TEST OK via the installed
  launcher (rsp imports, config/content loads, and initialize_data_directories() succeeds -> the
  save-dir fallback to ~/.var/app/.../data works in the read-only sandbox; #1 runtime risk cleared).
- DONE: flatpak-builder-lint - manifest passes (exit 0); builddir clean except
  appstream-external-screenshot-url (expected pre-publish; Flathub mirrors screenshots on its build).
- DONE: fixed desktop file CRLF->LF (failed desktop-file-validation) + .gitattributes guard for
  *.desktop/*.xml/*.yml + the launcher.
- DONE: repo submission files updated to the validated from-source config:
  - packaging/linux/info.aforster.roguesignalprotocol.yml rewritten (build-deps + modules + game
    module; --device=dri + --device=input; build-options.env; game source = v1.0.1 tag archive
    with sha256 TODO after tagging).
  - packaging/linux/rogue-signal-protocol launcher -> python3 RogueSignalProtocol.py.
  - flathub.json PyInstaller rationale dropped (x86_64-only kept).
- Validated on dragserver in ~/rsp-flatpak with game source rsynced as `type: dir` (gamesrc/).

## Remaining to submit
1. Manual: run the Flatpak windowed on a Linux desktop (dragserver is headless) - confirm gameplay +
   audio (miniaudio) + gamepad. Record a video for the PR.
2. Commit the audio + manifest work; bump done (1.0.1); tag v1.0.1 and push.
3. Fill the manifest source sha256 from the pushed v1.0.1 tag archive.
4. Human submission: PR vs flathub/flathub base `new-pr`, branch+title = app-id, supersede #7414,
   include video + dev-history justification. aforster.info domain verification token post-accept.
- Manifest module pulls SOURCE archive at the v1.0.1 tag (archive/refs/tags/v1.0.1.tar.gz),
  not the release tarball. Install src tree + JSON + font + graphics/sound/music to
  /app/lib/rogue-signal-protocol.
- Launcher: cd to game dir, `exec python3 RogueSignalProtocol.py "$@"` (entry script
  chdir's itself when not frozen).
- finish-args: `--device=all` -> `--device=input`. Confirm 25.08 is latest runtime.
- Drop PyInstaller rationale from flathub.json; keep `only-arches: [x86_64]`.

### D. Runtime-correctness risks to verify on dragserver
- Save dir: `initialize_data_directories()` tries portable mode first (/app is read-only),
  must fall back to platformdirs (~/.var/app/.../data) without fatal-erroring. TEST.
- miniaudio sdist builds clean in 25.08 SDK; 16-way numpy mixing keeps frame rate. TEST.
- Which SDL major tcod 19.6 links (expected SDL3) and that its sdist build uses runtime SDL,
  no network fetch. TEST.
- v1.0.1 source archive includes JSON content, font, graphics/sound/music (not gitignored).

### E. Release 1.0.1 (gates the Flathub-buildable tag)
- Bump `core/version.py` to 1.0.1.
- Add metainfo `<release version="1.0.1">` entry (note: Linux audio backend -> miniaudio).
- Tag v1.0.1 AFTER audio rewrite + pygame removal are merged and tested.

### F. Domain verification (parallel, non-blocking)
- aforster.info: add visible link tying domain to app/dev.
- Stage `.well-known/org.flathub.VerifiedApps.txt` token; publish AFTER acceptance.

### G. Submission (HUMAN, after blockers green)
- PR vs base branch `new-pr` of flathub/flathub; branch+title = `info.aforster.roguesignalprotocol`.
- PR body: video of Flatpak running; note it supersedes #7414 + app-id change
  (com.dragynrain -> info.aforster); dev-history justification (alpha 0.8.0 Nov 2025 ->
  betas Dec 2025 -> 1.0.x Jun 2026, tags + CHANGELOG).

## Done
- README.md / README.txt / docs/ROADMAP.md softened: Flatpak marked "coming soon" not live.
- Audio backend rewritten pygame -> miniaudio (src/rsp/systems/audio.py). Single PlaybackDevice
  at 22050Hz stereo, software numpy mixer (16 voices + music), WAV/OGG via miniaudio.decode_file,
  dedup cooldown, priority voice-stealing, music looping + fade in/out. Verified end-to-end on
  Windows (device open, decode, play sfx + music, fade, cleanup) and via headless mixer unit tests.
- Single global music stream preserved across separate menu/engine SoundManagers via class-level
  SoundManager._music_owner (replaces pygame.mixer.music global semantics).
- All pygame removed from src: core/loop.py (headless check now SDL_VIDEODRIVER==dummy;
  music check now is_music_playing()), core/file_paths.py (fatal-error dialog now tcod-based),
  utils/debug_export.py (reports miniaudio version). Zero `import pygame` remains repo-wide.
- requirements.txt: pygame removed, miniaudio==1.71 added.
- ci.yml: env-verify step checks miniaudio instead of pygame.
- Tests rewritten/passing: tests/unit/test_audio_system.py (24 pass, miniaudio-based),
  test_main_game_loop.py sound test, test_game_file_paths.py TestFatalErrorDisplay (tcod-based).

## Verified after audio rewrite
- docs/dependencies.json regenerated via `PYTHONPATH=src pydeps ... --show-deps --max-bacon 3`
  (rsp subtree + miniaudio present, pygame gone). CODE_QUALITY_TOOLS.md command fixed to add
  PYTHONPATH=src (post-reorg the old command silently dropped the rsp subtree).
- Audio tests pass under miniaudio: unit test_audio_system.py (24) + integration
  test_audio_edge_cases.py (28, run with --audio) in ~3.7s. The earlier "5 min" was
  test_main_game_loop/agent tests in a mixed run, NOT audio - no speed follow-up needed.
- Version cut to 1.0.1 (targeted): game_rules.json, README.md (badge + line), README.txt,
  metainfo <release> entry, CHANGELOG. Deliberately NOT bumped: PKGBUILD/.SRCINFO/
  AppImageBuilder.yml (track published 1.0.0 binaries until the 1.0.2 sync). bump-version.py
  --check 1.0.1 release passes.

## Follow-up (after full suite green)
- Uninstall pygame from the dev venv to confirm nothing imports it.

## Sequencing note for manifest
- The from-source manifest's final source should be the v1.0.1 GitHub tag archive, but that
  tag does not exist remotely until the audio change is committed+pushed+tagged. For build
  validation on dragserver BEFORE tagging, point the manifest source at a local dir / branch /
  commit SHA, then swap to archive/refs/tags/v1.0.1.tar.gz for the actual submission.
