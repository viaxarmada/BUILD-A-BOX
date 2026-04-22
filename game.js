/* ================================================================
   BUILD-A-BOX — game.js  (clean v3)
   Reads content/missions.json, builds the Reveal.js deck on the
   fly, manages player state, wires up keyboard shortcuts, and
   computes the final score.
   ================================================================ */

import Reveal from 'https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.esm.js';

let deck = null;

// ---- Paths -------------------------------------------------------
const CONTENT_URL  = './content/missions.json';
const IMAGES_BASE  = './assets/images/';
const MODELS_BASE  = './assets/models/';

// ---- State -------------------------------------------------------
const STATE_KEY = 'babx.state';
const state = { choices: {} };
loadState();

function loadState() {
  try {
    const raw = sessionStorage.getItem(STATE_KEY);
    if (raw) Object.assign(state, JSON.parse(raw));
  } catch (e) { /* ignore */ }
}
function saveState() {
  try { sessionStorage.setItem(STATE_KEY, JSON.stringify(state)); }
  catch (e) { /* ignore */ }
}
function resetState() { state.choices = {}; saveState(); }

// ---- HTML helpers -----------------------------------------------
function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
function imgSrc(name)   { return name ? IMAGES_BASE + encodeURIComponent(name) : ''; }
function modelSrc(name) { return name ? MODELS_BASE + encodeURIComponent(name) : ''; }

function renderModel(modelName, fallbackImage, opts = {}) {
  const cls = opts.small ? 'product-model product-model-small' : 'product-model';
  if (modelName) {
    return `<model-viewer
        src="${esc(modelSrc(modelName))}"
        alt="3D model"
        auto-rotate
        camera-controls
        rotation-per-second="25deg"
        exposure="1"
        shadow-intensity="0.8"
        reveal="auto"
        loading="lazy"
        class="${cls}"></model-viewer>`;
  }
  if (fallbackImage) {
    return `<img src="${esc(imgSrc(fallbackImage))}" alt="" class="${cls}" style="object-fit:contain;">`;
  }
  return `<div class="${cls}" style="border:1.5px dashed rgba(255,255,255,0.2);border-radius:10px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.4);font-size:0.85rem;">no 3D model set</div>`;
}

function renderStars(n) {
  return '&#9733;'.repeat(n) + '&#9734;'.repeat(Math.max(0, 5 - n));
}

// ---- Slide builders ---------------------------------------------
function slideTitle(content) {
  const meta = content.game_meta;
  return `
    <div class="title-layout">
      <div class="title-top auto-in" style="--delay:0.15s">
        <div class="title-pill">
          <div class="title-dots">&bull; &bull; &bull; &bull; &bull; &bull;</div>
          <h1>${esc(meta.title)}</h1>
        </div>
        <p class="title-subtitle auto-in" style="--delay:0.6s">${esc(meta.subtitle)}</p>
        <div class="btn-row auto-in" style="--delay:1.0s">
          <button class="primary-btn" data-action="start">&#9654; Start Game</button>
        </div>
      </div>
      <div class="title-bottom auto-in" style="--delay:1.4s">
        <div class="portal-preview">
          <div class="portal-pip"><span class="portal-num">1</span><span class="portal-lbl">Tray Style</span></div>
          <div class="portal-pip"><span class="portal-num">2</span><span class="portal-lbl">Paper Type</span></div>
          <div class="portal-pip"><span class="portal-num">3</span><span class="portal-lbl">Graphic</span></div>
        </div>
        <p class="title-tagline">3 portals. 1 perfect box.</p>
      </div>
    </div>
  `;
}

function slideIntro(content) {
  const intro = content.intro;
  const paragraphs = intro.body
    .split('\n\n')
    .map((p, i) => `<p class="auto-in" style="--delay:${0.15 + i * 0.18}s">${esc(p).replace(/\n/g, '<br>')}</p>`)
    .join('');
  return `
    <div class="hud-bar"><h2>LOADING</h2><span class="hud-dots">&bull; &bull; &bull; &bull;</span></div>
    <h1 class="intro-headline auto-in" style="--delay:0.1s">${esc(intro.headline)}</h1>
    <div class="intro-body">${paragraphs}</div>
    <p class="pick-prompt auto-in" style="--delay:1.2s;margin-top:40px;">
      Press <kbd>&rarr;</kbd> or <kbd>Space</kbd> to continue
    </p>
  `;
}

function slideRules(content) {
  const rules = content.rules;
  const paragraphs = rules.body
    .split('\n\n')
    .map((p, i) => `<p class="auto-in" style="--delay:${0.3 + i * 0.2}s">${esc(p).replace(/\n/g, '<br>')}</p>`)
    .join('');
  return `
    <div class="hud-bar"><h2>LOADING</h2><span class="hud-dots">&bull; &bull; &bull; &bull;</span></div>
    <div class="content-grid">
      <div>
        <h2 class="auto-in" style="--delay:0.1s">${esc(rules.headline)}</h2>
        ${paragraphs}
      </div>
      <div class="auto-in" style="--delay:0.4s">
        ${rules.hero_image ? `<img src="${esc(imgSrc(rules.hero_image))}" alt="" style="max-width:100%;border-radius:12px;">` : ''}
      </div>
    </div>
  `;
}

function slideMission(content, missionId) {
  const m = content.missions[missionId];
  const bullets = m.brief_bullets.map((b, i) => `<li class="auto-in" style="--delay:${0.6 + i * 0.2}s">${esc(b)}</li>`).join('');
  return `
    <div class="hud-bar"><h2>MISSION</h2><span class="hud-dots">&bull; &bull; &bull; &bull;</span></div>
    <div class="content-grid">
      <div class="pedestal-scene auto-in" style="--delay:0.1s">
        ${renderModel(m.product_model, m.product_image)}
      </div>
      <div class="mission-card auto-in" style="--delay:0.3s">
        <h3>CLIENT: ${esc(m.client)}</h3>
        <div class="mission-stars">${renderStars(m.stars || 0)}</div>
        <p>${esc(m.summary)}</p>
        <ul>${bullets}</ul>
      </div>
    </div>
  `;
}

function slideReady(content, missionId) {
  const m = content.missions[missionId];
  return `
    <div class="hud-bar"><h2>READY</h2><span class="hud-dots">&bull; &bull; &bull; &bull;</span></div>
    <div class="content-grid">
      <div>
        <h1 class="ready-cta auto-in" style="--delay:0.15s">${esc(m.call_to_action)}</h1>
        <div class="btn-row auto-in" style="--delay:0.5s;justify-content:flex-start;">
          <button class="primary-btn" data-action="start">&#9654; Start</button>
        </div>
      </div>
      <div class="pedestal-scene auto-in" style="--delay:0.3s">
        ${renderModel(m.product_model, m.product_image)}
      </div>
    </div>
  `;
}

function slideDecision(content, decisionId) {
  const d = content.decisions[decisionId];
  const colsClass = d.options.length === 2 ? 'cols-2' : 'cols-3';
  const optionCards = d.options.map((opt, i) => {
    const num = opt.number || (i + 1);
    const bullets = opt.bullets.map(b => `<li>${esc(b)}</li>`).join('');
    return `
      <div class="option-card"
           data-decision="${esc(decisionId)}"
           data-option="${esc(opt.id)}"
           data-recommended="${opt.is_recommended ? '1' : '0'}"
           data-number="${num}">
        <div class="option-number">${num}</div>
        <h3 class="option-name">${esc(opt.name)}</h3>
        <ul class="option-bullets">${bullets}</ul>
        ${renderModel(opt.model, opt.image, { small: true })}
        <div class="option-hotkey">press <kbd>${num}</kbd></div>
      </div>`;
  }).join('');

  return `
    <div class="hud-bar"><h2>PORTAL ${d.portal_number} &middot; ${esc((d.portal_label||'').toUpperCase())}</h2><span class="hud-dots">&bull; &bull; &bull; &bull;</span></div>
    <div class="door-wrap auto-in" style="--delay:0.1s"><div class="door"><div class="door-light" data-door-light></div></div></div>
    <h2 class="decision-title auto-in" style="--delay:0.25s">${esc(d.title)}</h2>
    <p class="decision-subtitle auto-in" style="--delay:0.4s">${esc(d.subtitle || '')}</p>
    <div class="options-grid ${colsClass} auto-in" style="--delay:0.55s">${optionCards}</div>
    <p class="pick-prompt" data-pick-prompt style="display:none;">
      Locked in. Press <kbd>&rarr;</kbd> or <kbd>Space</kbd> for the next portal.
    </p>
  `;
}

function slideResult(content, missionId) {
  return `
    <div class="hud-bar"><h2>RESULT</h2><span class="hud-dots">&bull; &bull; &bull; &bull;</span></div>
    <h1 class="result-headline">${esc(content.result.headline)}</h1>
    <div class="result-tier" data-result-tier>-</div>
    <p data-result-tier-msg class="result-msg">&nbsp;</p>
    <div class="content-grid">
      <div>
        <div class="score-big"><span data-result-score>0</span> / <span data-result-max>0</span></div>
        <p data-result-body class="result-body"></p>
        <ul class="choices-recap" data-result-choices></ul>
      </div>
      <div class="pedestal-scene">
        ${renderModel(
          (content.missions[missionId] || {}).product_model,
          (content.missions[missionId] || {}).product_image
        )}
      </div>
    </div>
    <div class="btn-row" style="margin-top:24px;">
      <button class="primary-btn" data-action="replay">&#8634; Play Again</button>
    </div>
  `;
}

// ---- Pick + advance logic ---------------------------------------
function pickOption(decisionId, optionId) {
  state.choices[decisionId] = optionId;
  saveState();
  const slide = document.querySelector(`.reveal section[data-step-id="${decisionId}"]`);
  if (!slide) return;

  slide.querySelectorAll('.option-card').forEach(card => {
    const isSel = card.dataset.option === optionId;
    const isRec = card.dataset.recommended === '1';
    card.classList.toggle('selected', isSel);
    card.classList.toggle('dimmed', !isSel);
    card.classList.toggle('recommended-reveal', isRec);
  });

  const doorLight = slide.querySelector('[data-door-light]');
  if (doorLight) doorLight.classList.add('lit');

  const prompt = slide.querySelector('[data-pick-prompt]');
  if (prompt) {
    prompt.textContent = 'Locked in. Press → or Space for the next portal.';
    prompt.style.display = '';
  }
  updateHudScore();
}

function pickOptionByNumber(n) {
  const slide = deck.getCurrentSlide();
  if (!slide || slide.dataset.stepType !== 'decision') return;
  const card = slide.querySelector(`.option-card[data-number="${n}"]`);
  if (card) pickOption(slide.dataset.stepId, card.dataset.option);
}

// ---- Scoring ----------------------------------------------------
function computeResult(content) {
  let total = 0, max = 0;
  const chosen = {};
  for (const [dId, d] of Object.entries(content.decisions)) {
    max += Math.max(0, ...d.options.map(o => Number(o.score) || 0));
    const choiceId = state.choices[dId];
    if (!choiceId) continue;
    const opt = d.options.find(o => o.id === choiceId);
    if (opt) { total += Number(opt.score) || 0; chosen[dId] = opt; }
  }
  let tier = { label: '-', message: '' };
  for (const t of (content.result.score_tiers || [])) {
    if (total >= t.min && total <= t.max) { tier = t; break; }
  }
  return { total, max, tier, chosen };
}

function updateHudScore() {
  const content = window._content;
  if (!content) return;
  const r = computeResult(content);
  document.getElementById('hudScore').textContent = `Score: ${r.total}`;
}

function updateResultSlide() {
  const content = window._content;
  const slide = document.querySelector('.reveal section[data-step-type="result"]');
  if (!slide || !content) return;

  const r = computeResult(content);
  slide.querySelector('[data-result-tier]').textContent     = r.tier.label;
  slide.querySelector('[data-result-tier-msg]').textContent = r.tier.message;
  slide.querySelector('[data-result-score]').textContent    = r.total;
  slide.querySelector('[data-result-max]').textContent      = r.max;

  const nameFor = (dId) => (r.chosen[dId] && r.chosen[dId].name) || '-';
  const body = (content.result.body_template || '')
    .replace('{tray_name}',    nameFor('tray_type'))
    .replace('{paper_name}',   nameFor('paper_type'))
    .replace('{graphic_name}', nameFor('graphic_element'));
  slide.querySelector('[data-result-body]').textContent = body;

  const list = slide.querySelector('[data-result-choices]');
  list.innerHTML = '';
  for (const [dId, opt] of Object.entries(r.chosen)) {
    const d = content.decisions[dId];
    const badge = opt.is_recommended ? '<span class="rec-badge">RECOMMENDED</span>' : '';
    const li = document.createElement('li');
    li.innerHTML = `<strong>${esc(d.title)}:</strong> ${esc(opt.name)} &mdash; ${Number(opt.score)||0} pts ${badge}`;
    list.appendChild(li);
  }
}

// ---- Build deck -------------------------------------------------
function buildDeck(content) {
  window._content = content;
  const root = document.getElementById('slideContainer');
  root.innerHTML = '';

  const transitionFor = {
    title: 'fade', intro: 'slide', rules: 'slide',
    mission: 'convex', ready: 'zoom', decision: 'slide', result: 'convex',
  };

  const missionId = content.flow.find(s => s.type === 'mission')?.id || 'mission_monster_snacks';
  const bgMap = content.backgrounds || {};
  const defaultBg = (content.game_meta || {}).default_background || '';

  // Also collect per-decision background_image fields (set in the PPT/admin Decisions tab)
  const decisionBgMap = {};
  for (const [dId, d] of Object.entries(content.decisions || {})) {
    if (d.background_image) decisionBgMap[dId] = d.background_image;
  }

  for (const step of content.flow) {
    const section = document.createElement('section');
    section.dataset.stepType  = step.type;
    section.dataset.stepId    = step.id;
    section.dataset.transition = transitionFor[step.type] || 'slide';

    // Background image — set as data-background-* attrs so Reveal handles rendering
    const bgName = bgMap[step.id] || decisionBgMap[step.id] || defaultBg;
    if (bgName) {
      section.dataset.backgroundImage    = imgSrc(bgName);
      section.dataset.backgroundSize     = 'cover';
      section.dataset.backgroundPosition = 'center';
      section.dataset.backgroundRepeat   = 'no-repeat';
      section.classList.add('has-bg');
      // Mirror class to the background element so our CSS overlay selector works
      section.dataset.backgroundClass    = 'has-bg';
    }

    let html = '';
    switch (step.type) {
      case 'title':    html = slideTitle(content);                                              break;
      case 'intro':    html = slideIntro(content);                                              break;
      case 'rules':    html = slideRules(content);                                              break;
      case 'mission':  html = slideMission(content, step.id);                                   break;
      case 'ready':    html = slideReady(content, step.id.includes('mission') ? step.id : missionId); break;
      case 'decision': html = slideDecision(content, step.id);                                  break;
      case 'result':   html = slideResult(content, missionId);                                  break;
      default:         html = `<h2>Unknown step type: ${esc(step.type)}</h2>`;
    }
    section.innerHTML = html;
    root.appendChild(section);
  }

  // Re-apply visual state for choices already in session (e.g. after page refresh)
  for (const [dId, oId] of Object.entries(state.choices)) {
    const slide = document.querySelector(`section[data-step-id="${dId}"]`);
    if (!slide) continue;
    slide.querySelectorAll('.option-card').forEach(card => {
      const isSel = card.dataset.option === oId;
      card.classList.toggle('selected', isSel);
      card.classList.toggle('dimmed',   !isSel);
      card.classList.toggle('recommended-reveal', card.dataset.recommended === '1');
    });
    const doorLight = slide.querySelector('[data-door-light]');
    if (doorLight) doorLight.classList.add('lit');
    const prompt = slide.querySelector('[data-pick-prompt]');
    if (prompt) prompt.style.display = '';
  }
}

// ---- Event wiring -----------------------------------------------
function wireUpEvents() {
  // Click: option cards + action buttons
  document.addEventListener('click', (ev) => {
    const card = ev.target.closest('.option-card');
    if (card) { pickOption(card.dataset.decision, card.dataset.option); return; }
    const btn = ev.target.closest('[data-action]');
    if (btn) {
      const action = btn.dataset.action;
      if (action === 'start') deck.next();
      if (action === 'replay') {
        resetState();
        updateHudScore();
        buildDeck(window._content);
        deck.sync();
        deck.slide(0);
      }
    }
  });

  // Keyboard: 1/2/3 pick, R restart
  document.addEventListener('keydown', (ev) => {
    if (ev.target.matches('input,textarea,button,select,dialog')) return;
    if (ev.key === '1' || ev.key === '2' || ev.key === '3') {
      pickOptionByNumber(Number(ev.key)); ev.preventDefault();
    } else if (ev.key === 'r' || ev.key === 'R') {
      resetState(); updateHudScore();
      buildDeck(window._content); deck.sync(); deck.slide(0);
    }
  });

  // Help dialog
  const dlg = document.getElementById('helpDialog');
  document.getElementById('hudHelpBtn').addEventListener('click',  () => dlg.showModal());
  document.getElementById('helpCloseBtn').addEventListener('click', () => dlg.close());

  // Fullscreen button
  const fsBtn = document.getElementById('hudFsBtn');
  if (fsBtn) {
    fsBtn.addEventListener('click', () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen().catch(() => {});
    });
  }

  // Result: recompute when slide becomes active
  deck.on('slidechanged', (ev) => {
    if (ev.currentSlide?.dataset?.stepType === 'result') updateResultSlide();
  });

  // Nav guard: block advancing past a decision without picking
  document.addEventListener('keydown', (ev) => {
    if (ev.target.matches('input,textarea,button,select,dialog')) return;
    if (!['ArrowRight','PageDown',' ','Spacebar','n','N'].includes(ev.key)) return;
    const slide = deck.getCurrentSlide();
    if (!slide || slide.dataset.stepType !== 'decision') return;
    if (state.choices[slide.dataset.stepId]) return;
    ev.preventDefault(); ev.stopPropagation();
    const prompt = slide.querySelector('[data-pick-prompt]');
    if (prompt) {
      prompt.textContent = 'Pick an option to continue. Press 1, 2, or 3 — or click a card.';
      prompt.style.display = '';
      prompt.animate([{transform:'scale(1)'},{transform:'scale(1.06)'},{transform:'scale(1)'}],{duration:400});
    }
  }, true);
}

// ---- Boot -------------------------------------------------------
async function boot() {
  const status = document.getElementById('bootStatus');
  try {
    const res = await fetch(CONTENT_URL, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status} loading missions.json`);
    const content = await res.json();

    buildDeck(content);

    deck = new Reveal({
      hash:               true,
      controls:           true,
      progress:           true,
      width:              1920,
      height:             1080,
      margin:             0.04,
      minScale:           0.1,
      maxScale:           3.0,
      center:             true,   // vertically centers shorter slides
      transition:         'slide',
      transitionSpeed:    'default',
      backgroundTransition: 'fade',
      slideNumber:        'c/t',
      keyboard:           true,
      touch:              true,
      viewDistance:       3,
    });
    await deck.initialize();
    window._deck = deck;

    wireUpEvents();
    updateHudScore();
  } catch (err) {
    console.error(err);
    if (status) status.textContent = 'Failed to load game content: ' + err.message;
  }
}

boot();
