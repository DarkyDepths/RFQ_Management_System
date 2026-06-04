# Itqān Defense Deck — Claude Code Build Brief
### In the folder with: DESIGN.md (visual contract) · blueprint.html (narrative contract) · 3 prototype_*.html (reference only)

---

## 0 · What you are building
A **Reveal.js** keynote-style defense presentation for a final-year engineering PFE. Light-first, premium, **datashow-legible**. Two contracts govern it:
- **DESIGN.md (v0.4)** — the **visual contract**: tokens, type scale, components, motion, anti-patterns. If your output disagrees with it, **it wins.**
- **blueprint.html (v2.0)** — the **narrative contract**: the seven steps, opening sequence, timing, per-slide objectives, the recurring hook, the demo plan. This defines *what each slide says and why*.

You execute against both. You do NOT redesign the system or rewrite the narrative — you build them well.

## 1 · The prototypes are REFERENCE, not pixel law
`prototype_opening_hook.html`, `prototype_agenda.html`, `prototype_gravity_collapse.html` are **early prototypes**. They show **intent** — composition, mood, the motion idea, how the system feels. **Do not reproduce them pixel-for-pixel.** Rebuild to production quality using the design skills below, honoring DESIGN.md. They are the floor of quality and the direction, not the ceiling. Where a prototype and DESIGN.md differ, DESIGN.md wins; where DESIGN.md is silent, use the skills' taste — but never to override a frozen decision (color, type, primitive, motion doctrine).

## 2 · Use the design skills (this is how you build well)
Apply the available skills as the means of execution:
- **gpt-taste** — editorial UX/UI + **GSAP motion engineering**. Primary for the gravity-collapse and all slide motion.
- **high-end-visual-design** — agency-grade fonts/spacing/shadows. Primary for system polish.
- **design-taste-frontend** — strict metric-based UI rules. Use to enforce rhythm/spacing consistency.
- **emil-design-eng** — animation/interaction polish (easing, restraint). Use to keep motion tasteful, not decorative.
- **stitch-design-taste** — semantic DESIGN.md discipline. Use to keep components token-driven and consistent with DESIGN.md.
- **image-to-code** — when working from the prototype images / target compositions.
- **minimalist-ui / impeccable** — editorial clarity passes and audits.
Skills serve the contract. A skill's taste never overrides DESIGN.md's frozen tokens, primitive (squircle), no-glow rule, or motion doctrine.

## 3 · Stack & hard constraints (DESIGN.md §9)
- **Reveal.js + vanilla CSS + GSAP.** No React/Vue/Tailwind in the deck.
- **21st.dev guardrail:** inspiration only — reimplement any effect in vanilla CSS/GSAP against tokens; never import a React/Framer/Tailwind component. No live shaders on the critical path.
- **"3D"/luminous core:** pre-rendered PNG/MP4 or one Spline embed — never many live WebGL frames.
- **Demos:** embedded MP4 in the browser-frame component — never a live app.
- **Export `.pptx` fallback** for academic submission.
- **No glow on light — ever.** Depth = shadow / gradient / space.
- **Legibility scrim mandatory** under text over a visual.
- **DATASHOW LEGIBILITY (DESIGN.md v0.4):** every word legible from the back of a difficult-light room. Nothing below the ~16–18px floor (`--t-caption`). Use the full frame confidently. This is a hard gate on every slide.

## 4 · Build order (PHASE GATE — stop at each gate for review)
**A · Foundation.** Scaffold Reveal.js. `tokens.css` from DESIGN.md §13 verbatim (the clamp() type scale — keep the px floors). Wire Space Grotesk + Inter + IBM Plex Mono. Set up GSAP. Deliver blank themed deck + one "hello" slide proving tokens/fonts/floors load. **GATE.**

**B · Component library (BEFORE slides).** Standalone `components.html` rendering every DESIGN.md §6 component against tokens: squircle tile (teal/amber/steel) · chapter-index row (label-above-title, never inverted) · luminous core (placeholder, mark for pre-render) · scatter field · legibility scrim · lifecycle rail · service-layer iso stack (NOT the agenda) · Copilot path diagram (red protected-exit) · demo browser frame · bracket CTA + corner ticks + section chrome (section label / subsection slider). **GATE — review gallery before any slide.**

**C · Opening + 5-slide prototype.** Build the **opening sequence explicitly**: 0.1 formal title · 0.2 animated scattered RFQ world · 0.3 gravity-collapse hook (anchor #1) · 0.4 seven-step agenda. Plus one section-opener (Step 05 · RFQ Copilot, with section label + subsection slider). Use gpt-taste for the collapse motion. Match prototype *intent*, exceed prototype *quality*. **GATE — make-or-break review.**

**D · One full section.** All sub-slides of Step 05 · RFQ Copilot (Contextual Entry → Path-Based Architecture → Protected Exit Paths → Demo Glimpse), incl. the embedded demo frame. Proves the system across a real section. **GATE.**

**E · Full deck.** Expand to all seven steps per blueprint.html timing. Export `.pptx` fallback. Run the §9 perf rehearsal on the actual presentation hardware.

## 5 · Reconnaissance rule (before any code)
Read DESIGN.md and blueprint.html fully; open the three prototypes. State back: the token set + legibility floor, the squircle primitive, no-glow rule, scrim rule, the seven steps with their thematic labels, and the 3× hook anchor arc. Only then start Phase A.

## 6 · Recurring hook (blueprint.html)
Verbatim: **"The real RFQ risk is losing control before the quotation is ready."** Anchored 3×: open (0.3, problem) → Backbone→Copilot transition (shown solved) → close (07, resolved). One line, one arc. Don't introduce competing slogans.

## 7 · Content honesty
All on-slide numbers/data are real (IF-25144 workbook / SA-AYPP-6-MR-022) or an obvious placeholder token — never an invented figure. Honest cold-start scoping; one golden reference pair; no overclaiming coverage.

## 8 · What NOT to do (DESIGN.md §10)
Glow on light · dark slides · React/Framer/Tailwind imports · live shaders/WebGL on critical path · mascot or "assistant object" · amber = risk (risk is red) · mixing hexagon+squircle (squircle only) · text over visual without scrim · text below the legibility floor · animated bullets/validation/limits · generic blue SaaS gradient · reproducing prototypes pixel-for-pixel instead of building to production quality.
