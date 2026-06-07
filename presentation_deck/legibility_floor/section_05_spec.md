# Section 05 — THE BOUNDARY · Build Spec

**For:** Claude Code (deck build) · **Status:** Content locked · **Theme:** amber
**Companion to:** blueprint.html (narrative contract) · DESIGN.md (visual contract)

This file is the **content contract** for Section 05. Claude Code builds the Reveal.js
slides *from* this spec. Do not redesign the narrative or rewrite the scripts — build them
well, in line with DESIGN.md. Where this spec and DESIGN.md disagree on visuals, DESIGN.md
wins; where this spec defines *what a slide says and why*, this spec wins.

---

## 0 · Global rules for this section (apply to every slide)

1. **Jury is francophone.** On-slide text and spoken scripts use **simple English**: short
   sentences, plain verbs, common words. Prefer cognates (control/contrôle, access/accès,
   truth/vérité). Avoid false friends and idioms. The depth lives in the *ideas*, not in
   hard vocabulary.
2. **Terminology — frozen, three words, three jobs:**
   - **copilot** = the whole system that was built (pipeline + factory + gates + the model).
     Use it when naming the achievement ("this copilot", "a controlled copilot").
   - **the model** = the language model *inside* the copilot — one component, helps at the
     edges only. Use it when talking about the AI part being constrained.
   - **GPT** = used **only** in the 05.1 headline, on purpose, to evoke the naive instinct.
     Never elsewhere.
   - Never call the model "the copilot" — that collapses the section's whole argument.
   - "the system" = acceptable neutral term for the whole copilot (used in scripts).
3. **Three frozen labels:** `TRUTH · ISOLATION · AUTHORITY`. They appear as the three risk
   tiles in 05.1 and as the three closure ticks in 05.3 — **identical wording, identical
   order, matching visual treatment**, so the jury feels each danger close.
4. **Visual constraints (DESIGN.md):** no glow on light; datashow-legible from the back of a
   difficult-light room; nothing below the caption floor; use the full frame.
5. **Section budget:** ~3:00 spoken (35 + 40 + 75 + 50s). The demo is **not** in this section
   — it lives in Section 07. Section 05 is the intellectual climax: architecture and control.

---

## 05.1 — The Chatbot Trap · 35s · amber

**Load-bearing claim**
A language model connected directly to RFQ data is dangerous — not only because it can be
wrong, but because it can break control in three ways: truth, isolation, and authority.

**On-slide**
- Headline: **Why not just connect GPT to the RFQ data?**
- Three tiles (name · plain line · label):
  - **Invented facts** — it gives facts the system never gave · `TRUTH`
  - **Mixed RFQs** — data from one RFQ appears in another answer · `ISOLATION`
  - **Access problem** — it shows an RFQ the user may not see · `AUTHORITY`

**Spoken (~35s · ~80 words)**
> "The easy way to add AI here would be to connect a language model directly to the RFQ data and
> let it answer. But the danger is not only that it can be wrong. The model can give facts the
> system never gave. It can mix data from two RFQs. And if access is not controlled by code, it
> may show an RFQ the user is not allowed to see. Three problems, one cause: the model would have
> power it should never have."

**Decision valorized**
I rejected the normal "AI on the database" design. In this RFQ context, a model that controls
facts, RFQ separation, and access is a danger, not a feature.

**Setup / payoff**
Plants the three axes — `TRUTH · ISOLATION · AUTHORITY`. Each is closed by a deterministic
owner in 05.3 (facts checked → truth; per-target separation → isolation; access by code →
authority). The three tile labels here must look identical to the three closure ticks there.

**Visual direction**
Show the model as powerful but uncontrolled: one direct arrow, **GPT → RFQ DATA**, nothing in
between. The *missing* checkpoints are the argument. This is the "before" picture; 05.3 is the
"after". Three tiles only. No glow, datashow-legible.

---

## 05.2 — The Copilot Inversion · 40s · amber

**Load-bearing claim**
The model is kept for what it does well — understanding the question and helping write the
answer — but removed from the decisions that matter. The platform controls facts, access, and
execution.

**On-slide** *(principle slide — keep it almost empty; headline huge and alone)*
- Headline: **The model proposes. The platform decides.**
- Support line: *The model reads and writes. The platform controls facts, access, and execution.*
- Small tag: *chatbot → copilot*

**Spoken (~40s · ~80 words)**
> "So how do we keep the power of the model without giving it control? We change its role. In a
> simple chatbot, too much is left to the model. In this copilot, the model has a safer role. It
> reads the question and helps write the answer. But it never decides what is true. It never gives
> access. It never builds the execution plan. The model proposes. The platform decides."

**Decision valorized**
I separated language from authority. The model keeps its strength — reading and writing
naturally — but the platform keeps control over facts, access, and execution.

**Setup / payoff**
Pays off "not a chatbot". States the principle; 05.3 makes it concrete with named owners. The
phrase "never builds the execution plan" is a deliberate teaser — 05.3 reveals the one component
that *does* (the ExecutionPlanFactory). Do not name it here.

**Visual direction**
Before/after inversion. **Left (chatbot):** the model in the center, arrows out to facts,
access, tools, execution — it is the brain. **Right (copilot):** the model moved to the side,
small, feeding only "language" into a solid platform core that holds every decision. The
argument is purely positional: center → edge. Headline huge and alone; this is not a
diagram-heavy slide. The jury should leave remembering one sentence. No glow.

---

## 05.3 — The Trust-Boundary Architecture · 75s · amber

**Load-bearing claim**
The copilot is one controlled pipeline. The model helps at the edges — reading the question and
writing the answer. The important decisions in the middle are made by code. Only one component
can build the plan that runs, and this rule is checked automatically by tests.

**On-slide**
- Headline: **The model works inside a controlled pipeline.**
- Four phase boxes (left → right):
  1. **UNDERSTAND** — read the question · *model helps here*
  2. **CONTROL THE PLAN** — build the plan that runs · *one component only · checked by tests*
     · small code label: `ExecutionPlanFactory`
  3. **USE REAL DATA** — check access · get real facts
  4. **WRITE A SAFE ANSWER** — write · verify · deliver · *model helps here*
- Three closure ticks placed on phases 3–4: `TRUTH ✓` `ISOLATION ✓` `AUTHORITY ✓`

**Spoken (~75s · ~135 words)**
> "Here is the copilot as one controlled pipeline. First, the system understands the question.
> The model helps here. Second, the system builds the plan that will run. This is the key step:
> only one component can build this plan, and this rule is checked automatically by tests. Third,
> the system uses real data. It checks access, then gets real facts from the platform. Fourth,
> the system writes and verifies the answer.
>
> So the model helps at the edges: it reads, then it writes. But the middle is controlled by
> code: plan, access, and data. This closes the three risks: truth is checked, RFQs stay
> isolated, and authority stays in the platform."

**Decision valorized**
I did not rely on model discipline — I built a controlled pipeline. One component builds the
execution plan (CI-enforced), policy is centralized in configuration, access is checked by code,
and answers are verified before delivery. Control is part of the system, not a promise.

**Setup / payoff**
Pays off 05.1 (the three axes close here) and 05.2 (the "never builds the plan" teaser is
answered: one component does, and only it). Shows **only the success path**; unsafe cases are
held for 05.4.

**Visual direction**
Four large boxes, left → right. Deterministic code is the dominant color and fills the middle
two phases completely. The model (a different, lighter color) appears **only** as a small helper
in box 1 and box 4 — never in the middle. That contrast *is* the argument. Box 2 carries a small
lock / "checked by tests" tag and the small `ExecutionPlanFactory` code label (proves depth
without weight — not in the headline). The three closure ticks match the 05.1 tiles exactly.
**Do not** draw the escalation loop or the 15 stages here. No glow, datashow-legible.

**Backup slide (Q&A only):** the full 15-stage pipeline diagram (FastIntake → … → Persist, with
the Escalation Gate loop and Path Registry). If a juror asks "concretely, how?", reveal it:
"each of these four phases is a real pipeline — here it is in full." The clean version sells the
idea; the detailed version proves the simplification was a choice, not a limit.

---

## 05.4 — Failure Is Also Designed · 50s · amber

**Load-bearing claim**
Control is not only about good answers. When the system cannot answer safely, it does not guess.
Each unsafe case has a planned, safe answer.

**On-slide**
- Headline: **When it cannot answer safely, it does not guess.**
- Small two-column table:

  | The situation | What the system does |
  |---|---|
  | The request is not supported | It says so clearly |
  | The request is outside the RFQ scope | It says so and redirects |
  | The target RFQ is not clear | It asks one question |
  | The RFQ is missing or not allowed | It stops |
  | There are not enough facts | It refuses to invent |

- Principle line: *One gate catches the problem. The answer is planned.*

**Spoken (~50s · ~100 words)**
> "Control is not only about good answers. It is also about what happens when the system cannot
> answer safely. In a simple chatbot, this is the dangerous moment: it may guess. Here, each
> unsafe case has a planned answer. If the request is not supported, the system says so. If it is
> outside the RFQ scope, it redirects. If the RFQ is not clear, it asks one question. If the RFQ
> is missing or not allowed, it stops. If there are not enough facts, it refuses to invent. Even
> when the system cannot answer, control is still there."

**Decision valorized**
I treated unsafe cases as designed paths, not as random errors. A single deterministic gate (the
Escalation Gate) catches problems from any step of the pipeline and routes them to safe, planned
answers. The system does not improvise when the answer is risky.

**Setup / payoff**
Closes the section. No demo bridge (the demo is in 07). The final beat — "even when the system
cannot answer, control is still there" — is the hook payoff. It hands to Section 06: now that
control is built, how does it feel for the user?

**Visual direction**
A calm two-column table: situation left, safe behavior right. Do **not** make it look like an
error screen — these are controlled exits, not alarms. A small node can collect the five rows
into one "safe answer" exit; label it lightly as "Escalation Gate". No glow, datashow-legible.

**Backup slide (Q&A only):** Path 8 / Escalation Gate detail — the five reason codes (8.1–8.5),
`build_from_escalation`, the templated finalizer. Reveal if a juror asks how failure routing
works concretely.

---

## Section-level notes

- **Arc check:** 05.1 danger → 05.2 role change → 05.3 architecture → 05.4 control in failure.
  Each card hands to the next with a reason, not a topic change.
- **Hook:** "the real RFQ risk is losing control before the quotation is ready" is resolved
  across this section; 05.4's closing line is its payoff.
- **Transition out:** Section 06 opens on "now that control is built, how does it feel to use?"
  Section 07 opens with the demo bridge: "the proof is not whether the copilot can talk — it is
  whether it stays controlled while answering real RFQ questions."
- **Backups:** two Q&A-only slides (full 15-stage pipeline; Path 8 detail). Build them but keep
  them out of the linear flow.
