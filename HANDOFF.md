# BUILD-A-BOX — Session Handoff

**Date:** 2026-04-26
**Repo:** `D:/PROJECTS/viaxarmada/BUILD-A-BOX/` (NOT `D:/PROJECTS/IGNITE/build_a_box/` — that's an older Streamlit/Reveal.js sibling that's not the active project)
**Live:** https://viaxarmada.github.io/BUILD-A-BOX/
**Working file:** all logic lives in `index.html` (~3500 lines: HTML + CSS + JS)

---

## How to run

```
cd D:/PROJECTS/viaxarmada/BUILD-A-BOX
python -m http.server 8080
# Open http://localhost:8080
```

Local dev only — **do NOT push to GitHub without explicit user approval.** The user said "make all repairs locally before we push to github."

---

## Working agreement / SOPs (memory-backed)

These are persistent rules. Stored in `C:/Users/T/.claude/projects/D--PROJECTS-IGNITE-build-a-box/memory/`:

1. **Verify visually before reporting done** — DOM `getBoundingClientRect()` inspection alone is not enough. Always `preview_screenshot` after a UI change. If the screenshot tool times out (it does sometimes), report that explicitly so the user sanity-checks themselves.
2. **Auto-rescale preview to fill the pane after every edit** — call `preview_resize` with `preset: "desktop"` (uses pane native size). The page has a 1600×900 design canvas centered in the body, so non-16:9 viewports letterbox internally — that's expected and the user prefers it over a smaller viewport that fits 16:9 exactly.
3. **No GitHub pushes without approval** — local-only edits are the default.

---

## Architecture (current, post-Three.js migration)

Three.js was replaced by `<model-viewer>` (Google's web component) months ago. All 3D rendering is now declarative HTML.

### Stage layout
- Body uses `display:flex; align-items:center; justify-content:center` to center `#stage`
- `#stage` is fixed 1600×900 design canvas, scaled via JS to fit viewport
- Non-16:9 viewports letterbox internally (top/bottom or left/right black bars)

### Scene flow (`SCENE_FLOW` array around line 2697)
```
scene-title → scene-congrats → scene-rules → scene-mission → scene-client →
scene-create → scene-portals → scene-level1 → scene-level2 → scene-level3 → scene-finale
```

Each scene is a `<div class="scene" id="scene-X">`. Active one has `.active`. Transitions go through `goToScene(id)` (380ms fade) or `teleportToScene(id)` (blur+zoom out → swap → blur+zoom in, 1.7s total).

### Portal door system (most recently worked-on)

Three doors, each is one `<button class="portal-slot">` containing:
- `<model-viewer class="portal-door-3d">` rendering `Door1.glb` / `Door2.glb` / `Door3.glb`
- `<div class="portal-preview">` — destination peek behind the door (hidden until `.chosen`)
  - `.preview-scene.preview-factory` — background image (`scene-factory.jpg`) with offset to show the blue monster character
  - `<model-viewer class="preview-monster">` — `Bag_of_chip.glb` chip bag that jumps + spins
- `<div class="portal-light">` — red bell light overlay activated when `.chosen`

Click handlers wired in `runPortalSequence()` (called from `onSceneEnter('scene-portals')`).

### The animation gotcha (critical for level-completion doors too)

**Door1.glb / Door2.glb / Door3.glb each ship with 4 animation clips:**
- `Action` — the real smooth panel-open animation (21 LINEAR keyframes, real range 0.21–1.04s)
- `Door1`, `Door2`, `Door3` — 2-keyframe STEP-only no-ops (look like real anims but just snap between two static poses)

**`playGlbOpenAnimation(mvEl)` (around line 2790)** must pick `"Action"` specifically. Earlier code picked the first clip matching `/door|open/i` regex, which matched "Door1" — a no-op. Now it prefers `"Action"`.

**model-viewer's `play({repetitions:1})` resets `currentTime` to 0 when the clip ends.** To hold the door at the open pose, the function does:
1. `play({ repetitions: 1 })` — binds the mixer
2. `pause()` — stops auto-playback
3. `currentTime = 1.04` — direct rig pose
4. `requestAnimationFrame(() => { currentTime = 1.04 })` — re-apply on next tick
5. `setTimeout(() => { currentTime = 1.04 }, 100)` — re-apply after 100ms

The re-applies override model-viewer's internal mixer reset.

**`resetPortalDoors()`** uses the same pattern with `currentTime = 0` to return doors to closed pose. Called inside `goToScene` and `teleportToScene` whenever leaving `scene-portals`.

### Door-open visibility / camera gotcha

The Door1/2/3 GLBs animate the panel **inward** (away from the camera). At a 0° face-forward camera, the rotated panel projects to almost the same outline as the closed panel — visually invisible. Camera-orbit was set to `45deg` earlier to make the rotation visible at a 3D side angle, but the user wanted face-forward. Eventually settled on **`camera-orbit="0deg 78deg 5m"`** (face forward) **AND** the GLB Action animation IS visible from this angle because the panel's projection changes enough (the panel disappears into the doorway revealing the dark interior). Verified working — see the screenshot history.

If the user ever asks for "just the panel rotates while the frame stays in place" — that's already what the Action clip does (the bone in the GLB rotates only the Cube/Cylinder.001 meshes via skinning, not the frame Plane/Sphere meshes).

### Two-GLB combine attempt (DON'T REDO)

The user shipped `door_frame.glb` + `green_door.glb` thinking I could stack two model-viewers and animate just the panel. **It doesn't work** because:
- frame center at world Y=1.0
- panel center at world Y=0.5, depth Z=2.39 (modeled lying on its side, off-center)
- model-viewer auto-frames each independently — no shared coordinate system → can't overlay cleanly

Reverted to single Door1/2/3.glb + GLB Action clip. If the user revisits this, suggest: **combine the two meshes into one GLB in Blender with a panel-only animation track.**

### Other model-viewer behaviors
- Bag in scene-create has `id="bag-advance"` and class `advance` — clicking the bag (not just the START button) triggers the teleport effect to scene-portals. Handler in `wireAdvance` checks `state.currentScene === 'scene-create' && (btn.id === 'btn-lets-start' || btn.id === 'bag-advance')`.
- Removed `camera-controls` from all interactive model-viewers and added `disable-zoom disable-pan disable-tap` so clicking doesn't drag-rotate the model.

---

## Reusable patterns for future scenes

The user explicitly said: **"this action will need to be repeated to all the doors after every level is completed."** So scene-level1/2/3 will each need:
1. A door element (probably re-using a `Door1.glb` style GLB)
2. An open-on-click flow using `playGlbOpenAnimation(mv)` to play the "Action" clip
3. A reset-on-leave hook in `goToScene`/`teleportToScene`
4. Possibly the same teleport-out effect that scene-create's bag click already uses

Look at `choosePortal()` (around line 2858) for the click → open → wait → teleport pattern. Mirror it.

---

## Recent UI tweaks (last few iterations)

- `.portal-preview` height is `calc(70% - 15px)` — cropped from bottom to not bleed below the door frame
- `.preview-scene` background-position is `78% calc(65% - 40px)` — shifted to show the blue monster character on the right side of the factory image, raised 40px from baseline
- `.preview-monster` (chip bag) at `bottom: -12%` — sits low in the doorway threshold
- `.preview-monster` animation: `monsterReveal 0.4s ease 1.0s, monsterJumpSpin 1.6s 1.5s` — appears 1s after click (after door opens at ~1.2s), jumps + spins 720°, completes well before the 4.8s teleport

---

## Files of interest

- [index.html](D:/PROJECTS/viaxarmada/BUILD-A-BOX/index.html) — everything (HTML, CSS, JS in one file)
- `models/Door1.glb` etc. — door GLBs with the "Action" clip
- `models/Bag_of_chip.glb` — chip bag (used both on the create-scene pedestal AND inside the portal preview)
- `assets/scene-factory.jpg` — destination background for the portal preview, has a blue cartoon monster on the right side
- `assets/pedestal.png` — replaces what was Pedestal.glb earlier (the 3D model was swapped for a 2D image at user's request)

---

## Git state

- Remote: `https://github.com/viaxarmada/BUILD-A-BOX.git`
- Auth via Git Credential Manager (Windows Credential Manager) — was previously embedding a PAT in the URL; that token has been **revoked**.
- Don't push without explicit approval.

---

## Pending / likely next requests

Based on user's hints:
1. **Level-completion doors** — same pattern as portal doors at the end of each level → next level transition.
2. Possibly more fine-tuning on the portal preview (still iterating on bag/monster positioning).
3. Possibly more 3D ↔ 2D swaps for assets that aren't loading or sizing well.

---

## Things to absolutely NOT do

1. Don't `git push` unless the user explicitly says to push.
2. Don't restore the embedded-PAT remote URL.
3. Don't try to combine `door_frame.glb` + `green_door.glb` via two stacked model-viewers — it has been thoroughly attempted and the coordinate systems are incompatible.
4. Don't use the `/door|open/i` regex when picking the door-open animation clip — it matches the no-op "Door1" clip. Use `n === 'Action'` or fall back to the second clip after Action.
5. Don't claim "done" on a UI change without a screenshot or explicit "screenshot tool failed" disclaimer.
