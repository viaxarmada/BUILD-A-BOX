# BUILD-A-BOX
**An interactive educational game for Smurfit Westrock**

Converted from the original PowerPoint training deck into a self-contained web game with animation, music, procedural sound effects, and keyboard interaction.

**Live:** https://viaxarmada.github.io/BUILD-A-BOX/

---

## How to run

The game is delivered as a folder build served over HTTP. The live deployment lives on GitHub Pages — see **Deploy to GitHub Pages** below.

**Why a web server?** Modern browsers block `XHR`/`fetch` calls to `file://` URLs by default (CORS policy). Three.js's `GLTFLoader` uses XHR to load `.glb` model files. If you open `index.html` via double-click (file://), you'll see "GLB load failed" console warnings and the game will fall back to 2D for all 3D objects. The game still works, just without 3D rendering.

**Local web server (any of these):**

```bash
# Python (built-in)
cd build-a-box
python3 -m http.server 8080
# Open http://localhost:8080 in Chrome

# Node.js
npx http-server -p 8080

# VS Code: install "Live Server" extension, right-click index.html, "Open with Live Server"
```

**Deploy to static hosting:** Upload the entire `build-a-box/` folder to any static host (S3, Netlify, Vercel, Cloudflare Pages, GitHub Pages, Azure Blob Storage, SharePoint, your own internal web server). Everything will work because the host serves over HTTP/HTTPS.

No backend, no build step, no dependencies.

---

## Deploy to GitHub Pages

The repo is preconfigured to auto-deploy via GitHub Actions on every push to `main`. The workflow lives at `.github/workflows/deploy.yml` and uploads the entire repo root as the Pages artifact.

**One-time setup (per repo):**

1. Create a GitHub repo (public or private; private requires GitHub Pro/Team for Pages).
2. Push this folder's contents to the repo root:
   ```bash
   cd build-a-box
   git init
   git add .
   git commit -m "Initial BUILD-A-BOX commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
3. In the repo on GitHub, go to **Settings → Pages**.
4. Under **Build and deployment → Source**, select **GitHub Actions**.
5. Push any commit to `main` (or trigger the workflow manually under the **Actions** tab → **Deploy to GitHub Pages** → **Run workflow**).
6. After the action completes (~30–60 seconds), the site is live at:
   ```
   https://<your-username>.github.io/<repo-name>/
   ```

**Subsequent deploys:** just `git push`. The action redeploys automatically.

**Why this works for the 3D models:** GitHub Pages serves over HTTPS, so the GLB fetches succeed (no `file://` CORS issue). All 3D models, level video backgrounds, and image assets stream from the host as the user plays.

**Repo size note:** The folder is ~11 MB (4.4 MB GLBs + 4.5 MB MP4s + 1.8 MB images/JS + 110 KB HTML). GitHub's repo size soft-limit is 1 GB and per-file limit is 100 MB, so we're well under both.

---

## Keyboard controls

| Key | Action |
|-----|--------|
| `Enter` / `Space` | Advance, confirm, or select focused option |
| `→` / `↓` | Move focus to next option (in level scenes) |
| `←` / `↑` | Move focus to previous option |
| `1` `2` `3` | Directly select option 1, 2, or 3 |
| `M` | Toggle sound on/off |

Mouse and touch also work throughout — hover or click any element.

---

## Game flow

1. **Title** — BUILD-A-BOX splash screen with START GAME
2. **Intro** — Congratulations / you're designing packaging for Smurfit Westrock
3. **Rules** — The 3-portal game mechanic is explained
4. **Mission** — Overview of your role
5. **Client brief** — Monster Snacks (cheese flavor) wants to enter warehouse club stores
6. **Lets Create!** — Ready to start designing
7. **Level 1 — Factory (ShelfSmart):** Pick a tray type
   - Pallet Tray / Single-Sided Tray / **Corner Post Tray** (best fit)
8. **Level 2 — Warehouse:** Pick a paper type
   - Kraft Paper / **White Paper** (best fit)
9. **Level 3 — Store:** Pick a communication focus
   - **Brand's Logo** (best fit) / Product Characteristics / Slogan
10. **Finale** — Score (X/9), rank, and per-level breakdown

After each level, a feedback overlay explains the trade-offs of **all** options (not just the winner) so the player learns the reasoning behind the best fit for Monster Snacks' specific situation.

---

## Scoring

Each level awards 1–3 points:
- **3 points** — Best fit for this client scenario
- **2 points** — Strong choice with trade-offs
- **1 point** — Works, but not optimal

Total: **9 points maximum**.

| Score | Rank |
|-------|------|
| 8–9 | 🏆 Master Packaging Designer |
| 6–7 | ⭐ Skilled Designer |
| 4–5 | ✨ Emerging Designer |
| <4 | Keep Exploring |

All choices advance the game — nothing blocks progression. The goal is learning, not gotcha.

---

## Sound design

- **Background music** — Looping 8-bit chiptune track (`assets/bgm.ogg` with `assets/bgm.m4a` Safari fallback) that fades in after the title screen.
- **Click / hover** — Short beeps and chirps for UI feedback (procedural, Web Audio API)
- **Select / confirm** — Ascending triangle-wave chime when a choice is locked in (procedural)
- **Whoosh** — Filtered noise sweep during scene transitions (procedural)
- **Fanfare** — Celebratory arpeggio on the finale scene (procedural)

Press `M` or click the `🔊 SOUND` button at top-right to mute at any time.

---

## Developer / Facilitator URL parameters

For demos, training sessions, or QA, you can skip directly to any scene:

| URL | Jumps to |
|-----|----------|
| `index.html?jump=scene-title` | Title |
| `index.html?jump=scene-level1` | Level 1 (factory / tray selection) |
| `index.html?jump=scene-level2` | Level 2 (warehouse / paper selection) |
| `index.html?jump=scene-level3` | Level 3 (store / communication selection) |
| `index.html?jump=scene-finale` | Finale |

Add `?noanim` to disable CSS animations (useful for screenshots). `?jump=` implies `?noanim`.

---

## File structure

```
build-a-box/
├── index.html           # Entire game — logic, layout, styles, sound, 3D
├── README.md            # This file
├── assets/              # 2D images and audio
│   ├── bgm.ogg          # Background music (Ogg Vorbis)
│   ├── bgm.m4a          # Background music (AAC fallback for Safari)
│   ├── scene-*.jpg      # Background images
│   ├── scene-*.mp4      # Looping per-level background videos
│   ├── door-*.png       # 2D fallback portal doors
│   ├── tray-*.png       # 2D fallback trays
│   ├── paper-*.png      # 2D fallback paper rolls
│   ├── bag-monster.png  # 2D fallback Monster Snacks bag
│   └── (other 2D assets)
└── models/              # GLB 3D models
    ├── Bag_of_chip.glb           # Monster Snacks bag (used on Let's Create scene)
    ├── Pedestal.glb              # Pedestal/turntable shown under the bag
    ├── Pallet_Tray.glb           # Level 1 option 1
    ├── Single_sided_tray.glb     # Level 1 option 2
    ├── Post_Tray.glb             # Level 1 option 3 (Corner Post)
    ├── Kraft_Roll_of_Paper.glb   # Level 2 option 1
    ├── White_Roll_of_Paper.glb   # Level 2 option 2
    ├── Door1.glb, Door2.glb, Door3.glb   # Portal doors (yellow/red/green)
    └── Final_Door.glb            # Rules-scene door with built-in open animation
```

---

## 3D model rendering

The game uses Google's **`<model-viewer>`** web component (loaded once from jsDelivr CDN) to render every `.glb`. It's purpose-built for product viewers: HDRI lighting, touch-friendly orbit/pinch, lazy loading, and animation control are all built in.

**3D models in use:**
- **Rules scene:** `Final_Door.glb` — the red advance door with a built-in open animation triggered when clicked
- **Let's Create scene:** `Bag_of_chip.glb` (auto-rotating Monster Snacks bag) on `Pedestal.glb` (3D turntable)
- **Portal selection scene:** Three doors, mapped slot → GLB:
  - Slot 1 (yellow visual) → `Door3.glb`
  - Slot 2 (red visual) → `Door1.glb`
  - Slot 3 (green visual) → `Door2.glb`
  - Each door has baked open animations; the first available clip fires when the door is chosen
- **Level 1 (Factory):** `Pallet_Tray.glb`, `Single_sided_tray.glb`, `Post_Tray.glb` — all auto-rotating
- **Level 2 (Warehouse):** `Kraft_Roll_of_Paper.glb`, `White_Roll_of_Paper.glb` — both auto-rotating

**Animation control:** A small helper `playGlbOpenAnimation(mvEl)` in `index.html` reads `mvEl.availableAnimations`, sets `animationName`, and calls `mvEl.play({ repetitions: 1 })`. Used by the rules door and portal door click handlers.

**Fallback:** If a GLB fails to load (network, blocked CDN, etc.) `<model-viewer>`'s `poster` attribute keeps the 2D PNG visible — the game stays playable without 3D.

---

## Browser support

Tested design patterns work in:
- Chrome / Edge 90+
- Firefox 88+
- Safari 14+

Requirements:
- ES2020 JavaScript (supported by all major browsers from 2020 onward)
- CSS `aspect-ratio`, `clamp()`, `backdrop-filter`
- Web Audio API (standard)

No polyfills needed for any modern browser.

---

## Accessibility notes

- All interactive elements are reachable by keyboard
- Focus outlines visible on buttons and options
- `prefers-reduced-motion` honored — animations shortened for users who request it
- High-contrast yellow/cyan/white text on dark backgrounds
- ARIA labels on icon-only buttons
- Score/feedback announced via live region semantics

---

## Credits

- Original content & artwork: Smurfit Westrock Ignite — BUILD-A-BOX
- Converted to interactive web game: April 2026
- Sound effects: Web Audio API (procedural)
- Background music: 8-bit chiptune loop

---

## Questions?

The game is a single HTML file plus assets — easy to modify. Common tweaks:

- **Change the correct answer for a level:** Edit `LEVEL_DATA` in `index.html` (search for `LEVEL_DATA`). Adjust `best` and the per-option `score` values.
- **Edit option explanations:** Same `LEVEL_DATA` object — change the `reasoning` HTML string.
- **Change the client scenario:** Edit the text in `#scene-client` inside `index.html`.
- **Adjust scoring thresholds:** Edit the `rank` logic in `renderFinale()` near the bottom of the script.
