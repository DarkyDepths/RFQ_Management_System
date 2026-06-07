# Section 04 — THE EVIDENCE · Build Spec

**For:** Claude Code (deck build) · **Status:** Content locked · **Theme:** per design system (DESIGN.md)
**Companion to:** blueprint.html (narrative contract) · DESIGN.md (visual contract)

This file is the **content contract** for Section 04. Claude Code builds the Reveal.js slides
*from* this spec. Do not redesign the narrative or rewrite the scripts. Where this spec and
DESIGN.md disagree on visuals, DESIGN.md wins; where this spec defines *what a slide says and
why*, this spec wins.

---

## 0 · Global rules for this section (apply to every slide)

1. **Jury is francophone.** On-slide text and spoken scripts use **simple English**: short
   sentences, plain verbs, cognates (platform/plateforme, package/paquet). No idioms, no false
   friends. Depth lives in the idea, not the vocabulary.
2. **This is a DESIGN / VISION section, not an achievement section.** The intelligence layer is
   *conception*; the only thing implemented today is deterministic workbook reading. The honesty
   discipline is satisfied **by tense and labelling, never by a disclaimer or a built-vs-designed
   table:**
   - Everything unbuilt (insights, KPIs, expected/best/worst cases, bid signals, briefings) is
     stated in **future tense** ("designed to", "the goal is", "as data grows") and/or visually
     **labelled as future**.
   - The **only** present-tense built claim allowed anywhere in this section:
     *"workbook data is already read and structured."* It is true, small, and not to be inflated.
   - **Do NOT** imply a finished knowledge base, that prediction/insights run today, or that
     history has already been loaded. There is no built-vs-designed comparison on any slide —
     that invites the jury to measure the small built thing against the big vision. Present the
     vision openly as designed, anchored on one working first step. Owned-as-conception = strong;
     conception-dressed-as-implementation = the trap.
3. **Theme color: per the design system (DESIGN.md).** Section 04's palette is the design
   system's call, not specified here.
4. **Visual constraints (DESIGN.md):** no glow, datashow-legible from the back of a difficult-light
   room, full frame.
5. **Section budget:** ~1:50–2:15 delivered (2 slides). **Short by design.** 05 is the climax; 04
   is the bridge between operational truth (03) and controlled use (05). Do not let it grow.

---

## 04.1 — Every RFQ Starts From Zero · ~50s

**Load-bearing claim**
GHI has deep estimating experience — but the platform doesn't reuse it. Every new RFQ package is
handled as if no similar job was ever quoted before.

**On-slide**
- Headline: **Every RFQ starts from zero.**
- A "scattered → blank" picture (see visual direction): past workbooks, old packages, expert
  know-how — scattered, faded, disconnected; a new package arrives; the team opens the **same
  blank workbook template** again.
- Key line (lower, in ink): *The problem is not experience. The platform cannot reuse it.*

**Spoken (~50s)**
> "GHI has years of estimating experience. The teams have already quoted many projects, for many
> clients. But when a new RFQ package arrives, the platform does not reuse this experience. There
> is no memory of similar RFQs, no lessons from past clients, no expected cost range, and no early
> signal about whether the project is worth bidding. The team opens the same blank workbook and
> starts again, almost from zero. So the problem is not a lack of experience. The experience
> exists. The problem is that the platform cannot reuse it."

**Decision valorized**
Recognizing that the real gap was not *missing* expertise but *un-reusable* expertise. That
reframing is what justifies an intelligence layer at all, instead of just another form to fill in.

**Setup / payoff**
Plants the gap. 04.2 answers it (turn scattered history into reusable memory). Same setup→payoff
structure as 05.1's danger: create the pain first, resolve it next.

**Visual direction** (the job, not the pixels)
Left/center: a loose scatter of artifacts — old workbooks, package folders, an "expert" mind —
disconnected, faded, no links between them. Right: a fresh package arriving, and a **blank**
workbook template opening.
**CRITICAL — visual hierarchy (do not invert):** the **blank workbook on the right must out-weigh
the scattered artifacts on the left.** The blank template is the payoff of the slide — the eye
must land there, on "they have all this past work but still restart blank." The natural instinct
is to make the scatter the hero because it's the busier visual; resist it. Scatter = faded
context; blank workbook = the focal point.
Calm, not alarmist. If the deck's intro "scattered RFQ world" motif exists, echo its visual
language here so it feels intentional. No glow, datashow-legible.

---

## 04.2 — Building Platform Memory · ~55s

**Load-bearing claim**
The intelligence layer starts turning past and new RFQ artifacts into reusable platform memory.
As data grows, each new package can arrive with insight instead of a blank page.

**On-slide**
- Headline: **Building platform memory.**
- Main flow (the hero): *Past RFQs + new packages + workbooks → structured memory → insight when a
  package arrives.*
- Future payoff cluster — **explicitly labelled** `Designed next, as data grows:`
  *expected case · best case · worst case · client & project signals · worth bidding?*
- Grounding line (small, lower): *Working foundation: workbook data is already read and structured.*

**Spoken (~55s · future tense for the vision)**
> "So the idea of the intelligence layer is to give the platform a memory. Past RFQs, client
> packages, and workbooks should not stay as isolated files. They should become structured data
> the platform can reuse. As this memory grows, the goal is that a new package no longer arrives
> to a blank page. It arrives with a briefing: expected, best, and worst cases, signals about the
> client and the project, and an early view of whether the project is worth bidding. This is the
> direction. It becomes stronger as more RFQs are added. And the foundation already starts today:
> the workbook data is read and structured. So the vision is ambitious, but it is anchored in a
> working first step."

**Decision valorized**
Designing the layer as a **compounding system** — every RFQ can enrich the next — rather than a
one-shot extraction feature. The value is in building memory over time, anchored on a working
deterministic foundation so the direction is real, not hand-waving.

**Setup / payoff**
Answers 04.1: the platform no longer has to stay blind to past work. Prepares 05: once the platform
holds trusted knowledge, you still cannot simply connect an AI to it — that knowledge must be used
with boundaries.
**Handoff line into 05.1 (deliver at the end of 04.2):**
*"The platform now starts to hold trusted knowledge. But we cannot just connect an AI to it. That
needs boundaries."* → lands on 05.1's "Why not just connect GPT to the RFQ data?"

**Visual direction** (the job, not the pixels)
A calm left-to-right flow showing scattered history **converging** into a single structured store,
then a new package arriving and receiving a briefing from it — the visual opposite of 04.1's blank
page.
**CRITICAL — visual hierarchy (do not invert):** the **main flow is the hero; the future-payoff
cluster must be visually SUBORDINATE and clearly read as future** (lighter, set apart, under the
`Designed next` label). The natural instinct is to make the exciting payoff (expected/best/worst,
worth-bidding) prominent — resist it. Prominent = overclaim. The grounding line stays small and
factual: present, never competing with the vision.
No glow, datashow-legible.

**Delivery note (for the presenter, not the build):** land "the foundation already starts today"
plainly — it's the line that anchors a minute of vision on solid ground. Don't rush past it.

---

## Section-level notes

- **Arc:** 03 operational truth → **04 document/history knowledge** → 05 controlled use of both.
  04 is the bridge that gives 05 its second source of trustworthy facts.
- **Handoff in (from 03):** dependency — confirm 03 ends in a way that sets up "there is also
  knowledge locked in past artifacts." If not, adjust 03's close when revisited.
- **Handoff out (to 05):** the locked line at the end of 04.2 → lands on 05.1. Must match exactly.
- **Honesty is the whole game here.** The single sharp-examiner question is "is the prediction
  implemented?" The answer is already on the slides: no — this section is the *design* of the
  intelligence layer; what runs today is deterministic workbook reading. Never claim more.
- **Backup (Q&A only):** workbook/package parser architecture, IF-25144 golden fixture, sheet
  extraction maps, cross-checks, confidence taxonomy, the four-pillar vision, cold-start seeding
  mechanism. Build none of this into the linear flow; it answers technical probes on demand.
