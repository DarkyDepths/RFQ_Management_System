// ============================================================================
// main.js — Reveal init + GSAP-driven slide motion
// ----------------------------------------------------------------------------
// Phase C wires the GRAVITY-COLLAPSE motion: on slide 0.2/0.3, advancing the
// Reveal fragment triggers a GSAP timeline that converges all 8 scatter tiles
// to the stage centre, fades them out, briefly pulses a central anchor, and
// reveals the locked hook phrase. Reduced-motion users skip directly to the
// collapsed end-state — no animation, but identical final composition.
// ============================================================================

// ──────────────────────────────────────────────────────────────────────────
// Reveal config — locked for the whole deck
// ──────────────────────────────────────────────────────────────────────────
Reveal.initialize({
  width:  1920,
  height: 1080,
  margin: 0,

  controls:    false,
  progress:    false,
  slideNumber: false,

  hash:                 true,
  keyboard:             true,
  touch:                true,
  respondToHashChanges: true,

  center: false,
  /* Soft 0.6s fade between slides — gives the 1 → 2 transition the
     "diving forward" feel as title content fades while storm tiles
     materialise. GSAP still owns per-slide motion. */
  transition:           'fade',
  backgroundTransition: 'none',
});

// ──────────────────────────────────────────────────────────────────────────
// Reduce-motion bucket + global namespace
// ──────────────────────────────────────────────────────────────────────────
const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

window.deck = {
  gsap,
  reducedMotion: reducedMotionQuery.matches,
  motion(buildFn) {
    if (this.reducedMotion) return undefined;
    return buildFn();
  },
};

reducedMotionQuery.addEventListener('change', (event) => {
  window.deck.reducedMotion = event.matches;
});


// Problem-storm resolve (slide 0.2 · anchor #1 of the hook arc).
// Slide 0.2 holds ~40 tiles + free-text fragments continuously cycling
// through depth via CSS @keyframes (camera-forward effect). On the
// fragment trigger, this timeline rushes all elements forward and
// dissolves them while the locked hook phrase fades up at centre with
// scrim. The CSS handles the *continuous* cycle; GSAP only handles the
// *resolve*. On resolve start we add `.resolving` to pause the CSS
// @keyframes so GSAP owns the transforms cleanly.

function buildStormResolve(scope) {
  const elements = scope.querySelectorAll('.storm-tile, .storm-text');
  const hook     = scope.querySelector('.storm-hook');

  const tl = gsap.timeline({ paused: true });

  // STEP 1 — capture each tile's CURRENT animated state (opacity, transform,
  // filter) into inline style. The CSS @keyframes have been driving these
  // values; we need to snapshot them before removing the animation so the
  // tiles don't snap to their CSS rule's opacity:0 the moment we kill the
  // animation. After this, inline styles fully control the tiles.
  tl.add(() => {
    elements.forEach((el) => {
      const cs = getComputedStyle(el);
      el.style.opacity   = cs.opacity;
      el.style.transform = cs.transform;
      el.style.filter    = cs.filter;
    });
    scope.classList.add('resolving');   // .resolving sets `animation: none`
  }, 0);

  // STEP 2 — Storm fades cleanly to ZERO. Now that animation is gone and
  // inline opacity is in control, GSAP's tween actually drives the fade.
  tl.to(elements, {
    opacity: 0,
    duration: 0.55,
    ease: 'power2.in',
    stagger: { each: 0.012, from: 'random' },
  }, 0.02);

  // STEP 3 — Hook waits for the storm to be FULLY gone before fading in.
  // Last storm element ends fading at ~0.012×26 + 0.55 + 0.02 ≈ 0.88s, so
  // hook starts at 0.95s — zero bleed-through between the two.
  tl.to(hook, {
    opacity: 1,
    duration: 0.85,
    ease: 'power2.out',
  }, 0.95);

  return tl;
}

const _stormCache = new WeakMap();
function getStormTl(scope) {
  if (!_stormCache.has(scope)) _stormCache.set(scope, buildStormResolve(scope));
  return _stormCache.get(scope);
}


// ──────────────────────────────────────────────────────────────────────────
// Agenda slide animation (slide 0.3)
// ──────────────────────────────────────────────────────────────────────────
// 7 scatter icons move through three positional states: scatter → centre
// stack → left stack (aligned with chapter rows). Border sweep ring fires
// on the centre stack as a "1, 2, 3 … 7" count-off in amber. Chapter row
// text + num revealed per click after icons settle left.

const AGENDA_POSITIONS = {
  // Centre stack — horizontal-leaning diagonal cascade. Each tile offsets
  // +8.5% x (≈163px) and +7% y (≈76px) from the previous, so adjacent tiles
  // don't overlap horizontally (3.6% gap) but stack ~50% vertically. With the
  // milder 3D tilt (rotateX 10°, rotateZ -6°), the row reads as a row of
  // parallel cards stepping down-right — icons in each card stay visible.
  center: [
    { x: 24.5, y: 27 },
    { x: 33.0, y: 34 },
    { x: 41.5, y: 41 },
    { x: 50.0, y: 48 },
    { x: 58.5, y: 55 },
    { x: 67.0, y: 62 },
    { x: 75.5, y: 69 },
  ],
  // Left column — icon centres aligned with the chapter-row icon slots.
  // y values match the row vertical centres (eyebrow + headline take ~17%
  // above row 1; each row is ~8.1% of the 1080 canvas).
  left: [
    { x: 6, y: 34.5 },
    { x: 6, y: 42.6 },
    { x: 6, y: 50.7 },
    { x: 6, y: 58.9 },
    { x: 6, y: 67.0 },
    { x: 6, y: 75.2 },
    { x: 6, y: 83.3 },
  ],
};

// Per-state tile sizes (px). Centre stack flattens focal to the same size as
// the others — in the stack moment we want a uniform row of seven (the speaker
// says "treated across seven steps"), not the scatter-state hierarchy.
const AGENDA_SIZES = {
  center: { std: 150, focal: 150 },
  left:   { std: 56,  focal: 56  },   // match chapter-row .chapter-icon (56px)
};

function animateAgendaIcons(slide, targetState) {
  const icons = slide.querySelectorAll('.scatter-icon');
  const positions = AGENDA_POSITIONS[targetState];
  const sizes     = AGENDA_SIZES[targetState];
  if (!positions || !sizes) return null;

  slide.classList.add('agenda-stacked');
  // The glyph font-size CSS hook fires only in the left state.
  slide.classList.toggle('agenda-stacked-left', targetState === 'left');

  const tl = gsap.timeline();
  const isCenter = targetState === 'center';

  icons.forEach((icon, i) => {
    const pos = positions[i];
    if (!pos) return;
    const isFocal = icon.classList.contains('focal');
    // Lock the GSAP transform base — xPercent/yPercent replaces the CSS
    // translate(-50%, -50%) so the rotateX/Z layer cleanly on top.
    tl.set(icon, { xPercent: -50, yPercent: -50 }, 0);
    tl.to(icon, {
      left:      pos.x + '%',
      top:       pos.y + '%',
      width:     isFocal ? sizes.focal : sizes.std,
      height:    isFocal ? sizes.focal : sizes.std,
      rotationX: isCenter ? 10 : 0,     // mild forward tilt — depth without hiding glyphs
      rotationZ: isCenter ? -6 : 0,     // slight CCW tilt — organic stack feel
      duration: 1.1,
      ease: 'power3.inOut',
    }, i * 0.04);
  });

  return tl;
}

function isAgendaCenterState(slide) {
  // The cascade callbacks gate on this — if the speaker has clicked past the
  // centre stack mid-cascade (icons now flying to left, or back to scatter),
  // pending light/fade adds are suppressed.
  return slide.classList.contains('agenda-stacked') &&
        !slide.classList.contains('agenda-stacked-left');
}

function triggerBorderSweep(slide) {
  // Two-beat sequence:
  //   1) Cascade 1→7 — each ring pulses on then fades, 260ms stagger.
  //      Speaker counts: "one, two, three… seven."
  //   2) Hold finale — after the last ring dies, a 300ms beat of darkness,
  //      then ALL seven light up together and hold. Speaker lands:
  //      "…seven chapters." Borders stay lit until the next click moves
  //      icons to the left stack (clearAgendaSweep there dissolves them).
  const icons = slide.querySelectorAll('.scatter-icon');
  icons.forEach((icon, i) => {
    const startDelay = i * 260;
    setTimeout(() => { if (isAgendaCenterState(slide)) icon.classList.add('sweep'); },        startDelay);
    setTimeout(() => { if (isAgendaCenterState(slide)) icon.classList.add('sweep-fade'); },   startDelay + 600);
    setTimeout(() => { icon.classList.remove('sweep', 'sweep-fade'); },                       startDelay + 1100);
  });
  const cascadeEnd = (icons.length - 1) * 260 + 1100;
  setTimeout(() => {
    if (!isAgendaCenterState(slide)) return;     // speaker already advanced — abort finale
    icons.forEach((icon) => {
      icon.classList.add('sweep');
      icon.classList.remove('sweep-fade');
    });
  }, cascadeEnd + 300);
}

function clearAgendaSweep(slide) {
  // Borders dissolve as icons depart the centre stack — the .sweep-ring
  // already transitions opacity over 0.45s, so removing the class lets the
  // ring fade out cleanly while the icons fly to their next position.
  slide.querySelectorAll('.scatter-icon').forEach((icon) => {
    icon.classList.remove('sweep', 'sweep-fade');
  });
}

function applyAgendaSweep(slide) {
  // Instant-on (no cascade) — used on reverse navigation and re-entry, where
  // the speaker has already seen the count-off and just expects the held state.
  slide.querySelectorAll('.scatter-icon').forEach((icon) => {
    icon.classList.add('sweep');
    icon.classList.remove('sweep-fade');
  });
}

function revealAgendaRow(slide, step) {
  const row = slide.querySelector(`.chapter-row[data-step="${step}"]`);
  if (row) row.classList.add('revealed');
}

function setAgendaState(slide, state) {
  // Used by slidechanged for re-entry — jumps directly to a state without GSAP
  if (!slide) return;
  if (state === 'all') {
    slide.classList.add('agenda-stacked', 'agenda-stacked-left', 'show-headline');
    const icons = slide.querySelectorAll('.scatter-icon');
    icons.forEach((icon, i) => {
      const pos = AGENDA_POSITIONS.left[i];
      if (!pos) return;
      gsap.set(icon, {
        left: pos.x + '%', top: pos.y + '%',
        xPercent: -50, yPercent: -50,
        width: 56, height: 56,
        rotationX: 0, rotationZ: 0,
      });
    });
    for (let s = 1; s <= 7; s++) revealAgendaRow(slide, s);
  }
}


// ──────────────────────────────────────────────────────────────────────────
// Title slide · cascade intro (slide 0.1)
// ----------------------------------------------------------------------------
// Each element starts invisible (CSS opacity 0). On slide entry we set the
// pre-anim transform offset, then play a timeline that lands each layer in
// turn: ambient → logos → academic header lines → eyebrow → title lines →
// subhead → "Élaboré chez" pill → credit cells. Total ~3s, then the slide
// sits and the ambient orb keeps breathing via CSS.
// ──────────────────────────────────────────────────────────────────────────

function getTitleParts(scope) {
  return {
    ambient:      scope.querySelector('.title-ambient'),
    logos:        scope.querySelectorAll('.title-logo-slot'),
    headerLines:  scope.querySelectorAll('.title-academic-header .line'),
    eyebrow:      scope.querySelector('.title-eyebrow'),
    titleLines:   scope.querySelectorAll('h1 .line'),
    subhead:      scope.querySelector('.title-subhead'),
    hostLine:     scope.querySelector('.title-host-line'),
    creditsIntro: scope.querySelector('.title-credits .credits-intro'),
    cells:        scope.querySelectorAll('.title-credits .cell'),
  };
}

function buildTitleIntro(scope) {
  const p = getTitleParts(scope);

  // pre-anim state — opacity matches CSS; transform offsets set inline
  gsap.set([p.logos, p.headerLines, p.eyebrow, p.titleLines,
            p.subhead, p.hostLine, p.creditsIntro, p.cells],
           { y: 28 });
  gsap.set(p.titleLines,  { y: 44 });   // title rises from a touch lower for weight
  gsap.set(p.hostLine,    { y: 20, scale: 0.96, transformOrigin: 'center' });
  gsap.set(p.creditsIntro, { y: 16 });  // intro line drifts in subtly before the cells

  const tl = gsap.timeline();

  tl.to(p.ambient,      { opacity: 0.85,           duration: 1.35, ease: 'power2.out' }, 0)
    .to(p.logos,        { opacity: 1, y: 0,        duration: 0.80, ease: 'power3.out' }, 0.20)
    .to(p.headerLines,  { opacity: 1, y: 0,        duration: 0.65, stagger: 0.10, ease: 'power3.out' }, 0.45)
    .to(p.eyebrow,      { opacity: 1, y: 0,        duration: 0.45, ease: 'power3.out' }, 1.05)
    .to(p.titleLines,   { opacity: 1, y: 0,        duration: 0.95, stagger: 0.14, ease: 'expo.out'  }, 1.20)
    .to(p.subhead,      { opacity: 1, y: 0,        duration: 0.50, ease: 'power3.out' }, 2.00)
    .to(p.hostLine,     { opacity: 1, y: 0, scale: 1, duration: 0.55, ease: 'back.out(1.6)' }, 2.25)
    .to(p.creditsIntro, { opacity: 1, y: 0,        duration: 0.45, ease: 'power3.out' }, 2.45)
    .to(p.cells,        { opacity: 1, y: 0,        duration: 0.55, stagger: 0.06, ease: 'power3.out' }, 2.65);

  return tl;
}

function showTitleInstant(scope) {
  const p = getTitleParts(scope);
  gsap.set([p.ambient, p.logos, p.headerLines, p.eyebrow, p.titleLines,
            p.subhead, p.hostLine, p.creditsIntro, p.cells],
           { opacity: 1, y: 0, scale: 1, clearProps: 'transform' });
  gsap.set(p.ambient, { opacity: 0.85 });
}

/**
 * Play the title intro cascade once, on first fragment-shown event.
 * Caller passes the .title-slide element directly (no longer wraps a slide).
 * No-ops if the cascade has already played (dataset.introPlayed = '1').
 * Reduce-motion users get the instant final state instead of the cascade.
 */
function maybePlayTitleIntro(scope) {
  if (!scope || scope.dataset.introPlayed === '1') return;
  scope.dataset.introPlayed = '1';
  if (window.deck.reducedMotion) {
    showTitleInstant(scope);
  } else {
    buildTitleIntro(scope);
  }
}



// ──────────────────────────────────────────────────────────────────────────
// Reveal event wiring
// ──────────────────────────────────────────────────────────────────────────

// ──────────────────────────────────────────────────────────────────────────
// Page numbering — populate `.page-num` on every slide from Reveal's
// slide index. Pad to two digits. Total updates if the deck grows.
// ──────────────────────────────────────────────────────────────────────────
function updatePageNums() {
  const total = Reveal.getTotalSlides();
  const totalStr = '/ ' + String(total).padStart(2, '0');
  document.querySelectorAll('.reveal .slides > section').forEach((slide, i) => {
    const num   = slide.querySelector('.page-num .num');
    const totEl = slide.querySelector('.page-num .total');
    if (num)   num.textContent   = String(i + 1).padStart(2, '0');
    if (totEl) totEl.textContent = totalStr;
  });
}


Reveal.on('ready', () => {
  // Page numbering across the whole deck.
  updatePageNums();

  // Inject the Itqān brand wordmark into the bottom-left corner of every
  // slide except the title (which already carries the wordmark in its
  // headline). One source-of-truth markup; CSS in base.css handles the
  // positioning. Skipped on .title-slide to avoid duplication.
  document.querySelectorAll('.reveal .slides > section > .slide').forEach((slide) => {
    if (slide.classList.contains('title-slide')) return;
    if (slide.querySelector('.slide-brand')) return;       // idempotent
    const brand = document.createElement('div');
    brand.className = 'slide-brand';
    brand.innerHTML = 'Itq<span class="accent">ā</span>n';
    slide.appendChild(brand);
  });

  // Pre-build storm-resolve timelines so the first key-press is instant.
  document.querySelectorAll('.problem-storm-slide').forEach((scope) => {
    getStormTl(scope).progress(0).paused(true);
  });

  // Checkpoint slides clone the WHOLE agenda block (eyebrow + headline +
  // chapter-index) so the layout — text positions, font sizes, hairlines —
  // is identical to the agenda. Only delta: which row carries .active.
  // Keeps markup DRY (one source of truth = the agenda slide).
  const sourceBlock = document.querySelector('.agenda-slide .agenda-block');
  if (sourceBlock) {
    document.querySelectorAll('.checkpoint-slide').forEach((slide) => {
      const target = slide.querySelector('.agenda-block');
      if (!target) return;
      target.innerHTML = sourceBlock.innerHTML;
      // Strip any .active class inherited from the agenda source.
      target.querySelectorAll('.chapter-row').forEach((r) => r.classList.remove('active'));
      // Mark the one row this checkpoint is highlighting.
      const step = slide.dataset.activeSection;
      const row  = step && target.querySelector(`.chapter-row[data-step="${step}"]`);
      if (row) row.classList.add('active');
    });
  }

  // If we landed on a checkpoint slide on initial page load (via URL hash),
  // trigger the entry animation now — slidechanged won't fire for the
  // first slide.
  activateCheckpointEntry(Reveal.getCurrentSlide());

  // Dev hatch — `?intro=skip` shows the title slide in its final composed
  // state immediately on load (for headless screenshots). Live presentation
  // never sends this param, so the title stays blank until the speaker
  // triggers the cascade with the first key-press / click.
  if (new URLSearchParams(location.search).get('intro') === 'skip') {
    document.querySelectorAll('.title-slide').forEach((scope) => {
      showTitleInstant(scope);
      scope.dataset.introPlayed = '1';
    });
  }

  // Dev hatch — render the post-collapse state directly via `?state=collapsed`
  // in the URL. Used for headless screenshots; not invoked in live presentation.
  if (new URLSearchParams(location.search).get('state') === 'resolved') {
    document.querySelectorAll('.problem-storm-slide').forEach((scope) => {
      if (window.deck.reducedMotion) {
        scope.classList.add('resolved');
      } else {
        getStormTl(scope).progress(1).paused(true);
      }
    });
  }

  console.info(
    '%c[Itqān · Phase C] Deck ready.',
    'font-family: monospace; color: #a06a18; font-weight: 600; font-size: 12px;',
    {
      Reveal:        typeof Reveal,
      gsap:          typeof gsap,
      gsapVersion:   gsap.version,
      reducedMotion: window.deck.reducedMotion,
      slides:        Reveal.getTotalSlides(),
    }
  );
});

// Text-scramble helper — left-to-right "decoder" wave that handles length
// asymmetry gracefully. A single scrambling position moves left→right
// across the text:
//   · positions BEFORE the wave: locked to target char (or hidden if shrinking)
//   · positions AT the wave: scrambling with random char
//   · positions AFTER the wave: show start char (if any), else hidden
// Result: when target is LONGER, text grows char-by-char; when SHORTER,
// the start text is "eaten" from the left as the wave advances.
// Cancellable via element._scrambleAbort.
function cancelScramble(element) {
  if (element && element._scrambleAbort) element._scrambleAbort();
}
function scrambleTo(element, newText, duration = 800) {
  if (!element) return;
  cancelScramble(element);

  let aborted = false;
  element._scrambleAbort = () => { aborted = true; };

  const startText = element.textContent;
  const startLen  = startText.length;
  const targetLen = newText.length;
  const maxLen    = Math.max(startLen, targetLen);
  const chars     = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const startTime = performance.now();

  function frame(now) {
    if (aborted) return;
    const elapsed  = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const wave     = progress * maxLen;          // wave-front position

    let result = '';
    for (let i = 0; i < maxLen; i++) {
      const phase = wave - i;                    // <0 not yet · 0..1 scrambling · >=1 locked
      const targetChar = i < targetLen ? newText[i]   : null;
      const startChar  = i < startLen  ? startText[i] : null;

      if (phase >= 1) {
        // Locked. Show target (or skip if target is shorter — char "disappears").
        if (targetChar === null)  continue;     // shrinking case: trim tail
        if (targetChar === ' ')   { result += ' '; continue; }
        result += targetChar;
      } else if (phase >= 0) {
        // Wave-front: scramble this position.
        if (targetChar === ' ')   { result += ' '; continue; }
        result += chars[Math.floor(Math.random() * chars.length)];
      } else {
        // Not yet reached.
        if (startChar === null)   continue;     // growing case: position hidden until reached
        if (startChar === ' ')    { result += ' '; continue; }
        result += startChar;
      }
    }
    element.textContent = result;

    if (progress < 1) requestAnimationFrame(frame);
    else {
      element.textContent = newText;
      element._scrambleAbort = null;
    }
  }
  requestAnimationFrame(frame);
}

// Slide 01.3 gap cards — per-card reveal + active-highlight helper.
// n = how many gap cards should be revealed; the LAST one carries .current
// (speaker is talking about that gap). n = 0 resets the grid.
function setGapCard(slide, n) {
  if (!slide) return;
  const cards = slide.querySelectorAll('.gap-card');
  cards.forEach((card, i) => {
    card.classList.toggle('revealed', i < n);
    card.classList.toggle('current',  i === n - 1);
  });
}

// Slide 01.2 audit convergence — per-input reveal + active-highlight helper.
// n = how many input nodes should be revealed; the LAST one carries .current
// (speaker is on that input). n = 0 resets the column to empty.
function setFlowInput(slide, n) {
  if (!slide) return;
  const inputs = slide.querySelectorAll('.flow-input');
  inputs.forEach((input, i) => {
    input.classList.toggle('revealed', i < n);
    input.classList.toggle('current',  i === n - 1);
  });
}

// Slide 01.1.b lifecycle rail — per-stage reveal + active-highlight helper.
// stageNum = how many stages should be revealed; the LAST one carries the
// .current pulse (speaker is on that stage right now). stageNum=0 means
// reset (empty rail). stageNum=8 (chips reached) means all revealed, no
// .current (caller passes 7 then clears .current separately for chips).
function setRailStage(slide, stageNum) {
  if (!slide) return;
  const stages = slide.querySelectorAll('.rail-stage');
  const arrows = slide.querySelectorAll('.rail-arrow');
  stages.forEach((stage, i) => {
    stage.classList.toggle('revealed', i < stageNum);
    stage.classList.toggle('current',  i === stageNum - 1);
  });
  arrows.forEach((arrow, i) => {
    // Arrow i sits between stage i and stage i+1 → reveal when stage i+1 is revealed.
    arrow.classList.toggle('revealed', i < stageNum - 1);
  });
}

// Snap-set helper for slide 01.1.a re-entry (slidechanged) — no scramble,
// instant text swap so re-entering the slide lands cleanly without replay.
// Cancels any in-flight scramble first.
function setRfqCentreText(slide, lang) {
  if (!slide) return;
  const title    = slide.querySelector('[data-rfq-title]');
  const subtitle = slide.querySelector('[data-rfq-subtitle]');
  cancelScramble(title);
  cancelScramble(subtitle);
  if (lang === 'fr') {
    if (title)    title.textContent    = 'Demande de devis';
    if (subtitle) subtitle.textContent = 'quotation-focused request';
  } else {
    if (title)    title.textContent    = 'RFQ';
    if (subtitle) subtitle.textContent = 'Request for Quotation';
  }
}


Reveal.on('fragmentshown', (event) => {
  const trigger = event.fragment;

  // ── Slide 01.1.a · RFQ definition · 5-click sequence ─────────────────
  // Click 0: empty slide → canvas fades up (deck-wide pattern: every
  // subsection slide should land EMPTY, first click reveals the body).
  if (trigger.matches('[data-rfq-show]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (slide) slide.classList.add('canvas-shown');
    return;
  }
  if (trigger.matches('[data-rfq-morph-fr]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (!slide) return;
    scrambleTo(slide.querySelector('[data-rfq-title]'),    'Demande de devis');
    scrambleTo(slide.querySelector('[data-rfq-subtitle]'), 'quotation-focused request');
    return;
  }
  if (trigger.matches('[data-rfq-morph-en]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (!slide) return;
    scrambleTo(slide.querySelector('[data-rfq-title]'),    'RFQ');
    scrambleTo(slide.querySelector('[data-rfq-subtitle]'), 'Request for Quotation');
    return;
  }
  if (trigger.matches('[data-rfq-artifacts]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (slide) slide.classList.add('artifacts-shown');
    return;
  }
  if (trigger.matches('[data-rfq-synthesis]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (slide) slide.classList.add('synthesis-shown');
    return;
  }

  // ── Slide 01.1.b · Industrial RFQ Lifecycle · 9-click sequence ───────
  // Clicks 1-7 reveal each rail stage one at a time. The most recently
  // revealed stage carries the .current pulse highlight; previous stages
  // stay visible at normal style. Click 8 reveals the 3-column context
  // band (with L→R column stagger) and clears the rail's current highlight.
  // Click 9 reveals the synthesis sentence.
  if (trigger.matches('[data-lc-stage]')) {
    const slide = trigger.closest('.lifecycle-slide');
    if (slide) setRailStage(slide, parseInt(trigger.dataset.lcStage, 10));
    return;
  }
  if (trigger.matches('[data-lc-context]')) {
    const slide = trigger.closest('.lifecycle-slide');
    if (!slide) return;
    slide.classList.add('context-shown');
    // Speaker has moved past the rail stages — clear the current highlight
    // so all 7 stages read as "fully revealed, lifecycle complete".
    slide.querySelectorAll('.rail-stage.current').forEach((s) => s.classList.remove('current'));
    return;
  }
  if (trigger.matches('[data-lc-sentence]')) {
    const slide = trigger.closest('.lifecycle-slide');
    if (slide) slide.classList.add('sentence-shown');
    return;
  }

  // ── Slide 01.2 · GHI Audit Approach · 7-click convergence sequence ───
  // Click 1: header (badge + claim).
  // Clicks 2-4: 3 input nodes; .current pulses on the most recent one.
  // Click 5: convergence — connectors stroke-draw in sequence + center
  //          node ("Map Control Gaps") appears with .current pulse;
  //          .current is cleared from inputs (focus moves to synthesis).
  // Click 6: center→output connector draws + output node appears with
  //          .current pulse; center's .current clears.
  // Click 7: bottom output strip fades up; output's .current clears.
  if (trigger.matches('[data-audit-header]')) {
    const slide = trigger.closest('.audit-slide');
    if (slide) slide.classList.add('header-shown');
    return;
  }
  if (trigger.matches('[data-audit-input]')) {
    const slide = trigger.closest('.audit-slide');
    if (slide) setFlowInput(slide, parseInt(trigger.dataset.auditInput, 10));
    return;
  }
  if (trigger.matches('[data-audit-converge]')) {
    const slide = trigger.closest('.audit-slide');
    if (!slide) return;
    slide.classList.add('converge-shown');
    slide.querySelectorAll('.flow-input.current').forEach((n) => n.classList.remove('current'));
    const center = slide.querySelector('.flow-center-node');
    if (center) { center.classList.add('revealed'); center.classList.add('current'); }
    return;
  }
  if (trigger.matches('[data-audit-output]')) {
    const slide = trigger.closest('.audit-slide');
    if (!slide) return;
    slide.classList.add('output-shown');
    const center = slide.querySelector('.flow-center-node');
    if (center) center.classList.remove('current');
    const output = slide.querySelector('.flow-output-node');
    if (output) { output.classList.add('revealed'); output.classList.add('current'); }
    return;
  }
  if (trigger.matches('[data-audit-strip]')) {
    const slide = trigger.closest('.audit-slide');
    if (!slide) return;
    slide.classList.add('strip-shown');
    const output = slide.querySelector('.flow-output-node');
    if (output) output.classList.remove('current');
    return;
  }

  // ── Slide 01.3 · Control Gaps Before Quotation · 7-click sequence ────
  // 1) claim sentence · 2) 3-zone timeline · 3-6) 4 gap cards, per-card
  // amber pulse on the current · 7) bottom diagnosis strip (pulse clears).
  if (trigger.matches('[data-gaps-sentence]')) {
    const slide = trigger.closest('.gaps-slide');
    if (slide) slide.classList.add('sentence-shown');
    return;
  }
  if (trigger.matches('[data-gaps-timeline]')) {
    const slide = trigger.closest('.gaps-slide');
    if (slide) slide.classList.add('timeline-shown');
    return;
  }
  if (trigger.matches('[data-gaps-card]')) {
    const slide = trigger.closest('.gaps-slide');
    if (slide) setGapCard(slide, parseInt(trigger.dataset.gapsCard, 10));
    return;
  }
  if (trigger.matches('[data-gaps-diagnosis]')) {
    const slide = trigger.closest('.gaps-slide');
    if (!slide) return;
    slide.classList.add('diagnosis-shown');
    // Speaker moves to the conclusion — clear the last card's pulse.
    slide.querySelectorAll('.gap-card.current').forEach((c) => c.classList.remove('current'));
    return;
  }

  // Title-slide cascade — first click on slide 0.1 plays the intro reveal.
  if (trigger.matches('[data-title-intro-trigger]')) {
    const scope = trigger.closest('.title-slide');
    if (scope) maybePlayTitleIntro(scope);
    return;
  }

  // Storm-START trigger — first click on slide 0.2 starts the depth cycle.
  // Until then the CSS animations are paused (storm sits blank).
  if (trigger.matches('[data-storm-start]')) {
    const scope = trigger.closest('.problem-storm-slide');
    if (scope) scope.classList.add('storm-running');
    return;
  }

  // Agenda · click 1 — icons fly to vertical CENTRE stack + amber border
  // sweep cascades through them (1→7) as a visible "treated in 7 chapters"
  // count-off. Border fades back to neutral after each icon's sweep.
  if (trigger.matches('[data-agenda-stack-center]')) {
    const slide = trigger.closest('.agenda-slide');
    if (!slide) return;
    if (window.deck.reducedMotion) {
      slide.classList.add('agenda-stacked');
      return;
    }
    animateAgendaIcons(slide, 'center');
    setTimeout(() => triggerBorderSweep(slide), 1150);
    return;
  }

  // Agenda · click 2 — icons translate from centre to left stack
  // positions; agenda eyebrow + headline fade in alongside. Borders fade
  // out in parallel (clearAgendaSweep removes the .sweep class, the 0.45s
  // opacity transition dissolves the rings while the tiles fly to the left).
  if (trigger.matches('[data-agenda-stack-left]')) {
    const slide = trigger.closest('.agenda-slide');
    if (!slide) return;
    if (window.deck.reducedMotion) {
      slide.classList.add('show-headline');
      return;
    }
    clearAgendaSweep(slide);
    animateAgendaIcons(slide, 'left');
    slide.classList.add('show-headline');
    return;
  }

  // Agenda · clicks 3–9 — per-row text + num reveal.
  if (trigger.matches('[data-agenda-row]')) {
    const slide = trigger.closest('.agenda-slide');
    const step  = trigger.getAttribute('data-agenda-row');
    if (slide && step) revealAgendaRow(slide, step);
    return;
  }

  // Storm-RESOLVE trigger — second click dissolves tiles + reveals the hook.
  if (!trigger.matches('[data-storm-resolve]')) return;

  const scope = trigger.closest('.problem-storm-slide');
  if (!scope) return;

  if (window.deck.reducedMotion) {
    scope.classList.add('resolved');
    return;
  }

  const tl = getStormTl(scope);
  tl.timeScale(1).play();
});

Reveal.on('fragmenthidden', (event) => {
  const trigger = event.fragment;

  // ── Slide 01.1.a · reverse navigation ────────────────────────────────
  // Hiding the show fragment → empty slide state.
  if (trigger.matches('[data-rfq-show]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (slide) slide.classList.remove('canvas-shown');
    return;
  }
  // Hiding morph-fr (going back past click 2) → centre is English again.
  if (trigger.matches('[data-rfq-morph-fr]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (!slide) return;
    scrambleTo(slide.querySelector('[data-rfq-title]'),    'RFQ');
    scrambleTo(slide.querySelector('[data-rfq-subtitle]'), 'Request for Quotation');
    return;
  }
  // Hiding morph-en (going back past click 2 — back to French state).
  if (trigger.matches('[data-rfq-morph-en]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (!slide) return;
    scrambleTo(slide.querySelector('[data-rfq-title]'),    'Demande de devis');
    scrambleTo(slide.querySelector('[data-rfq-subtitle]'), 'quotation-focused request');
    return;
  }
  if (trigger.matches('[data-rfq-artifacts]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (slide) slide.classList.remove('artifacts-shown');
    return;
  }
  if (trigger.matches('[data-rfq-synthesis]')) {
    const slide = trigger.closest('.rfq-def-slide');
    if (slide) slide.classList.remove('synthesis-shown');
    return;
  }

  // ── Slide 01.1.b · reverse navigation ────────────────────────────────
  // Hiding a stage fragment → rail rolls back to the previous stage.
  if (trigger.matches('[data-lc-stage]')) {
    const slide = trigger.closest('.lifecycle-slide');
    if (slide) setRailStage(slide, parseInt(trigger.dataset.lcStage, 10) - 1);
    return;
  }
  // Hiding the context band → restore .current on stage 7 (the band only
  // fires after all 7 stages are revealed, so the speaker is "back on" 7).
  if (trigger.matches('[data-lc-context]')) {
    const slide = trigger.closest('.lifecycle-slide');
    if (!slide) return;
    slide.classList.remove('context-shown');
    const stages = slide.querySelectorAll('.rail-stage');
    if (stages[6]) stages[6].classList.add('current');
    return;
  }
  if (trigger.matches('[data-lc-sentence]')) {
    const slide = trigger.closest('.lifecycle-slide');
    if (slide) slide.classList.remove('sentence-shown');
    return;
  }

  // ── Slide 01.2 · reverse navigation ──────────────────────────────────
  // Each rollback restores the previous beat's .current highlight so the
  // pulse follows the speaker's actual position.
  if (trigger.matches('[data-audit-header]')) {
    const slide = trigger.closest('.audit-slide');
    if (slide) slide.classList.remove('header-shown');
    return;
  }
  if (trigger.matches('[data-audit-input]')) {
    const slide = trigger.closest('.audit-slide');
    if (slide) setFlowInput(slide, parseInt(trigger.dataset.auditInput, 10) - 1);
    return;
  }
  if (trigger.matches('[data-audit-converge]')) {
    const slide = trigger.closest('.audit-slide');
    if (!slide) return;
    slide.classList.remove('converge-shown');
    const center = slide.querySelector('.flow-center-node');
    if (center) { center.classList.remove('revealed'); center.classList.remove('current'); }
    // Back on input 3 (the converge fires only after all 3 inputs are shown).
    const inputs = slide.querySelectorAll('.flow-input');
    if (inputs[2]) inputs[2].classList.add('current');
    return;
  }
  if (trigger.matches('[data-audit-output]')) {
    const slide = trigger.closest('.audit-slide');
    if (!slide) return;
    slide.classList.remove('output-shown');
    const output = slide.querySelector('.flow-output-node');
    if (output) { output.classList.remove('revealed'); output.classList.remove('current'); }
    const center = slide.querySelector('.flow-center-node');
    if (center) center.classList.add('current');
    return;
  }
  if (trigger.matches('[data-audit-strip]')) {
    const slide = trigger.closest('.audit-slide');
    if (!slide) return;
    slide.classList.remove('strip-shown');
    const output = slide.querySelector('.flow-output-node');
    if (output) output.classList.add('current');
    return;
  }

  // ── Slide 01.3 · reverse navigation ──────────────────────────────────
  if (trigger.matches('[data-gaps-sentence]')) {
    const slide = trigger.closest('.gaps-slide');
    if (slide) slide.classList.remove('sentence-shown');
    return;
  }
  if (trigger.matches('[data-gaps-timeline]')) {
    const slide = trigger.closest('.gaps-slide');
    if (slide) slide.classList.remove('timeline-shown');
    return;
  }
  if (trigger.matches('[data-gaps-card]')) {
    const slide = trigger.closest('.gaps-slide');
    if (slide) setGapCard(slide, parseInt(trigger.dataset.gapsCard, 10) - 1);
    return;
  }
  if (trigger.matches('[data-gaps-diagnosis]')) {
    const slide = trigger.closest('.gaps-slide');
    if (!slide) return;
    slide.classList.remove('diagnosis-shown');
    // Restore .current on card 4 (the diagnosis only fires after all cards).
    const cards = slide.querySelectorAll('.gap-card');
    if (cards[3]) cards[3].classList.add('current');
    return;
  }

  // Title-slide — going back (left arrow on slide 0.1 from the shown state)
  // resets to the blank pre-anim state so the next forward press replays.
  if (trigger.matches('[data-title-intro-trigger]')) {
    const scope = trigger.closest('.title-slide');
    if (!scope) return;
    scope.dataset.introPlayed = '';
    const p = getTitleParts(scope);
    gsap.set([p.ambient, p.logos, p.headerLines, p.eyebrow, p.titleLines,
              p.subhead, p.hostLine, p.cells],
             { opacity: 0, clearProps: 'transform' });
    return;
  }

  // Storm-START hide — pressing back from running state pauses the storm
  // again (returns to the blank pre-start state).
  if (trigger.matches('[data-storm-start]')) {
    const scope = trigger.closest('.problem-storm-slide');
    if (scope) scope.classList.remove('storm-running');
    return;
  }

  // Agenda reverses — going back through the phases.
  if (trigger.matches('[data-agenda-row]')) {
    const slide = trigger.closest('.agenda-slide');
    const step  = trigger.getAttribute('data-agenda-row');
    const row   = slide && slide.querySelector(`.chapter-row[data-step="${step}"]`);
    if (row) row.classList.remove('revealed');
    return;
  }
  if (trigger.matches('[data-agenda-stack-left]')) {
    const slide = trigger.closest('.agenda-slide');
    if (!slide) return;
    slide.classList.remove('show-headline');
    // animateAgendaIcons handles re-adding/removing agenda-stacked-left.
    // On reverse, borders re-appear instantly (no cascade — speaker has
    // already seen the count-off, they just want the held state back).
    if (!window.deck.reducedMotion) {
      animateAgendaIcons(slide, 'center');
      applyAgendaSweep(slide);
    }
    return;
  }
  if (trigger.matches('[data-agenda-stack-center]')) {
    const slide = trigger.closest('.agenda-slide');
    if (!slide) return;
    slide.classList.remove('agenda-stacked', 'agenda-stacked-left');
    clearAgendaSweep(slide);     // borders fade out as tiles fly back to scatter
    if (!window.deck.reducedMotion) {
      // Restore icons to their scatter positions, full scatter size + flat
      // (no rotation). Don't re-enable the CSS drift animation here — once an
      // icon has an inline transform from GSAP, it owns it. Removing the
      // .agenda-stacked class re-enables the @keyframes, which then takes back
      // over by overwriting the inline transform after this tween completes.
      const icons = slide.querySelectorAll('.scatter-icon');
      icons.forEach((icon) => {
        const sx = icon.style.getPropertyValue('--scatter-x');
        const sy = icon.style.getPropertyValue('--scatter-y');
        const isFocal = icon.classList.contains('focal');
        gsap.to(icon, {
          left: sx, top: sy,
          xPercent: -50, yPercent: -50,
          width:  isFocal ? 200 : 160,
          height: isFocal ? 200 : 160,
          rotationX: 0, rotationZ: 0,
          duration: 1.0, ease: 'power3.inOut',
          onComplete: () => gsap.set(icon, { clearProps: 'transform,width,height' }),
        });
      });
    }
    return;
  }

  // Storm-resolve hide — pressing back from the resolved state plays the
  // timeline in reverse, then HARD-RESTARTS every tile's CSS cycle so the
  // storm builds up fresh from t=0 instead of resuming the frozen frame
  // captured at resolve time.
  if (!trigger.matches('[data-storm-resolve]')) return;

  const scope = trigger.closest('.problem-storm-slide');
  if (!scope) return;

  if (window.deck.reducedMotion) {
    scope.classList.remove('resolved');
    return;
  }

  const tl = getStormTl(scope);
  tl.timeScale(1.4);
  tl.eventCallback('onReverseComplete', () => {
    // 1) Remove .resolving so the CSS @keyframes rule applies again.
    scope.classList.remove('resolving');

    // 2) Clear inline opacity/transform/filter that the capture-then-tween
    //    chain set on every tile. Without this, the @keyframes can't drive
    //    the visible state — inline transform was holding tiles frozen at
    //    their captured z-depth.
    const elements = scope.querySelectorAll('.storm-tile, .storm-text');
    elements.forEach((el) => {
      el.style.opacity   = '';
      el.style.transform = '';
      el.style.filter    = '';
      // Force the animation to reset by setting it to none inline …
      el.style.animationName = 'none';
    });

    // 3) Reflow so the browser commits the "no animation" state …
    void scope.offsetWidth;

    // 4) … then release the inline override so the CSS rule re-applies and
    //    every tile restarts its cycle from 0 + its own --cycle-delay. The
    //    storm visibly *builds up* from sparse to full, instead of snapping
    //    back to a frozen mid-cycle frame.
    elements.forEach((el) => { el.style.animationName = ''; });
  });
  tl.reverse();
});

// Re-trigger the checkpoint entry animation every time we LAND on a
// checkpoint slide. Removing the class then force-reflowing then re-adding
// restarts the CSS animations from t=0 so the wash blooms in again.
function activateCheckpointEntry(currentSlide) {
  if (!currentSlide) return;
  const cp = currentSlide.classList && currentSlide.classList.contains('checkpoint-slide')
    ? currentSlide
    : currentSlide.querySelector('.checkpoint-slide');
  if (!cp) return;                       // not on a checkpoint — leave others alone
  cp.classList.remove('animate-in');
  void cp.offsetWidth;                   // force reflow → animation restarts
  cp.classList.add('animate-in');
}

Reveal.on('slidechanged', (event) => {
  activateCheckpointEntry(event.currentSlide);
  const slide = event.currentSlide;

  // Re-entering the title slide with the intro fragment already shown
  // (e.g. user pressed ← from slide 0.2 and the trigger is still "visible")
  // should land directly in the composed state — don't replay the cascade.
  const titleScope = slide.querySelector('.title-slide');
  if (titleScope) {
    const titleTrigger = slide.querySelector('[data-title-intro-trigger]');
    const titleShown = titleTrigger && titleTrigger.classList.contains('visible');
    if (titleShown && titleScope.dataset.introPlayed !== '1') {
      showTitleInstant(titleScope);
      titleScope.dataset.introPlayed = '1';
    }
  }

  // Slide 01.1.a re-entry — set canvas-shown / centre text / cluster /
  // synthesis states based on which fragments are already visible. No
  // scramble replay; instant snap so re-entry feels seamless.
  const rfqSlide = slide.querySelector('.rfq-def-slide');
  if (rfqSlide) {
    const showShown       = !!slide.querySelector('[data-rfq-show].visible');
    const morphFrShown    = !!slide.querySelector('[data-rfq-morph-fr].visible');
    const morphEnShown    = !!slide.querySelector('[data-rfq-morph-en].visible');
    const artifactsShown  = !!slide.querySelector('[data-rfq-artifacts].visible');
    const synthesisShown  = !!slide.querySelector('[data-rfq-synthesis].visible');
    rfqSlide.classList.toggle('canvas-shown',    showShown);
    rfqSlide.classList.toggle('artifacts-shown', artifactsShown);
    rfqSlide.classList.toggle('synthesis-shown', synthesisShown);
    // French only when morph-fr is shown but morph-en hasn't fired yet.
    setRfqCentreText(rfqSlide, (morphFrShown && !morphEnShown) ? 'fr' : 'en');
  }

  // Slide 01.1.b re-entry — restore the rail to its deepest visible stage,
  // plus context/synthesis flags. No animation replay; just instant snap.
  const lcSlide = slide.querySelector('.lifecycle-slide');
  if (lcSlide) {
    let maxStage = 0;
    for (let n = 7; n >= 1; n--) {
      if (slide.querySelector(`[data-lc-stage="${n}"].visible`)) { maxStage = n; break; }
    }
    setRailStage(lcSlide, maxStage);

    const contextShown  = !!slide.querySelector('[data-lc-context].visible');
    const sentenceShown = !!slide.querySelector('[data-lc-sentence].visible');
    lcSlide.classList.toggle('context-shown',  contextShown);
    lcSlide.classList.toggle('sentence-shown', sentenceShown);
    // If context is visible, clear the rail's current highlight (stage 7
    // sits as "complete, no longer being narrated").
    if (contextShown) {
      lcSlide.querySelectorAll('.rail-stage.current').forEach((s) => s.classList.remove('current'));
    }
  }

  // Slide 01.2 re-entry — restore the convergence-diagram state without
  // replaying the line-draw animation. Snaps each node and connector class
  // to match the deepest visible fragment.
  const auditSlide = slide.querySelector('.audit-slide');
  if (auditSlide) {
    let maxInput = 0;
    for (let n = 3; n >= 1; n--) {
      if (slide.querySelector(`[data-audit-input="${n}"].visible`)) { maxInput = n; break; }
    }
    setFlowInput(auditSlide, maxInput);

    const headerShown   = !!slide.querySelector('[data-audit-header].visible');
    const convergeShown = !!slide.querySelector('[data-audit-converge].visible');
    const outputShown   = !!slide.querySelector('[data-audit-output].visible');
    const stripShown    = !!slide.querySelector('[data-audit-strip].visible');

    auditSlide.classList.toggle('header-shown',   headerShown);
    auditSlide.classList.toggle('converge-shown', convergeShown);
    auditSlide.classList.toggle('output-shown',   outputShown);
    auditSlide.classList.toggle('strip-shown',    stripShown);

    const center = auditSlide.querySelector('.flow-center-node');
    if (center) {
      center.classList.toggle('revealed', convergeShown);
      // center pulses only while it IS the current beat (converge shown, output not yet)
      center.classList.toggle('current',  convergeShown && !outputShown);
    }
    const output = auditSlide.querySelector('.flow-output-node');
    if (output) {
      output.classList.toggle('revealed', outputShown);
      // output pulses only while it IS the current beat (output shown, strip not yet)
      output.classList.toggle('current',  outputShown && !stripShown);
    }
    // Once converge is shown, inputs are no longer the focus — kill their pulse.
    if (convergeShown) {
      auditSlide.querySelectorAll('.flow-input.current').forEach((n) => n.classList.remove('current'));
    }
  }

  // Slide 01.3 re-entry — snap sentence/timeline/diagnosis flags, and
  // restore the gap-card row to its deepest visible state. No animation
  // replay; just instant set.
  const gapsSlide = slide.querySelector('.gaps-slide');
  if (gapsSlide) {
    gapsSlide.classList.toggle('sentence-shown',  !!slide.querySelector('[data-gaps-sentence].visible'));
    gapsSlide.classList.toggle('timeline-shown',  !!slide.querySelector('[data-gaps-timeline].visible'));
    const diagnosisShown = !!slide.querySelector('[data-gaps-diagnosis].visible');
    gapsSlide.classList.toggle('diagnosis-shown', diagnosisShown);

    let maxCard = 0;
    for (let n = 4; n >= 1; n--) {
      if (slide.querySelector(`[data-gaps-card="${n}"].visible`)) { maxCard = n; break; }
    }
    setGapCard(gapsSlide, maxCard);
    // If diagnosis is shown, the speaker has moved past the cards — clear pulses.
    if (diagnosisShown) {
      gapsSlide.querySelectorAll('.gap-card.current').forEach((c) => c.classList.remove('current'));
    }
  }

  // Agenda re-entry — if any agenda fragment is already shown, jump to
  // the deepest state without replaying the cinematic intro.
  const agendaSlide = slide.querySelector('.agenda-slide');
  if (agendaSlide) {
    const stackCenterShown = !!slide.querySelector('[data-agenda-stack-center].visible');
    const stackLeftShown   = !!slide.querySelector('[data-agenda-stack-left].visible');
    const rowsShown = [];
    for (let s = 1; s <= 7; s++) {
      if (slide.querySelector(`[data-agenda-row="${s}"].visible`)) rowsShown.push(s);
    }
    if (stackLeftShown) {
      // Either: left stack with some rows revealed, or fully revealed.
      agendaSlide.classList.add('agenda-stacked', 'agenda-stacked-left', 'show-headline');
      const icons = agendaSlide.querySelectorAll('.scatter-icon');
      icons.forEach((icon, i) => {
        const pos = AGENDA_POSITIONS.left[i];
        if (!pos) return;
        gsap.set(icon, {
          left: pos.x + '%', top: pos.y + '%',
          xPercent: -50, yPercent: -50,
          width: 56, height: 56,
          rotationX: 0, rotationZ: 0,
        });
      });
      rowsShown.forEach((s) => revealAgendaRow(agendaSlide, s));
    } else if (stackCenterShown) {
      agendaSlide.classList.add('agenda-stacked');
      agendaSlide.classList.remove('agenda-stacked-left');
      const icons = agendaSlide.querySelectorAll('.scatter-icon');
      icons.forEach((icon, i) => {
        const pos = AGENDA_POSITIONS.center[i];
        if (!pos) return;
        gsap.set(icon, {
          left: pos.x + '%', top: pos.y + '%',
          xPercent: -50, yPercent: -50,
          width: 150, height: 150,
          rotationX: 10, rotationZ: -6,
        });
      });
      applyAgendaSweep(agendaSlide);   // held state: all borders lit on re-entry
    }
  }

  // Re-entry rules for the storm slide. Two fragments matter:
  //   data-storm-start    → storm CSS animations running?
  //   data-storm-resolve  → GSAP resolve completed (hook visible)?
  // We mirror each state on re-entry so the slide always lands correctly.
  const scope = slide.querySelector('.problem-storm-slide');
  if (!scope) return;

  const startTrigger   = slide.querySelector('[data-storm-start]');
  const resolveTrigger = slide.querySelector('[data-storm-resolve]');
  const startShown   = startTrigger   && startTrigger.classList.contains('visible');
  const resolveShown = resolveTrigger && resolveTrigger.classList.contains('visible');

  // CSS-animations running state
  scope.classList.toggle('storm-running', !!startShown);

  if (window.deck.reducedMotion) {
    scope.classList.toggle('resolved', !!resolveShown);
    return;
  }

  // GSAP resolve state
  const tl = getStormTl(scope);
  if (resolveShown) {
    tl.progress(1).paused(true);
  } else {
    tl.progress(0).paused(true);
    scope.classList.remove('resolving');
  }
});
