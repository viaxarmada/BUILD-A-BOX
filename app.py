# -*- coding: utf-8 -*-
"""
app.py -- player-facing BUILD-A-BOX game.

The flow is a sequence of steps defined in content/missions.json.
Each step type has a matching render function below. st.session_state
holds the current step index and the player's choices so far.
"""
from __future__ import annotations

import streamlit as st

from game_state import (
    advance,
    compute_result,
    current_step,
    go_back,
    init_game_state,
    load_content,
    record_choice,
    reset_game,
)
from ui import apply_theme, hud, render_image, render_model


# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Build-A-Box | Smurfit Westrock",
    page_icon="\U0001F4E6",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()
init_game_state()

content = load_content()


# ----------------------------------------------------------------------
# Step renderers. One function per step type in the flow.
# ----------------------------------------------------------------------
def render_title() -> None:
    meta = content["game_meta"]
    st.markdown(
        f"""
        <div class="title-pill">
          <div class="title-dots">\u2022 \u2022 \u2022 \u2022 \u2022 \u2022</div>
          <h1>{meta['title']}</h1>
        </div>
        <p style="text-align:center; opacity: 0.85; margin-top: 10px;">
          {meta['subtitle']}
        </p>
        """,
        unsafe_allow_html=True,
    )
    col_l, col_mid, col_r = st.columns([1, 1, 1])
    with col_mid:
        st.write("")
        st.write("")
        if st.button("\u25B6  START GAME", key="start_btn", use_container_width=True):
            reset_game()
            advance()
            st.rerun()


def render_intro() -> None:
    hud("LOADING")
    intro = content["intro"]
    st.markdown(
        f"""
        <div style="text-align:center; padding: 30px 40px;">
          <h1 style="color: var(--sw-primary); font-style: italic; font-size: 3rem;">
            {intro['headline']}
          </h1>
          <p style="font-size: 1.15rem; line-height: 1.6; white-space: pre-line; max-width: 900px; margin: 20px auto;">
            {intro['body']}
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _nav_buttons(show_back=False)


def render_rules() -> None:
    hud("LOADING")
    rules = content["rules"]
    col_text, col_img = st.columns([3, 2])
    with col_text:
        st.markdown(
            f"""
            <div style="padding: 20px 0;">
              <h2>{rules['headline']}</h2>
              <p style="font-size: 1.1rem; line-height: 1.7; white-space: pre-line;">
                {rules['body']}
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_img:
        if rules.get("hero_image"):
            render_image(rules["hero_image"])
    _nav_buttons()


def render_mission() -> None:
    hud("MISSION")
    mission_id = st.session_state.current_mission
    mission = content["missions"][mission_id]

    col_model, col_card = st.columns([3, 2])
    with col_model:
        # 3D product display if available, otherwise the flat product image
        if mission.get("product_model"):
            render_model(
                mission["product_model"],
                height=420,
                fallback_image=mission.get("product_image"),
            )
        elif mission.get("product_image"):
            render_image(mission["product_image"], width=380)

    with col_card:
        stars = "\u2605" * mission.get("stars", 0) + "\u2606" * (5 - mission.get("stars", 0))
        bullets = "".join(f"<li>{b}</li>" for b in mission["brief_bullets"])
        st.markdown(
            f"""
            <div class="mission-card">
              <h3>CLIENT: {mission['client']}</h3>
              <div style="color: var(--sw-primary); font-size: 1.2rem; margin: 4px 0 12px 0;">
                {stars}
              </div>
              <p>{mission['summary']}</p>
              <ul>{bullets}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    _nav_buttons()


def render_ready() -> None:
    hud("READY")
    mission = content["missions"][st.session_state.current_mission]
    col_text, col_product = st.columns([3, 2])
    with col_text:
        st.markdown(
            f"""
            <div style="padding: 40px 0;">
              <h1 style="color: var(--sw-accent); font-size: 2.6rem; line-height: 1.2;">
                {mission['call_to_action']}
              </h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_product:
        if mission.get("product_model"):
            render_model(
                mission["product_model"],
                height=380,
                fallback_image=mission.get("product_image"),
            )
    _nav_buttons(next_label="START  \u25B6")


def render_decision(decision_id: str) -> None:
    decision = content["decisions"][decision_id]
    hud(f"PORTAL {decision['portal_number']}  \u00B7  {decision['portal_label'].upper()}")

    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom: 20px;">
          <h2 style="margin: 0;">{decision['title']}</h2>
          <p style="opacity: 0.8; margin: 6px 0 0 0;">{decision['subtitle']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    options = decision["options"]
    current_choice = st.session_state.choices.get(decision_id)
    reveal = current_choice is not None  # after pick, show which was recommended

    cols = st.columns(len(options))
    for col, opt in zip(cols, options):
        with col:
            is_recommended = reveal and opt.get("is_recommended")
            klass = "option-card recommended-reveal" if is_recommended else "option-card"
            bullets = "".join(f"<li>{b}</li>" for b in opt["bullets"])
            st.markdown(
                f"""
                <div class="{klass}">
                  <div class="option-number">{opt['number']}</div>
                  <div class="option-name">{opt['name'].upper()}</div>
                  <ul>{bullets}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # 3D or image
            if opt.get("model"):
                render_model(
                    opt["model"],
                    height=280,
                    fallback_image=opt.get("image"),
                )
            elif opt.get("image"):
                render_image(opt["image"])

            pick_label = (
                f"\u2713 SELECTED" if current_choice == opt["id"] else f"PICK  #{opt['number']}"
            )
            if st.button(pick_label, key=f"{decision_id}_{opt['id']}", use_container_width=True):
                record_choice(decision_id, opt["id"])
                st.rerun()

    if reveal:
        picked = next(o for o in options if o["id"] == current_choice)
        if picked.get("is_recommended"):
            st.success(f"Great pick -- {picked['name']} fits this mission well.")
        else:
            rec = next((o for o in options if o.get("is_recommended")), None)
            if rec:
                st.info(f"Choice locked in. Heads-up: **{rec['name']}** is often the stronger fit for this brief -- you'll see why at the end.")
            else:
                st.info("Choice locked in.")

    _nav_buttons(
        next_disabled=(current_choice is None),
        next_label="NEXT PORTAL  \u25B6",
    )


def render_result() -> None:
    hud("RESULT")
    result = compute_result()
    mission = content["missions"][st.session_state.current_mission]

    st.markdown(
        f"""
        <div style="text-align:center; padding: 20px 0;">
          <h1 style="color: var(--sw-accent); font-size: 2.8rem;">
            {content['result']['headline']}
          </h1>
          <div class="tier-badge">{result['tier']['label']}</div>
          <p style="font-size: 1.1rem; margin-top: 16px;">{result['tier']['message']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_recap, col_product = st.columns([3, 2])
    with col_recap:
        st.markdown("### Your design")
        st.markdown(result["body"])
        st.markdown(f"**Score:** {result['total']} / {result['max_possible']}")

        st.markdown("#### Choices")
        for decision_id, opt in result["chosen"].items():
            decision = content["decisions"][decision_id]
            recommended = " \u2728 *recommended*" if opt.get("is_recommended") else ""
            st.markdown(
                f"- **{decision['title']}:** {opt['name']} -- {opt['score']} pts{recommended}"
            )

    with col_product:
        # Show the 3D product on the pedestal one more time
        if mission.get("product_model"):
            render_model(
                mission["product_model"],
                height=360,
                fallback_image=mission.get("product_image"),
            )

    st.write("")
    col_l, col_mid, col_r = st.columns(3)
    with col_mid:
        if st.button("\u21BA  PLAY AGAIN", key="replay", use_container_width=True):
            reset_game()
            st.rerun()


# ----------------------------------------------------------------------
# Nav bar (back / next), used by most intermediate steps.
# ----------------------------------------------------------------------
def _nav_buttons(
    *,
    show_back: bool = True,
    next_label: str = "NEXT  \u25B6",
    next_disabled: bool = False,
) -> None:
    st.write("")
    cols = st.columns([1, 1, 1])
    with cols[0]:
        if show_back and st.button("\u25C0  BACK", key=f"back_{st.session_state.step_index}"):
            go_back()
            st.rerun()
    with cols[2]:
        if st.button(
            next_label,
            key=f"next_{st.session_state.step_index}",
            disabled=next_disabled,
            use_container_width=True,
        ):
            advance()
            st.rerun()


# ----------------------------------------------------------------------
# Dispatch
# ----------------------------------------------------------------------
step = current_step()
step_type = step["type"]

if step_type == "title":
    render_title()
elif step_type == "intro":
    render_intro()
elif step_type == "rules":
    render_rules()
elif step_type == "mission":
    render_mission()
elif step_type == "ready":
    render_ready()
elif step_type == "decision":
    render_decision(step["id"])
elif step_type == "result":
    render_result()
else:
    st.error(f"Unknown step type: {step_type}")


# Small footer -- dev aid. Hide by setting show_debug to False.
with st.sidebar:
    st.caption("Admin tools are on the **Admin** page (sidebar).")
    if st.checkbox("Show debug state", value=False):
        st.json({
            "step": st.session_state.step_index,
            "step_type": step_type,
            "choices": st.session_state.choices,
        })
