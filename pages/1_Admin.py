# -*- coding: utf-8 -*-
"""
pages/1_Admin.py -- content editor.

Password-gated. Lets a game admin edit every piece of copy, swap
images, upload new .glb 3D models, and adjust scoring -- all without
touching JSON directly.

To set a password, either:
  - set env var BUILD_A_BOX_ADMIN_PASSWORD, or
  - put [admin] password = "..." in .streamlit/secrets.toml
Default for local dev is "admin".
"""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path

import streamlit as st

from game_state import (
    IMAGES_DIR,
    MODELS_DIR,
    image_path,
    list_images,
    list_models,
    load_content,
    reload_content,
    save_content,
)
from ui import apply_theme, render_image, render_model


# ----------------------------------------------------------------------
# Page setup + auth
# ----------------------------------------------------------------------
st.set_page_config(page_title="Admin \u00B7 Build-A-Box", page_icon="\U0001F527", layout="wide")
apply_theme()
st.title("\U0001F527 Build-A-Box -- Content Admin")


def _get_expected_password() -> str:
    env_pw = os.environ.get("BUILD_A_BOX_ADMIN_PASSWORD")
    if env_pw:
        return env_pw
    try:
        return st.secrets["admin"]["password"]  # type: ignore[index]
    except (KeyError, FileNotFoundError, st.errors.StreamlitAPIException):
        return "admin"


def _check_password() -> bool:
    if st.session_state.get("admin_authed"):
        return True
    expected = _get_expected_password()
    with st.form("login"):
        pw = st.text_input("Admin password", type="password")
        submitted = st.form_submit_button("Enter")
    if submitted:
        if pw == expected:
            st.session_state.admin_authed = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False


if not _check_password():
    st.stop()


# ----------------------------------------------------------------------
# Load content into a working copy so edits don't commit until save.
# ----------------------------------------------------------------------
content = load_content()
if "admin_draft" not in st.session_state:
    st.session_state.admin_draft = copy.deepcopy(content)
draft: dict = st.session_state.admin_draft


# ----------------------------------------------------------------------
# Helper widgets
# ----------------------------------------------------------------------
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(name: str) -> str:
    """Strip characters that could cause problems on disk or in URLs."""
    name = name.strip().replace(" ", "_")
    return SAFE_NAME_RE.sub("", name) or "file"


def image_picker(label: str, current: str, key: str) -> str:
    """Dropdown of available images + inline preview + upload."""
    options = [""] + list_images()
    idx = options.index(current) if current in options else 0
    chosen = st.selectbox(label, options, index=idx, key=f"img_{key}")
    if chosen:
        render_image(chosen, width=160)
    with st.expander("Upload a new image"):
        up = st.file_uploader(
            "PNG / JPG / SVG",
            type=["png", "jpg", "jpeg", "svg"],
            key=f"img_up_{key}",
        )
        if up is not None:
            target = IMAGES_DIR / _safe_filename(up.name)
            target.write_bytes(up.read())
            st.success(f"Uploaded as `{target.name}`. Select it from the dropdown above.")
            st.rerun()
    return chosen


def model_picker(label: str, current: str, key: str) -> str:
    """Dropdown of available 3D models + inline preview + upload."""
    options = [""] + list_models()
    idx = options.index(current) if current in options else 0
    chosen = st.selectbox(label, options, index=idx, key=f"mdl_{key}")
    if chosen:
        render_model(chosen, height=260)
    with st.expander("Upload a new 3D model (.glb)"):
        up = st.file_uploader("GLB only", type=["glb"], key=f"mdl_up_{key}")
        if up is not None:
            target = MODELS_DIR / _safe_filename(up.name)
            target.write_bytes(up.read())
            st.success(f"Uploaded as `{target.name}`. Select it from the dropdown above.")
            st.rerun()
    return chosen


# ----------------------------------------------------------------------
# Top-level actions -- save, reset, export, import
# ----------------------------------------------------------------------
bar_l, bar_mid, bar_r1, bar_r2 = st.columns([2, 1, 1, 1])
with bar_l:
    st.caption("Edits apply to a draft in memory. Click **Save** to commit to disk.")
with bar_mid:
    if st.button("\U0001F4BE Save", use_container_width=True):
        save_content(draft)
        st.session_state.admin_draft = copy.deepcopy(draft)
        reload_content()
        st.success("Saved.")
with bar_r1:
    if st.button("\u21BA Discard", use_container_width=True):
        st.session_state.admin_draft = copy.deepcopy(content)
        st.rerun()
with bar_r2:
    st.download_button(
        "\u2B07 Export JSON",
        data=json.dumps(draft, indent=2, ensure_ascii=False),
        file_name="missions.json",
        mime="application/json",
        use_container_width=True,
    )

# Import
uploaded_json = st.file_uploader(
    "Import JSON (replaces the current draft)", type=["json"], key="import_json"
)
if uploaded_json is not None:
    try:
        st.session_state.admin_draft = json.loads(uploaded_json.read().decode("utf-8"))
        st.success("JSON imported into draft. Review below, then click Save to commit.")
        st.rerun()
    except Exception as e:
        st.error(f"Couldn't parse JSON: {e}")


st.divider()


# ----------------------------------------------------------------------
# Tabs -- Meta / Intro & Rules / Missions / Decisions / Results / Flow
# ----------------------------------------------------------------------
tab_meta, tab_intro, tab_mission, tab_decisions, tab_result, tab_bg, tab_flow, tab_raw = st.tabs(
    ["Meta", "Intro & Rules", "Missions", "Decisions", "Result", "Backgrounds", "Flow", "Raw JSON"]
)


# ----- META ----------------------------------------------------------
with tab_meta:
    st.subheader("Game metadata")
    meta = draft["game_meta"]
    meta["title"] = st.text_input("Title", meta["title"])
    meta["subtitle"] = st.text_input("Subtitle", meta["subtitle"])
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        meta["brand_color_primary"] = st.color_picker("Primary", meta["brand_color_primary"])
    with c2:
        meta["brand_color_dark"] = st.color_picker("Dark", meta["brand_color_dark"])
    with c3:
        meta["brand_color_bg"] = st.color_picker("Background", meta["brand_color_bg"])
    with c4:
        meta["brand_color_accent"] = st.color_picker("Accent", meta["brand_color_accent"])
    meta["logo_image"] = image_picker("Logo image", meta.get("logo_image", ""), "logo")


# ----- INTRO & RULES -------------------------------------------------
with tab_intro:
    st.subheader("Intro screen")
    intro = draft["intro"]
    intro["headline"] = st.text_input("Intro headline", intro["headline"], key="intro_h")
    intro["body"] = st.text_area("Intro body", intro["body"], height=180, key="intro_b")

    st.subheader("Rules screen")
    rules = draft["rules"]
    rules["headline"] = st.text_input("Rules headline", rules["headline"], key="rules_h")
    rules["body"] = st.text_area("Rules body", rules["body"], height=180, key="rules_b")
    rules["hero_image"] = image_picker("Rules hero image", rules.get("hero_image", ""), "rules_hero")


# ----- MISSIONS ------------------------------------------------------
with tab_mission:
    mission_ids = list(draft["missions"].keys())
    selected_mission = st.selectbox("Edit mission", mission_ids, key="mission_sel")
    mission = draft["missions"][selected_mission]

    c1, c2 = st.columns(2)
    with c1:
        mission["client"] = st.text_input("Client name", mission["client"])
        mission["stars"] = st.slider("Difficulty stars (0-5)", 0, 5, int(mission.get("stars", 3)))
        mission["summary"] = st.text_area("Summary", mission["summary"], height=100)
        mission["call_to_action"] = st.text_area(
            "Call to action (Ready screen)", mission["call_to_action"], height=80
        )

    with c2:
        mission["logo_image"] = image_picker(
            "Client logo image", mission.get("logo_image", ""), "m_logo"
        )
        mission["product_image"] = image_picker(
            "Product hero image (fallback if no 3D)",
            mission.get("product_image", ""),
            "m_prod_img",
        )
        mission["product_model"] = model_picker(
            "Product 3D model (.glb)", mission.get("product_model", ""), "m_prod_mdl"
        )

    st.markdown("**Brief bullets** -- one per line.")
    bullets_text = st.text_area(
        "Bullets",
        "\n".join(mission["brief_bullets"]),
        height=120,
        key="m_bullets",
    )
    mission["brief_bullets"] = [b.strip() for b in bullets_text.splitlines() if b.strip()]


# ----- DECISIONS -----------------------------------------------------
with tab_decisions:
    decision_ids = list(draft["decisions"].keys())
    selected_decision = st.selectbox("Edit decision", decision_ids, key="decision_sel")
    decision = draft["decisions"][selected_decision]

    c1, c2, c3 = st.columns(3)
    with c1:
        decision["portal_label"] = st.text_input("Portal label", decision["portal_label"])
    with c2:
        decision["portal_number"] = st.number_input(
            "Portal number", 1, 20, int(decision["portal_number"])
        )
    with c3:
        decision["background_image"] = image_picker(
            "Background image", decision.get("background_image", ""), f"dec_bg_{selected_decision}"
        )

    decision["title"] = st.text_input("Decision title", decision["title"], key="d_title")
    decision["subtitle"] = st.text_input("Decision subtitle", decision["subtitle"], key="d_sub")

    st.markdown("### Options")
    for i, opt in enumerate(decision["options"]):
        with st.expander(f"#{opt.get('number', i+1)} -- {opt['name']}", expanded=False):
            c1, c2 = st.columns([1, 1])
            with c1:
                opt["number"] = st.number_input(
                    "Display number", 1, 9, int(opt.get("number", i + 1)),
                    key=f"opt_num_{selected_decision}_{i}",
                )
                opt["name"] = st.text_input(
                    "Name", opt["name"], key=f"opt_name_{selected_decision}_{i}"
                )
                bullets_text = st.text_area(
                    "Bullets (one per line)",
                    "\n".join(opt["bullets"]),
                    height=120,
                    key=f"opt_bul_{selected_decision}_{i}",
                )
                opt["bullets"] = [b.strip() for b in bullets_text.splitlines() if b.strip()]
                opt["score"] = st.slider(
                    "Score (higher = better fit for mission)",
                    0, 5, int(opt.get("score", 0)),
                    key=f"opt_score_{selected_decision}_{i}",
                )
                opt["is_recommended"] = st.checkbox(
                    "Mark as the recommended option",
                    value=bool(opt.get("is_recommended")),
                    key=f"opt_rec_{selected_decision}_{i}",
                )
            with c2:
                opt["image"] = image_picker(
                    "Option image",
                    opt.get("image", ""),
                    f"opt_img_{selected_decision}_{i}",
                )
                opt["model"] = model_picker(
                    "Option 3D model",
                    opt.get("model", ""),
                    f"opt_mdl_{selected_decision}_{i}",
                )
            remove_col, move_up, move_down = st.columns(3)
            with remove_col:
                if st.button("\U0001F5D1 Remove option", key=f"opt_rm_{selected_decision}_{i}"):
                    decision["options"].pop(i)
                    st.rerun()
            with move_up:
                if i > 0 and st.button("\u25B2 Move up", key=f"opt_up_{selected_decision}_{i}"):
                    decision["options"][i - 1], decision["options"][i] = (
                        decision["options"][i], decision["options"][i - 1]
                    )
                    st.rerun()
            with move_down:
                if i < len(decision["options"]) - 1 and st.button(
                    "\u25BC Move down", key=f"opt_dn_{selected_decision}_{i}"
                ):
                    decision["options"][i + 1], decision["options"][i] = (
                        decision["options"][i], decision["options"][i + 1]
                    )
                    st.rerun()

    if st.button("\u2795 Add new option", key=f"add_opt_{selected_decision}"):
        decision["options"].append({
            "id": f"option_{len(decision['options']) + 1}",
            "number": len(decision["options"]) + 1,
            "name": "New option",
            "model": "",
            "image": "",
            "bullets": ["Pro point one.", "Trade-off point."],
            "score": 1,
            "is_recommended": False,
        })
        st.rerun()


# ----- RESULT --------------------------------------------------------
with tab_result:
    st.subheader("Result screen")
    result = draft["result"]
    result["headline"] = st.text_input("Result headline", result["headline"])
    result["body_template"] = st.text_area(
        "Body template -- use {tray_name}, {paper_name}, {graphic_name} placeholders.",
        result["body_template"],
        height=100,
    )
    st.markdown("**Score tiers** -- label + message shown for ranges of total score.")
    for i, tier in enumerate(result["score_tiers"]):
        c1, c2, c3, c4 = st.columns([1, 1, 2, 3])
        with c1:
            tier["min"] = st.number_input("Min", 0, 100, int(tier["min"]), key=f"t_min_{i}")
        with c2:
            tier["max"] = st.number_input("Max", 0, 100, int(tier["max"]), key=f"t_max_{i}")
        with c3:
            tier["label"] = st.text_input("Label", tier["label"], key=f"t_lab_{i}")
        with c4:
            tier["message"] = st.text_input("Message", tier["message"], key=f"t_msg_{i}")


# ----- BACKGROUNDS ---------------------------------------------------
with tab_bg:
    st.subheader("Slide backgrounds")
    st.caption(
        "Pick or upload a background image for each slide. Images are "
        "dimmed slightly by the player for text readability. Leave a "
        "slide empty to fall back to the **Default background** (below), "
        "or to the arcade gradient if no default is set."
    )

    # Ensure the schema fields exist
    draft.setdefault("backgrounds", {})
    meta = draft["game_meta"]
    meta["default_background"] = image_picker(
        "Default background (applied when a slide has none)",
        meta.get("default_background", ""),
        "bg_default",
    )

    st.divider()
    st.markdown("##### Per-slide backgrounds")

    # Human-readable labels for each step id
    def _label_for(step_id: str) -> str:
        for s in draft.get("flow", []):
            if s["id"] == step_id:
                return f"{s['type'].title()} \u2014 `{step_id}`"
        return step_id

    # One picker per flow step
    seen = set()
    for step in draft.get("flow", []):
        sid = step["id"]
        if sid in seen:
            continue
        seen.add(sid)
        draft["backgrounds"].setdefault(sid, "")
        with st.expander(_label_for(sid), expanded=False):
            draft["backgrounds"][sid] = image_picker(
                "Background",
                draft["backgrounds"][sid],
                f"bg_{sid}",
            )



    st.subheader("Flow sequence")
    st.caption(
        "Drag-free reorder: use the up/down arrows. Each entry must have a valid "
        "`id` that matches something in intro / rules / missions / decisions / result."
    )
    flow = draft["flow"]
    for i, step in enumerate(flow):
        c1, c2, c3, c4, c5 = st.columns([2, 3, 1, 1, 1])
        with c1:
            step["type"] = st.selectbox(
                "Type", ["title", "intro", "rules", "mission", "ready", "decision", "result"],
                index=["title", "intro", "rules", "mission", "ready", "decision", "result"].index(step["type"]),
                key=f"flow_type_{i}",
            )
        with c2:
            step["id"] = st.text_input("ID", step["id"], key=f"flow_id_{i}")
        with c3:
            if i > 0 and st.button("\u25B2", key=f"flow_up_{i}"):
                flow[i - 1], flow[i] = flow[i], flow[i - 1]
                st.rerun()
        with c4:
            if i < len(flow) - 1 and st.button("\u25BC", key=f"flow_dn_{i}"):
                flow[i + 1], flow[i] = flow[i], flow[i + 1]
                st.rerun()
        with c5:
            if st.button("\U0001F5D1", key=f"flow_rm_{i}"):
                flow.pop(i)
                st.rerun()

    if st.button("\u2795 Add step"):
        flow.append({"type": "decision", "id": ""})
        st.rerun()


# ----- RAW JSON ------------------------------------------------------
with tab_raw:
    st.caption("Read-only view. Use Export/Import above for round-trips.")
    st.json(draft)
