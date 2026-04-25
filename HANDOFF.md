# BUILD-A-BOX — Claude Code Handoff Document

**Project status: Live at https://viaxarmada.github.io/BUILD-A-BOX/**
**Date prepared: 2026-04-25**
**Prepared for: Claude Code (or any LLM/developer continuing this work)**

---

## TL;DR — Recently resolved (2026-04-25 follow-up)

- **Single-file artifact concept dropped** — only the GitHub Pages folder build is supported.
- **Door open animation bug fixed** — `mixer._actions` was undefined; now uses `inst.getActions()`.
- **Mobile portrait** — rotate-to-landscape overlay added; players are prompted to rotate, with a "Continue anyway" escape hatch.
- **Background music added** — 90-second 8-bit chiptune loop in `assets/bgm.ogg`/`bgm.m4a`. SFX still procedural.
- **Repo content corrected** — earlier commits had files from the unrelated Streamlit-era project; replaced with the correct self-contained `index.html` + `assets/` + `models/`.

---

## Project goal

Convert a Smurfit Westrock PowerPoint training game (`/mnt/user-data/uploads/Design_your_Own_SRP_GAME.pptx`) and accompanying animation reference video into a self-contained HTML web game. The game teaches packaging design through a 3-portal interactive flow with a fictional client (Monster Snacks, cheese flavor).

**Two delivery formats are required:**
- **Production zip** (`build-a-box.zip`) — full-quality folder build with all assets, served via static web hosting
- **Single-file artifact** (`build-a-box-playable.html`) — self-contained HTML with everything inlined, openable from `file://`

---

## Current file structure

```
/mnt/user-data/outputs/build-a-box/
├── index.html              # 3,380 lines — entire game (HTML + CSS + JS)
├── README.md               # End-user documentation
├── HANDOFF.md              # This file
├── assets/
│   ├── three.min.js        # Three.js r128 (603 KB)
│   ├── GLTFLoader.js       # Three.js examples/js/loaders/GLTFLoader.js (96 KB)
│   ├── scene-factory.jpg, scene-warehouse.jpg, scene-store.jpg, scene-costco.jpg
│   ├── door-red.png, door-yellow.png, door-green.png
│   ├── tray-pallet.png, tray-single.png, tray-corner.png  (2D fallbacks)
│   ├── paper-kraft.png, paper-white.png  (2D fallbacks)
│   ├── bag-monster.png, pedestal.png  (2D fallbacks)
│   ├── logo-monster.png, logo-monster-orange.png, logo-ignite.png
│   ├── paper-card.png, badge-queso.png, badge-delicious.png
└── models/
    ├── Bag_of_chip.glb            (1.93 MB — Monster Snacks bag)
    ├── Pallet_Tray.glb            (75 KB)
    ├── Single_sided_tray.glb      (374 KB)
    ├── Post_Tray.glb              (1.40 MB — Corner Post tray)
    ├── Kraft_Roll_of_Paper.glb    (28 KB)
    ├── White_Roll_of_Paper.glb    (28 KB)
    ├── Door1.glb                  (117 KB — red door, 4 anims)
    ├── Door2.glb                  (117 KB — green door, 4 anims)
    ├── Door3.glb                  (117 KB — yellow/orange door, 4 anims)
    ├── Final_Door.glb             (53 KB — double-door with open animation, 2 anims)
    └── Pedestal.glb             (119 KB — pedestal/turntable)

Total: index.html 3,380 lines, models folder 4.4 MB, full zip 5.3 MB
```

---

## What works

The game flow is end-to-end functional and tested via headless Chrome + DevTools Protocol with score 9/9 confirmed:

1. **Title** → glowing BUILD-A-BOX logo with START GAME button
2. **Congratulations** → text fades in line by line
3. **Rules** → 2-paragraph explanation; large red door is the "advance" button (uses `Final_Door.glb` with baked open animation in production build)
4. **Mission** → 2 paragraph fast fade
5. **Client brief** → Monster Snacks bag rocks side-to-side (-25° to +25°, NOT full Y-rotation, to avoid mirrored-text bug from flipping a 2D PNG); torn-tape paper card drops in from top
6. **Let's Create** → bag flies in on parabolic arc onto a pedestal (uses `Bag_of_chip.glb` + `Pedestal.glb`)
7. **Portal selection** → 3 doors centered, same height, all clickable. User picks one. Selected door's red light flashes, non-selected dim, chosen door plays its baked GLB open animation, Monster bag jumps + spins 720° behind it, then **teleport effect** (blur + zoom out → blur + zoom in) transitions to Level 1
8. **Level 1 — Factory** → 3 trays as rotating 3D models (Pallet_Tray, Single_sided_tray, Post_Tray)
9. **Level 2 — Warehouse** → 2 paper rolls (Kraft, White) as rotating 3D
10. **Level 3 — Store** → focus selection (Logo / Characteristics / Slogan)
11. **Finale** → score count-up X/9 with rank only (NO per-level recap by design)

**Best-fit answers (silently scored, max 9):**
- Corner Post Tray (Level 1, option 3) → 3pts
- White Paper (Level 2, option 2) → 3pts
- Brand's Logo (Level 3, option 1) → 3pts

Picking those three gives 9/9 → "MASTER PACKAGING DESIGNER" rank.

---

## Architecture

### Single-file HTML structure

`index.html` contains everything — DOM, CSS, JS, asset references. No build step, no npm install at runtime.

### Three.js 3D system (most important architecture)

**Generic `init3DModel(canvasId, modelPath, opts)` function** at line ~2500. Every 3D object on screen uses this same function with different parameters. It:

1. Cleans up any previous instance for that canvas (cancels RAF, disposes geometries/materials/renderer, calls `forceContextLoss()` to free GPU memory)
2. Creates `THREE.Scene`, `PerspectiveCamera`, `WebGLRenderer` with `alpha: true`
3. Adds standard lighting: ambient + directional key + directional fill + cyan rim point light
4. Loads the GLB via `THREE.GLTFLoader`
5. Auto-centers and scales the model to fit `targetSize` using `THREE.Box3().setFromObject(model)`
6. Sets `material.side = THREE.DoubleSide` and `map.encoding = THREE.sRGBEncoding` for proper PBR rendering
7. Stores animation clips and actions on the instance for later programmatic playback
8. Registers a `resize` listener to keep the renderer sized correctly
9. Returns an instance object with `cleanup()`, `getModel()`, `getMixer()`, `getActions()`

**Tracking & lifecycle:**
- `_3DInstances = new Map()` keyed by canvas ID — ensures no duplicate WebGL contexts for the same canvas
- `cleanup3DScene(prefix)` called on scene transitions to dispose all instances whose canvas ID starts with that prefix (e.g., `cleanup3DScene('tray-')` on leaving Level 1)
- Each scene's `onSceneEnter` block calls cleanup for non-relevant prefixes, then `setTimeout(initFn, 100-200ms)` to let the canvas measure its size after layout

**Convenience initializers:**
- `init3DBag()` → `bag-3d-canvas` ← `models/Bag_of_chip.glb`
- `init3DPedestal()` → `pedestal-3d-canvas` ← `models/Pedestal.glb`
- `init3DTrays()` → 3 canvases ← Pallet/Single_sided/Post tray GLBs
- `init3DRolls()` → 2 canvases ← Kraft/White paper roll GLBs
- `init3DPortalDoors()` → 3 canvases ← Door3/Door1/Door2 GLBs (note: visual-color-to-GLB mapping)
- `init3DRulesDoor()` → `rules-door-3d-canvas` ← `models/Final_Door.glb`

**Animation triggering:**
- Doors are loaded with `playAnimations: false` so they stay closed
- `playPortalDoorOpenAnimation(slotIndex)` called at 1900ms after portal click
- `playRulesDoorOpenAnimation()` called when rules door is clicked, with 1100ms delay before scene advance
- Each `play*Animation` function resets actions, sets `LoopOnce` + `clampWhenFinished`, and plays them

**Portal door color mapping (slot index → GLB):**
- Slot 1 (yellow visual) → `Door3.glb` (yellow/orange tint, RGB 0.65, 0.27, 0)
- Slot 2 (red visual) → `Door1.glb` (red, RGB 1.0, 0, 0)
- Slot 3 (green visual) → `Door2.glb` (green, RGB 0, 0.21, 0)

### CSS animation system

- `seq-*` classes (`seq-fade`, `seq-up`, `seq-pop`, `seq-pill`, `seq-left`) with `data-delay="n"` attribute (n is multiplier, base 130ms)
- 16 stagger delay slots defined: `[data-delay="1"]` through `[data-delay="16"]`
- `restartSceneAnimations(sceneEl)` blanks `el.style.animation = 'none'`, forces reflow, then restores — used when entering a scene to replay animations from start

### Stage scaling (most recently changed, may need work)

```css
#stage-wrapper {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  overflow: hidden;
}
#stage {
  width: 1600px;
  height: 900px;
  /* transform: scale(N) set by JS */
}
```

```js
function scaleStageToFit() {
  const designW = 1600, designH = 900;
  const scale = Math.min(window.innerWidth / designW, window.innerHeight / designH);
  document.getElementById('stage').style.transform = `scale(${scale})`;
}
```

This produces the letterboxed-into-a-band appearance on tall portrait viewports (the user's mobile screenshot). The math is correct, but the visual result is wrong on portrait phones — most of the screen is wasted black space. Likely needs a UX rethink (rotate to landscape prompt? Different layout for portrait? Auto-rotate the stage 90° and ask user to turn phone?).

### Scene transitions

- `goToScene(id)` — fades out current scene (380ms), then activates new one and replays its animations
- `teleportToScene(targetId)` — full blur + zoom-out (900ms) → swap → blur + zoom-in (800ms). Used for portal-to-level1 and level-to-level transitions to avoid showing intermediate screens
- `goBack()` — replays previous scene with full animations restored, refunds score if leaving a level

### Other behaviors

- **Web Audio API** procedural sounds: click, hover, confirm, whoosh, fanfare, ambient pad. M key toggles mute.
- **Keyboard nav**: Enter/Space advances, Backspace goes back, 1/2/3 selects options on level scenes, ←/→ navigates between options
- **Dev URL params**: `?jump=scene-X` jumps to a scene with animations disabled (used for QA captures); `?feedback=L,C` legacy
- **Back button**: top-left corner of every scene except title, portals (auto-advance), finale

---

## The two unresolved issues

### Issue 1: Artifact missing two GLB models

**Current state:** When building the single-file artifact, my Python build script intentionally skips two large GLB files (`SKIP_MODELS = {'Bag_of_chip.glb', 'Post_Tray.glb'}`) to keep the artifact under 2.5 MB. The error message the user is seeing (`"Model not in artifact: Bag_of_chip.glb"`) is this fallback firing as designed.

**Why this is wrong:** The two skipped models are the most prominent visual elements in the game (the snack bag is on the create scene AND should be the focal point; the corner-post tray is the best-fit answer for Level 1). Skipping them defeats the purpose of integrating 3D models in the first place. The artifact should include ALL the models even at the cost of a larger file size.

**What to do:** Either:
- **Option A (recommended):** Inline all GLBs. The artifact would be ~6.2 MB (1.66 MB + 1.93 MB Bag + 1.40 MB Post = ~5 MB encoded plus the rest = ~6.2 MB). Still loadable for a static demo file.
- **Option B:** Use Draco compression or meshopt to shrink the GLB files first (Bag_of_chip can probably be reduced to ~400 KB). Tools: `gltf-transform` CLI from npm.
- **Option C:** Ditch the single-file artifact concept entirely; only deliver the production zip + folder.

**Build script location:** Inline Python in the chat history. Can be reconstructed easily — the relevant lines are in `/mnt/user-data/outputs/` history.

### Issue 2: Mobile portrait layout

**Current state:** Stage is fixed 1600×900 px and CSS-scaled to fit viewport. On a portrait phone (e.g. iPhone 13 at 390×844), the scale factor is `Math.min(390/1600, 844/900) = 0.244`. So the stage renders at 390×219 px in the middle of an 844px-tall screen — letterboxed into a tiny horizontal band with massive black bars top and bottom.

**What the user wants:** Content should fill the screen properly on mobile. Right now it's unusable on a phone.

**Possible solutions:**
- **Option A (simplest):** Force landscape orientation with CSS `screen.orientation.lock('landscape')` (limited browser support) or show a "Please rotate your phone" overlay on portrait
- **Option B:** Build a portrait-specific layout that re-stacks the content vertically. Significant work — most scenes are designed left-right or with absolute positioning that assumes landscape
- **Option C:** Keep current letterbox approach but make the black bars not all-black — extend the gradient background, add the BUILD-A-BOX logo or branding in the dead zones
- **Option D (probably best):** Auto-rotate the stage 90° via CSS transform when portrait detected. The stage stays 1600×900 internally, but rotates to fill portrait screens. Slightly weird UX but content is fully visible

**Recommendation:** Try Option A first (rotate prompt) since this is a training game intended to be played in landscape on a tablet or laptop. If users insist on portrait phone use, then Option D.

---

## How to run for development

### Production build (full quality, all 11 GLBs)

```bash
cd build-a-box/
python3 -m http.server 8080
# Open http://localhost:8080 in Chrome
```

**Critical:** opening `index.html` directly via `file://` will block GLB loads due to browser CORS policy on local files. Must use a web server.

### Single-file artifact

Open `build-a-box-playable.html` directly in any browser. Works from `file://` because GLBs are embedded as `data:` URIs (CORS-safe). Currently missing 2 of 11 GLBs by design (Bag_of_chip and Post_Tray) — see Issue 1.

### Build the artifact from the production folder

The Python build script lives in chat history. The general flow:
1. Read `build-a-box/index.html`
2. Read all images from `assets/` (or pre-compressed versions from `/home/claude/assets-tiny/`)
3. Read all GLBs from `models/`
4. Read `assets/three.min.js` and `assets/GLTFLoader.js`
5. Inline Three.js + GLTFLoader as `<script>` tags (replacing the dynamic CDN loader at top of HTML)
6. Build a JS asset map: `{"asset:filename.png": "data:image/png;base64,..."}`
7. Build a JS model map: `{"filename.glb": "data:model/gltf-binary;base64,..."}`
8. Replace `assets/X.png` references in HTML with `asset:X.png` tokens
9. Inject a bootstrap `<script>` that:
   - Resolves `asset:X.png` tokens in `<img src>` and inline `style` attributes
   - Walks all CSS rules and rewrites `asset:X.png` in `background-image: url(...)` etc.
   - **Patches `THREE.GLTFLoader.prototype.load`** to translate any URL ending in `.glb` to its inline data URI from the model map. This is the critical part.

Key gotcha: when patching GLTFLoader, the regex must not assume any path prefix. Use `/([^\/]+\.glb)$/` to extract just the filename, then look up in the model map.

---

## Things to verify after any change

These are the regression checks:

1. **All 11 scenes render without errors** — title, congrats, rules, mission, client, create, portals, level1, level2, level3, finale
2. **Full flow with score 9/9** — pick options 3, 2, 1 across the three levels
3. **Back button works** — replays animations on previous scene
4. **Portal selection animation completes** — chosen door's light flashes, door opens (3D anim), bag jumps behind, teleport happens
5. **Door light flashes** between levels (red light on the level's portal-door element)
6. **No `console.error` and no thrown exceptions** in DevTools
7. **No GLTFLoader warnings** about missing GLBs (assuming all are inlined or available via web server)
8. **3D models actually render** — open the create scene and look for the bag rotating; not just see the canvas element

### Headless test command

I built a Node.js + chrome-devtools-protocol test that walks through the full flow. It's at `/home/claude/flow-test-final.js` (not in the deliverable zip). Pattern:

```js
const { spawn } = require('child_process');
const WebSocket = require('ws');
// Spawn chrome with --remote-debugging-port=N --use-gl=swiftshader
// Connect WS, enable Runtime + Page domains
// Navigate, walk through clicks with appropriate delays
// Assert state.currentScene, state.score, _3DInstances.has(...)
// Capture screenshots via Page.captureScreenshot
```

Use this as your end-to-end test harness.

---

## What was tried but didn't work

1. **CDN loading of GLTFLoader** — cdnjs only hosts the four core three.js files for r128, not GLTFLoader (which lives in `examples/js/loaders/`). Switched to jsDelivr which mirrors the full npm package. But CDN loading fails entirely when the artifact is opened in environments that block external scripts (some sandboxed iframes). **Solution: inline Three.js + GLTFLoader as `<script>` tags.** That's currently in place.

2. **Replacing `models/X.glb` with `model:X.glb` in JS source code** — this corrupted the GLTFLoader patch's regex. **Solution: don't replace anything in the JS source; leave URLs as `models/X.glb` and have the patched `loader.load()` translate them at call time.**

3. **`forceContextLoss()` in cleanup** — added this to ensure GPU memory is freed when scenes change. Necessary because some browsers leak WebGL contexts otherwise.

4. **Multiple Three.js + GLTFLoader instances on screen** — works, but each instance creates its own renderer/canvas/context. Browsers limit total active WebGL contexts (Chrome: 16). On Level 1 + portal scene + create scene we use 3-5 contexts. Cleanup must be aggressive between scenes.

5. **2D PNG fallback rotation as a Y-axis spin** — caused mirrored-text bug because the back of a 2D PNG is the same artwork mirrored. **Solution: rock between -25° and +25°, never showing the back face.**

---

## Design references

User-provided references in `/mnt/user-data/uploads/`:
- `Design_your_Own_SRP_GAME.pptx` — original PowerPoint training deck (15 MB)
- `record_2026-04-24_05-20-09.mp4` — animation reference video
- `slide_3.JPG` — rules scene reference (red door is the advance button)
- `Slide_7.JPG` — portal selection reference (3 doors same height, centered)
- `Slide_7_door_selection__door_opens.JPG` — chosen-portal animation reference (door opens, bag visible inside)
- `IMG_2417.png`, `IMG_2418.png` — mobile screenshots showing layout problems (header too big, text wrapping issues)
- `IMG_2420.png` — mobile screenshot of current build showing letterbox + GLB fallback warning

---

## Recommended next steps for Claude Code

In priority order:

1. **Set up dev environment**
   - `cd build-a-box/`
   - `python3 -m http.server 8080` (terminal 1)
   - Open `http://localhost:8080` in Chrome
   - Open DevTools console
   - Verify the production build works without GLB warnings (it should)

2. **Decide on the artifact strategy** — given the size constraint vs the user's desire to see all 3D models, either:
   - Compress GLBs with `gltf-transform optimize` and inline all of them
   - Drop the artifact concept and only deliver the folder build

3. **Fix mobile portrait layout** — implement either a rotate-to-landscape prompt or auto-rotate the stage. The user is testing on iPhone vertically; this needs to work.

4. **Write a real test harness** — Playwright is ideal (npm `playwright`). Tests should:
   - Walk the full flow
   - Assert no console errors
   - Capture screenshots at each scene
   - Verify 3D `_3DInstances` Map populates correctly
   - Run on both desktop and mobile viewport sizes

5. **Optional improvements waiting:**
   - Reduce header pill size further (user has asked for this multiple times)
   - Verify content sizing on the create scene (bag has been resized but may need more polish)
   - The pedestal-3d-canvas was added but its visual placement on top of the existing 2D pedestal image may overlap weirdly; verify

---

## Contact / context

This work was iterated in a chat session with Claude (Anthropic). The user is Via, R&D and Digital Experience Manager at Smurfit Westrock. The project is for the company's "Ignite" innovation training program. The chat session became inefficient at this scale and was handed off to Claude Code per user request.

The user's frustration is justified — incremental chat-based debugging of a 3,000+ line single-file game with multiple build outputs and 3D rendering is the wrong tool. Claude Code with file-watching, dev-server access, and direct browser console visibility is the right tool.
