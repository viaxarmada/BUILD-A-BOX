# Build-A-Box — online edition

Streamlit port of the Smurfit Westrock **BUILD-A-BOX** PowerPoint game. Players walk through three packaging-design portals, pick options, and get a scored result. 3D models (`.glb`) from the original deck render live in the browser via Google's `<model-viewer>` web component.

The app ships with a password-gated **Admin** page that lets a non-developer edit every piece of copy, swap images, upload new 3D models, reorder options, and tune the scoring — no JSON editing required.

---

## Project layout

```
build_a_box/
├── app.py                    # Player-facing game
├── pages/
│   └── 1_Admin.py            # Content editor (password-gated)
├── game_state.py             # State machine + asset helpers
├── ui.py                     # Theme CSS + model-viewer wrapper
├── content/
│   └── missions.json         # Single source of truth for the game
├── assets/
│   ├── images/               # PNGs / JPEGs / SVGs (extracted from the .pptx)
│   └── models/               # GLB 3D models (extracted from the .pptx)
├── .streamlit/
│   ├── config.toml           # Dark arcade theme
│   └── secrets.toml.example  # Copy → secrets.toml, set admin password
├── requirements.txt
└── README.md
```

---

## Run locally

```bash
cd build_a_box
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. The **Admin** page is in the sidebar. Default password is `admin` — change it via either `BUILD_A_BOX_ADMIN_PASSWORD` env var or `.streamlit/secrets.toml` before deploying.

---

## Deploy to Streamlit Community Cloud

1. Push the whole `build_a_box/` folder to a GitHub repo (private is fine).
2. On [share.streamlit.io](https://share.streamlit.io), pick the repo and set the main file to `app.py`.
3. In **Settings → Secrets**, paste:
   ```toml
   [admin]
   password = "your-real-password-here"
   ```
4. Deploy.

The `.glb` and image assets live in the repo alongside the code, so no external storage is needed for the starter deck.

---

## Editing the game (no code)

1. Open the deployed app, navigate to the **Admin** page, sign in.
2. Pick the tab for the thing you want to change:
   - **Meta** — title, brand colors
   - **Intro & Rules** — the two onboarding screens
   - **Missions** — client name, brief, hero 3D model
   - **Decisions** — each portal's title and its options. Every option has: display number, name, bullets, score, recommended flag, image, 3D model. You can add/remove/reorder options.
   - **Result** — result copy and score tiers
   - **Flow** — the sequence of steps players walk through
   - **Raw JSON** — export or reimport the whole config
3. Click **Save** at the top to commit edits to `content/missions.json`.

### Uploading a new 3D model

On any option row in the **Decisions** tab, expand **Upload a new 3D model (.glb)** and pick a file. It's saved to `assets/models/` and appears in the dropdown. Export GLBs from Blender, SketchUp, Rhino, or whatever your team uses — any GLTF 2.0 binary.

> Heads-up for Streamlit Community Cloud: the app's filesystem is **ephemeral**. Anything uploaded via the admin page survives until the container is recycled. For durable edits, either (a) download the JSON via **Export**, upload new assets to the repo, and redeploy, or (b) plug in cloud storage (S3 / GCS / Supabase) — see *Next steps* below.

---

## How the code fits together

- `content/missions.json` — the entire game as data. The app renders whatever is in this file.
- `game_state.py` — loads that JSON into `st.session_state`, exposes the state machine (`advance`, `go_back`, `record_choice`, `compute_result`), and resolves asset paths.
- `ui.py` — CSS theme plus two rendering helpers: `render_image` and `render_model`. The model helper embeds `<model-viewer>` from a CDN and inlines the GLB as a data URI so Streamlit's static serving isn't in the loop.
- `app.py` — player experience. Dispatches on the current step's type (`title`, `intro`, `rules`, `mission`, `ready`, `decision`, `result`) to a matching render function.
- `pages/1_Admin.py` — thin UI over the same JSON structure. Every widget is bound to a key in the draft dict; **Save** writes the draft back to disk.

---

## Known trade-offs vs. the original PowerPoint

| Feature | PPTX | This version |
|---|---|---|
| 3D models rotating on pedestals | Yes (native) | Yes (`<model-viewer>`) |
| Portal/door light-up animation | Yes (PPT entrance effects) | Replaced by a "reveal recommended" visual hint after choice |
| Keyboard 1/2/3 to pick | Custom VBA | Click buttons (can add keyboard via `streamlit-shortcuts` if needed) |
| Character/scene backgrounds | Painted illustrations | Extracted as images and usable via background_image field |
| Offline playback | Yes | No (needs browser + network for `<model-viewer>` CDN) |

---

## Next steps (if you want to go further)

- **Persistent cloud storage** for admin edits: swap `save_content()` / uploads to write to Supabase Storage or S3 instead of the local filesystem.
- **Multiple missions**: the data model already supports them — add mission records to `missions.json`, and add a mission picker to the title screen.
- **Leaderboards / player analytics**: add a lightweight backend (Supabase or Firestore). Log `choices` + `total score` at the result step.
- **Keyboard shortcuts**: install `streamlit-shortcuts` and wire 1/2/3 to the option buttons on decision steps.
- **Better 3D staging**: the `<model-viewer>` wrapper in `ui.py` accepts props — drop in environment HDRIs, shadows, or exposure tweaks per model without touching app code.

---

## The Reveal.js player (recommended for audiences)

`index.html`, `game.js`, `game.css`, and `.nojekyll` together form a static, browser-based version of the same game. It reads the same `content/missions.json` the Streamlit admin edits. This version has real slide transitions, 3D models rotating on pedestals, keyboard-driven option picking (1/2/3), fullscreen support, and none of Streamlit's re-run-the-script interaction overhead.

### Deploy to GitHub Pages

1. Make sure the whole folder (including `index.html` and the `.nojekyll` file) is pushed to a GitHub repo.
2. Repo → **Settings → Pages → Build and deployment**.
3. Source: **Deploy from a branch**. Branch: **main**, folder: **/ (root)**. Save.
4. Wait ~60 seconds. The game lives at `https://YOUR-USERNAME.github.io/REPO-NAME/`.

That's it. No build step, no secrets, no config. GitHub serves the HTML, the browser fetches `missions.json` + images + GLBs over HTTPS, and Reveal.js + `<model-viewer>` come from the jsdelivr CDN.

### Local preview

The files need to be served over HTTP (not opened as `file://`) because the game fetches JSON at runtime:

```bash
cd build_a_box
python3 -m http.server 8000
# open http://localhost:8000
```

### Keyboard shortcuts

| Key | Action |
|---|---|
| → / Space / N | Next slide or next fragment |
| ← / P | Previous |
| 1 / 2 / 3 | Pick option on a decision slide |
| F | Fullscreen |
| R | Restart game |
| Esc | Overview / exit fullscreen |
| ? button (top right) | Show shortcuts help |

### Sync between admin (Streamlit) and player (GitHub Pages)

The two apps read the same `content/missions.json`, but **they read it from different places**: the Streamlit admin reads/writes the file on its own (ephemeral) container filesystem, while the GitHub Pages player reads from the repo. So admin edits on Streamlit Cloud do NOT automatically appear on Pages.

For now, the workflow for permanent content changes is:

1. Make edits in the Streamlit admin.
2. Click **Export JSON** to download the updated `missions.json`.
3. Commit the updated file to the GitHub repo (replace `content/missions.json`).
4. GitHub Pages auto-rebuilds within a minute; players see the new version.

If this becomes painful, the proper fix is swapping `save_content()` in `game_state.py` to commit via the GitHub API (requires a PAT in Streamlit Cloud's Secrets). Happy to build that if you want it.

### What might go wrong on first deploy

- **Page is blank, console shows 404 on `missions.json`**: the `.nojekyll` file is missing or wasn't pushed. Without it, GitHub Pages runs Jekyll, which mangles some paths. Re-check the repo has `.nojekyll` at the root.
- **3D models don't show, only flat boxes**: the `.glb` files didn't upload. Check `assets/models/` in the repo has all 11 `.glb` files.
- **Page loads but the boot "Loading game content..." never goes away**: open DevTools → Console. Usually a fetch error for `missions.json` (check the file exists at `content/missions.json`) or a CSP blocking the CDN.
- **Models show, but they're the wrong ones for each option**: the starter mapping in `missions.json` is a best guess. Open the Streamlit admin's **Decisions** tab, pick the right GLB for each option from the dropdown (each has a live preview), export, recommit.

### Browser support

Tested on Chromium (Chrome, Edge, Brave). Firefox 98+ and Safari 15.4+ also support `<model-viewer>` and ES modules natively. IE is not supported (neither is Reveal.js 5.x).

### v2 player improvements (April 2026)

**Auto-animate text**
Slides now animate their content in automatically — no need to click or press Arrow-right to reveal bullet points. Elements fade in with a staggered delay (about 0.15–0.2s per item). Navigate away and back to see the animation replay.

**Backgrounds**
Each slide can have its own background image. Edit them from the **Admin → Backgrounds** tab. If a slide has no background set, it falls back to the **Default background** (also in that tab), or to the arcade gradient if no default is set either. Backgrounds are automatically dimmed by a subtle overlay so text stays legible on busy images.

**Fullscreen + responsive scaling**
The canvas is now 1920×1080 (16:9). Reveal.js scales that canvas proportionally to whatever viewport the player is on — full-size on a 1920×1080 monitor, scaled-up on 4K, scaled-down on mobile. Click the ⛶ button in the top-right HUD (or press F) to go true fullscreen.

**Admin: uploading backgrounds**
Go to Admin → Backgrounds. Either pick an existing image from the dropdown, or use the "Upload a new image" expander to add one. Save the JSON, export it, commit to the repo. The Reveal.js player picks it up on the next page load.
