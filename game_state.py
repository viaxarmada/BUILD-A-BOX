# -*- coding: utf-8 -*-
"""
game_state.py -- state machine + content loading for BUILD-A-BOX.
Everything game-related that isn't UI lives here so the admin page
and the player page can both import it without duplication.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import streamlit as st

# ----------------------------------------------------------------------
# Paths -- resolved from this file so it doesn't matter where Streamlit
# is launched from.
# ----------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
CONTENT_PATH = ROOT / "content" / "missions.json"
IMAGES_DIR = ROOT / "assets" / "images"
MODELS_DIR = ROOT / "assets" / "models"


# ----------------------------------------------------------------------
# Content loading / saving
# ----------------------------------------------------------------------
def load_content() -> dict[str, Any]:
    """Load the game JSON. Cached in session_state so admin edits apply
    immediately without needing to restart the app."""
    if "content" not in st.session_state:
        with CONTENT_PATH.open("r", encoding="utf-8") as f:
            st.session_state.content = json.load(f)
    return st.session_state.content


def save_content(content: dict[str, Any]) -> None:
    """Persist edits back to disk and refresh the cached copy."""
    with CONTENT_PATH.open("w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    st.session_state.content = content


def reload_content() -> dict[str, Any]:
    """Force a re-read from disk."""
    st.session_state.pop("content", None)
    return load_content()


# ----------------------------------------------------------------------
# Asset discovery -- used by admin dropdowns
# ----------------------------------------------------------------------
def list_images() -> list[str]:
    if not IMAGES_DIR.exists():
        return []
    return sorted([p.name for p in IMAGES_DIR.iterdir() if p.is_file()])


def list_models() -> list[str]:
    if not MODELS_DIR.exists():
        return []
    return sorted([p.name for p in MODELS_DIR.iterdir() if p.suffix.lower() == ".glb"])


def image_path(name: str) -> Path | None:
    if not name:
        return None
    p = IMAGES_DIR / name
    return p if p.exists() else None


def model_path(name: str) -> Path | None:
    if not name:
        return None
    p = MODELS_DIR / name
    return p if p.exists() else None


def asset_as_data_uri(path: Path) -> str:
    """Turn a local file into a data: URI so it can be embedded
    inside an <model-viewer> inside st.components.v1.html without
    worrying about Streamlit's static file serving quirks."""
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".glb": "model/gltf-binary",
    }.get(path.suffix.lower(), "application/octet-stream")
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ----------------------------------------------------------------------
# Game state machine
# ----------------------------------------------------------------------
def init_game_state() -> None:
    if "step_index" not in st.session_state:
        st.session_state.step_index = 0
    if "choices" not in st.session_state:
        st.session_state.choices = {}
    if "current_mission" not in st.session_state:
        st.session_state.current_mission = "mission_monster_snacks"


def reset_game() -> None:
    st.session_state.step_index = 0
    st.session_state.choices = {}


def advance() -> None:
    flow = load_content()["flow"]
    if st.session_state.step_index < len(flow) - 1:
        st.session_state.step_index += 1


def go_back() -> None:
    if st.session_state.step_index > 0:
        st.session_state.step_index -= 1


def record_choice(decision_id: str, option_id: str) -> None:
    st.session_state.choices[decision_id] = option_id


def current_step() -> dict[str, Any]:
    flow = load_content()["flow"]
    idx = min(st.session_state.step_index, len(flow) - 1)
    return flow[idx]


def progress_fraction() -> float:
    flow = load_content()["flow"]
    if not flow:
        return 0.0
    return (st.session_state.step_index + 1) / len(flow)


# ----------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------
def compute_result() -> dict[str, Any]:
    content = load_content()
    choices = st.session_state.choices
    total = 0
    chosen_options: dict[str, dict[str, Any]] = {}
    for decision_id, decision in content["decisions"].items():
        chosen_id = choices.get(decision_id)
        if chosen_id is None:
            continue
        for opt in decision["options"]:
            if opt["id"] == chosen_id:
                total += int(opt.get("score", 0))
                chosen_options[decision_id] = opt
                break

    tier = {"label": "--", "message": ""}
    for t in content["result"]["score_tiers"]:
        if t["min"] <= total <= t["max"]:
            tier = t
            break

    def name_for(did: str) -> str:
        opt = chosen_options.get(did)
        return opt["name"] if opt else "--"

    body = content["result"]["body_template"].format(
        tray_name=name_for("tray_type"),
        paper_name=name_for("paper_type"),
        graphic_name=name_for("graphic_element"),
    )

    return {
        "total": total,
        "max_possible": sum(
            max((o["score"] for o in d["options"]), default=0)
            for d in content["decisions"].values()
        ),
        "tier": tier,
        "body": body,
        "chosen": chosen_options,
    }
