# Edit Guide — Itqān deck

A short manual so you can adjust text, colors, sizes, and spacing yourself without pinging me.

---

## 1 · The workflow (every edit is the same 4 steps)

1. **Open the file** in your IDE (VS Code, etc.)
2. **Find the thing** (Ctrl+F to search the text or class name)
3. **Change the value**, then save (Ctrl+S)
4. **Refresh the browser** (Ctrl+R · use Ctrl+Shift+R for a hard refresh if a CSS change doesn't show up)

That's it. No build step. No compile.

---

## 2 · Folder map

```
presentation_deck/deck/                   ← the production deck lives here
├── index.html                            ← THE 5 SLIDES (title, scatter+hook, agenda, section opener)
├── components.html                       ← Phase B review page (the component library)
├── preview.html                          ← single-slide preview at projector scale (for testing)
│
├── css/
│   ├── tokens.css                        ← the design DNA: colors, fonts, sizes (edit here once → everywhere updates)
│   ├── base.css                          ← shared chrome on every slide: corner ticks, brand, section labels, page numbers, bottom meta
│   ├── components.css                    ← reusable pieces: squircle tile, chapter index, lifecycle rail, Copilot path, etc.
│   ├── slides.css                        ← slide-specific composition (currently mostly the title slide)
│   └── gallery.css                       ← only used by components.html (the review page)
│
├── js/
│   └── main.js                           ← Reveal.js config + intro animation + page-number logic
│
├── vendor/
│   └── img/                              ← drop ENET'COM and BACAB logo files here when ready
│
└── EDIT_GUIDE.md                         ← you are here
```

---

## 3 · "I want to..." recipes

### Change a piece of text

All visible text lives in `index.html`. Search (Ctrl+F) for the current text and replace it.

| What you want to change | Search for | Where |
|---|---|---|
| The big title | `Itq` then look for `An RFQ Lifecycle` | `index.html` |
| The eyebrow above the title | `Final-Year Engineering Project` | `index.html` |
| The subhead under the title | `Designing operational control` | `index.html` |
| Author name | `Mohamed Guidara` | `index.html` |
| Academic supervisor | `Boukthir Haddar` | `index.html` |
| Industrial supervisors | `Omar Abid · Omar Baccar` | `index.html` |
| Defense day (the big amber number) | `<span class="day">20</span>` | `index.html` |
| Defense month/year | `<span class="ymd">June 2026</span>` | `index.html` |
| ENET'COM logo placeholder text | `ENET'<span class="accent">COM</span>` | `index.html` |
| BACAB logo placeholder text | `BACAB` | `index.html` |
| Bottom meta line | `Gulf Heavy Industries` | `index.html` (4 places — Find & Replace All) |
| Agenda headline | `From scattered RFQs` | `index.html` |
| Hook phrase (slide 0.3) | `The real RFQ risk` | `index.html` |
| Section 05 headline | `The LLM understands language` | `index.html` |

### Change spacing (move something up or down)

Spacing lives in CSS files. The keywords are `margin` and `padding`.

> **Quick rule:** `margin: top right bottom left`. So `margin: 0 0 80px;` means top=0, sides=0, **bottom=80px**.

For the title slide, all edit points are in `css/slides.css`. I've marked the most-edited values with `/* ↓↓↓ EDIT: ... */` comments — open `slides.css` and search for `EDIT` to jump between them.

The four most useful ones on the title slide:

| Want to change... | File | Search for | Current value |
|---|---|---|---|
| Gap between title and subhead | `slides.css` | `.title-slide h1 {` | `margin: 0 0 20px;` |
| Gap between subhead and HOSTED BY pill | `slides.css` | `.title-subhead {` | `margin: 0 0 80px;` |
| Gap between eyebrow and title | `slides.css` | `.title-eyebrow {` | `margin-bottom: 36px;` |
| Gap from credits row down to the GHI meta line | `slides.css` | `.title-slide {` | `padding: 64px 96px 128px;` (last value is bottom) |

To make a gap **bigger**, increase the number (`80px` → `100px`).
To make a gap **smaller**, decrease the number (`80px` → `60px`).

### Change a color

All system colors are stored as named variables in `css/tokens.css`. The most useful ones:

| Variable | What it is |
|---|---|
| `--amber-on-light` | The warm orange used for the `ā` accent and the labels (`AUTHOR`, `ACADEMIC SUPERVISOR`...) |
| `--amber-500` | The bright amber used in the gradient corners and the page-number current digit |
| `--teal-900` | The dark teal used for the eyebrow and the dot in the meta line |
| `--l-ink` | The main dark text color (almost-black) |
| `--l-muted` | The muted gray text (used for subhead, meta line) |
| `--l-bg` | The cream background |

**To change ONE thing's color:** edit its CSS rule, find `color:`, point to a different variable.
Example — make the subhead darker:
```css
.title-subhead {
  color: var(--l-ink);   /* was var(--l-muted) — now full ink black */
  ...
}
```

**To change a color EVERYWHERE in the deck:** edit `tokens.css`, change the hex value next to the variable. Every place that uses it updates at once.

### Make text bold (or lighter)

Find the CSS rule for the element, and edit `font-weight:`:

| Value | What it looks like |
|---|---|
| `400` | Normal (default) |
| `500` | Medium |
| `600` | Semibold |
| `700` | Bold |

Example — make the subhead bold:
```css
.title-subhead {
  font-weight: 700;   /* was 400 */
  ...
}
```

### Resize text

Text sizes are tokens in `tokens.css`. **Never use a custom px value** — pick from the existing tokens so the floor stays honest.

| Token | Size | Used for |
|---|---|---|
| `--t-hook` | 90px | Opening hook headline |
| `--t-h2` | 64px | The big title on most slides |
| `--t-h3` | 40px | Sub-headers (agenda titles, etc.) |
| `--t-sub` | 28px | Subhead, body |
| `--t-kicker` | 24px | The eyebrow (small uppercase teal) |
| `--t-chrome` | 22px | Chrome (section label, brand, slider) |
| `--t-caption` | 20px | **The floor — smallest text allowed anywhere** |

To resize an element, change its `font-size:` to a different token:
```css
.title-subhead {
  font-size: var(--t-sub);    /* change to --t-kicker for smaller, or --t-h3 for bigger */
}
```

**⚠ Hard rule: never go below `--t-caption` (20px).** It will become unreadable on the defense projector.

### Add the ENET'COM and BACAB logo files

1. Save the logo files into `presentation_deck/deck/vendor/img/` as `enetcom.svg` (or `.png`) and `bacab.svg` (or `.png`).
2. Open `index.html`, search for `ENET'COM`. Replace the placeholder block:
   ```html
   <span class="logo-mark">ENET'<span class="accent">COM</span></span>
   <span class="logo-sub">Sfax</span>
   ```
   …with:
   ```html
   <img src="vendor/img/enetcom.svg" alt="ENET'COM">
   ```
3. Do the same for BACAB.
4. Refresh.

The CSS already constrains `<img>` to a sensible max-height (96px), so the logos will resize automatically.

---

## 4 · Title-slide cheat sheet (one place for the most common tweaks)

| What you see on the slide | File | Search for | What controls it |
|---|---|---|---|
| `ENET'COM SFAX` mark, top-left | `slides.css` | `.title-logo-slot` | size + position |
| Academic header (3 lines centered top) | `slides.css` | `.title-academic-header` | font / spacing |
| `BACAB CONSULTING` mark, top-right | `slides.css` | `.title-logo-slot.right` | position alignment |
| `FINAL-YEAR ENGINEERING PROJECT · 2026` | `slides.css` | `.title-eyebrow` | color, size, gap to title |
| Big title (`Itqān: An RFQ Lifecycle...`) | `slides.css` | `.title-slide h1` | font, weight, gap to subhead |
| Subhead (`Designing operational...`) | `slides.css` | `.title-subhead` | gap to host pill |
| `HOSTED BY BACAB Consulting` pill | `slides.css` | `.title-host-line` | border, background, padding |
| AUTHOR · ACADEMIC SUPERVISOR · ... row | `slides.css` | `.title-credits` | column gap, internal lines |
| The `20 JUNE 2026` date plate | `slides.css` | `.title-credits .cell.date-cell` | day size, month-year style |
| The `01 / 04` page number, bottom-right | `base.css` | `.page-num` | font, color, position |
| Bottom meta line (`Gulf Heavy...`) | `base.css` | `.meta` | font, color |
| Ambient background orb | `slides.css` | `.title-ambient` | size, blur, opacity |
| The corner gradients (amber + teal) | `slides.css` | `.title-slide { background:` | the 3 `radial-gradient(...)` lines |

---

## 5 · Things you should NOT do

- **Don't go below 20px font size.** The defense projector will eat smaller text.
- **Don't add `text-shadow` or `box-shadow: ... rgba(...glow...)` to text.** DESIGN.md anti-pattern #1: no glow on light slides.
- **Don't paste hex colors directly into CSS.** Always use a token from `tokens.css` (`var(--amber-500)` etc.) so the system stays consistent.
- **Don't add new fonts.** Three families only: Space Grotesk (display), Inter (body), IBM Plex Mono (chrome).
- **Don't put images that need internet to load on slides** — anything we ship must work offline. Logos go in `vendor/img/`, not as URLs.

---

## 6 · When to ping me

You can do these yourself:
- Edit any text
- Move things up/down (spacing)
- Change a color or weight
- Resize text (within the tokens)
- Drop in logo files
- Fix typos

Ping me for:
- Adding a brand-new slide or component
- Changing motion (the gravity-collapse, the title intro cascade)
- Anything that touches the JS in `main.js`
- Layout that doesn't fit the existing tokens (e.g. "I want a totally different agenda style")
- Anything you're not sure about — never break the slide trying to fix it

---

## 7 · Reading the inline comments

In `slides.css` I've marked the most common edit points with this pattern:

```css
/* ↓↓↓ EDIT: this is the gap between X and Y. Bigger = more space. */
margin: 0 0 80px;
```

Search `EDIT:` in `slides.css` to jump to all of them.
