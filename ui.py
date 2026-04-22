# -*- coding: utf-8 -*-
"""
ui.py -- reusable UI building blocks: arcade-style CSS theme,
the <model-viewer> wrapper, and small widgets like the HUD bar.
"""
from __future__ import annotations

import streamlit as st

from game_state import (
    asset_as_data_uri,
    image_path,
    load_content,
    model_path,
    progress_fraction,
)


# ----------------------------------------------------------------------
# Theme -- injected once per page. Call `apply_theme()` at the top of
# each Streamlit page that wants the arcade look.
# ----------------------------------------------------------------------
def apply_theme() -> None:
    content = load_content()
    meta = content["game_meta"]
    css = f"""
    <style>
    :root {{
      --sw-primary: {meta['brand_color_primary']};
      --sw-dark: {meta['brand_color_dark']};
      --sw-bg: {meta['brand_color_bg']};
      --sw-accent: {meta['brand_color_accent']};
    }}
    .stApp {{
      background: radial-gradient(
        ellipse at top,
        #1a3a7a 0%,
        var(--sw-bg) 45%,
        var(--sw-dark) 100%
      );
      color: #fff;
    }}
    .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}
    h1, h2, h3, h4 {{ color: #fff; letter-spacing: 0.5px; }}

    /* Arcade HUD -- the black rounded pill at the top of each slide */
    .hud-bar {{
      background: #000;
      border: 2px solid var(--sw-primary);
      border-radius: 40px;
      padding: 12px 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 24px rgba(0, 191, 255, 0.45);
      margin: 0 auto 24px auto;
      max-width: 680px;
    }}
    .hud-bar h2 {{
      margin: 0;
      font-weight: 800;
      letter-spacing: 3px;
      font-size: 1.6rem;
    }}
    .hud-dots {{ margin-left: 14px; color: var(--sw-primary); letter-spacing: 3px; }}

    /* Title-slide treatment */
    .title-pill {{
      background: #000;
      border: 3px solid var(--sw-primary);
      border-radius: 80px;
      padding: 30px 60px;
      text-align: center;
      box-shadow: 0 0 40px rgba(0, 191, 255, 0.6);
      margin: 60px auto 30px auto;
      max-width: 720px;
    }}
    .title-pill h1 {{
      font-size: 4rem;
      font-weight: 900;
      letter-spacing: 5px;
      margin: 0;
    }}
    .title-dots {{ margin-bottom: 10px; font-size: 1.4rem; letter-spacing: 10px; }}

    /* Option card used for each decision choice */
    .option-card {{
      background: rgba(0, 0, 0, 0.45);
      border: 2px solid rgba(0, 191, 255, 0.4);
      border-radius: 16px;
      padding: 16px;
      margin-bottom: 10px;
      min-height: 200px;
      transition: all 160ms ease;
    }}
    .option-card:hover {{
      border-color: var(--sw-primary);
      box-shadow: 0 0 20px rgba(0, 191, 255, 0.5);
      transform: translateY(-2px);
    }}
    .option-card.recommended-reveal {{
      border-color: #40E0D0;
      box-shadow: 0 0 22px rgba(64, 224, 208, 0.6);
    }}
    .option-number {{
      display: inline-block;
      background: var(--sw-accent);
      color: #000;
      width: 36px; height: 36px;
      border-radius: 50%;
      text-align: center;
      line-height: 36px;
      font-weight: 900;
      margin-bottom: 6px;
    }}
    .option-name {{ color: var(--sw-primary); font-weight: 800; letter-spacing: 1px; }}
    .option-card ul {{ margin: 6px 0 0 18px; padding: 0; }}
    .option-card li {{ margin-bottom: 4px; font-size: 0.92rem; }}

    /* Mission client-card (the tilted-paper look from the deck) */
    .mission-card {{
      background: #fafafa;
      color: #1a1a1a;
      padding: 24px;
      border-radius: 6px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      transform: rotate(-1deg);
    }}
    .mission-card h3 {{ color: #1a1a1a; margin-top: 0; }}

    /* Result screen -- the tier badge */
    .tier-badge {{
      background: var(--sw-accent);
      color: #000;
      padding: 8px 20px;
      border-radius: 20px;
      display: inline-block;
      font-weight: 800;
      letter-spacing: 1px;
    }}

    /* Primary CTA buttons -- Streamlit's default button, restyled */
    .stButton > button {{
      background: var(--sw-primary);
      color: #000;
      border: none;
      border-radius: 24px;
      padding: 10px 28px;
      font-weight: 800;
      letter-spacing: 1px;
      box-shadow: 0 4px 18px rgba(0, 191, 255, 0.4);
      transition: transform 120ms ease;
    }}
    .stButton > button:hover {{
      transform: scale(1.03);
      background: #7EDBF5;
      color: #000;
    }}

    /* Progress line (thin, under HUD) */
    .progress-rail {{
      width: 100%;
      height: 4px;
      background: rgba(255,255,255,0.12);
      border-radius: 2px;
      overflow: hidden;
      margin: -14px auto 20px auto;
      max-width: 680px;
    }}
    .progress-rail > div {{
      height: 100%;
      background: var(--sw-primary);
      transition: width 300ms ease;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# HUD (the black rounded bar with the status label)
# ----------------------------------------------------------------------
def hud(label: str) -> None:
    st.markdown(
        f"""
        <div class="hud-bar">
          <h2>{label}</h2>
          <span class="hud-dots">\u2022 \u2022 \u2022 \u2022</span>
        </div>
        <div class="progress-rail"><div style="width: {progress_fraction()*100:.0f}%"></div></div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Image rendering -- `st.image` wants a local path or bytes. We use
# bytes because we also want to support images that may have been
# uploaded via the admin page into new files.
# ----------------------------------------------------------------------
def render_image(name: str, *, width: int | None = None, caption: str | None = None) -> None:
    p = image_path(name)
    if p is None:
        st.info(f"(image `{name}` not found)")
        return
    # Streamlit >=1.30 rejects width=None; use "stretch" to fill the column.
    st.image(str(p), width=width if width is not None else "stretch", caption=caption)


# ----------------------------------------------------------------------
# 3D model viewer -- embeds Google's <model-viewer> web component.
# We inline the .glb as a data URI so there's no separate static
# file server plumbing to set up on Streamlit Community Cloud.
# ----------------------------------------------------------------------
MODEL_VIEWER_CDN = "https://cdn.jsdelivr.net/npm/@google/model-viewer/dist/model-viewer.min.js"


def render_model(
    model_name: str,
    *,
    height: int = 360,
    bg: str = "transparent",
    auto_rotate: bool = True,
    camera_controls: bool = True,
    fallback_image: str | None = None,
) -> None:
    """Render a .glb file inline. Falls back to an image if the model
    is missing -- useful both when an admin hasn't picked a model yet
    and when running in environments that block the CDN."""
    p = model_path(model_name) if model_name else None
    if p is None:
        if fallback_image:
            render_image(fallback_image, width=300)
        else:
            st.info(f"(3D model `{model_name}` not found -- upload one in the admin page)")
        return

    data_uri = asset_as_data_uri(p)
    auto_rotate_attr = "auto-rotate" if auto_rotate else ""
    camera_controls_attr = "camera-controls" if camera_controls else ""

    html = f"""
    <script type="module" src="{MODEL_VIEWER_CDN}"></script>
    <model-viewer
        src="{data_uri}"
        alt="3D model"
        {auto_rotate_attr}
        {camera_controls_attr}
        auto-rotate-delay="0"
        rotation-per-second="25deg"
        exposure="1"
        shadow-intensity="0.8"
        style="width: 100%; height: {height}px; background: {bg};">
    </model-viewer>
    """
    # `unsafe_allow_javascript` is required for the <model-viewer>
    # custom element to register and render the GLB.
    st.html(html, unsafe_allow_javascript=True)
