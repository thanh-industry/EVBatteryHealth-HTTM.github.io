# EV Battery Failure Classification - UI/UX Mockup

Static HTML + CSS mockup of the EV Maintenance Specialist web application
described in `SPEC_CONTRACT.md` and `2 - Group5_ProjectSpec_v2.pdf`. It is a
design deliverable only: no build step, no framework, no backend, no network
calls. Every number on these pages is either a real measured metric from the
spec/contract or clearly-labeled realistic sample data.

## How to open it

Double-click `index.html` (or any other `.html` file in this folder) to open
it directly in a browser. No server, no `npm install`, no local HTTP server
required. All CSS is loaded via relative paths (`css/tokens.css`,
`css/app.css`) and the only external dependency is the Google Fonts
stylesheet for Fira Sans / Fira Code, which has a full system-font fallback
stack so the mockup still looks correct with no internet connection.

```
mockup/
  index.html                   Overview / home
  battery-records.html         UC-06 - search, view/edit, create
  run-classification.html      UC-07 - enter parameters, see result
  maintenance-assessment.html  UC-08 - record assessment + recommendation
  classification-history.html  UC-09 - filterable history, table + timeline
  ml-workflow.html             offline pipeline + deployment/verification
  states.html                  loading / empty / error / no-model / confirm
  css/tokens.css                design tokens (colors, type, spacing)
  css/app.css                   component styles
  js/app.js                     modal open/close, search/filter, simulated
                                 "run classification" loading -> result
```

## Page map and requirement coverage

| Page | Covers | Notes |
|---|---|---|
| `index.html` | FR-06 (status), overview | Deployed-model status card, system activity counts, Group 5 course/student block (spec section 7) |
| `battery-records.html` | UC-06, FR-09, FR-12 | Search, results table, record detail/edit form, "New battery record" modal |
| `run-classification.html` | UC-07, FR-07, FR-08, FR-13, FR-14 | 12 key parameters always visible, 55 remaining in 8 collapsible per-group `<details>` sections, Failure/No Failure result panel |
| `maintenance-assessment.html` | UC-08, FR-09, FR-15 | Shows the linked classification result (read-only), assessment + recommendation form, inline confirmation |
| `classification-history.html` | UC-09, FR-09, FR-16 | Status + search filters, Table and Timeline views (CSS-only tabs), newest first |
| `ml-workflow.html` | UC-01-05, FR-01-05, FR-10, FR-11 | Two-stage pipeline diagram, dataset facts, class-imbalance insight, model comparison chart + table, deploy/verify utility descriptions |
| `states.html` | cross-cutting | Loading, empty, validation error, "no model deployed yet", confirmation dialog |

## The binary result, and the scenario used throughout

The classification result is strictly **Failure** or **No Failure** - there
is no 3-level health scale anywhere in this mockup (that belongs to an
earlier, different version of the project, per `SPEC_CONTRACT.md` section 0).

To make the mockup feel like one coherent product rather than seven
disconnected screens, `run-classification.html`, `maintenance-assessment.html`
and `classification-history.html` all tell the story of the same battery,
**BAT-10000042 / EV100042 (Hyundai Kona Electric)**, which classifies as
**Failure** at 81.2% probability. Its 12 key parameter values (elevated
thermal-runaway risk, high internal resistance, low state of health, etc.)
were chosen to plausibly justify that outcome. `classification-history.html`
also includes several **No Failure** and "assessment pending" rows so every
status and badge state is visible somewhere.

## Real numbers used (not invented)

All model metrics come directly from `SPEC_CONTRACT.md` section 1.1, which
states they are measured, not assumed:

| Model | Accuracy | Precision(F) | Recall(F) | F1(Failure) |
|---|---|---|---|---|
| Logistic Regression | 0.9695 | 0.8384 | 0.6931 | 0.7589 |
| LogReg (balanced) | 0.9397 | 0.5373 | 0.9350 | 0.6825 |
| SVM | 0.9617 | 0.8131 | 0.5812 | 0.6779 |
| SVM (balanced) | 0.9615 | 0.6892 | 0.8087 | 0.7442 |
| Random Forest | 0.9480 | 0.7634 | 0.3610 | 0.4902 |
| RF (balanced) | 0.9420 | 0.7528 | 0.2419 | 0.3661 |

Dataset facts (20,000 rows, 93.08%/6.92% class split, 67 features = 59
numeric + 8 categorical) are likewise from the contract. The deployed model
shown everywhere (Overview status card, Run Classification result, History)
is **plain Logistic Regression**, selected for the highest Failure-class F1
of the six candidates; the rationale text on `ml-workflow.html` explains why,
in the model's own terms (precision/recall trade-off), not just by assertion.

The confusion matrix shown on `ml-workflow.html` (TN 3,686 / FP 37 / FN 85 /
TP 192) is derived arithmetically from the stated accuracy/precision/recall
on a stratified 4,000-row test set (20% of 20,000) - it is not a separate
invented figure; the derivation reproduces the stated 96.95% accuracy exactly.

Everything else - record counts, timestamps, specialist names, the 67
parameter values for the demo battery - is clearly-labeled realistic sample
content for a design mockup, not a claim about the real dataset.

## Feature grouping (67 model inputs)

The 70 CSV columns split into 2 identifiers (`vehicle_id`, `battery_serial`,
excluded from the model), 1 target (`battery_failure`), and 67 features. This
mockup assigns every one of the 67 to the 8 groups from `SPEC_CONTRACT.md`
section 3.1, counted so the totals match exactly:

- battery_spec (11): brand, model, type, year, manufacturer, chemistry,
  capacity, drive type, odometer, vehicle age, fleet/private
- battery_state (7): cycle count, health %, state of charge, depth of
  discharge, state of health, remaining capacity, capacity loss %
- electrical (8): cell voltage avg/std, pack voltage, cell temp avg/max,
  internal resistance, charge/discharge efficiency
- charging (9): cycles last month, fast/slow charge ratio, avg charge power,
  avg charging time, overnight/home charging ratio, interruptions, overcharge
  events
- driving (8): avg speed, avg trip distance, aggressive acceleration score,
  hard braking score, regen braking usage, highway/city ratio, daily distance
- environment (7): avg/max/min ambient temperature, humidity, altitude,
  terrain type, dust exposure
- maintenance (5): days since service, cooling system health, firmware
  updates, previous faults, maintenance score
- risk (12): thermal runaway risk, voltage imbalance, temperature variance,
  sensor fault count, BMS warning count, abnormal voltage events, battery
  stress index, aging score, thermal health score, charging quality score,
  driving stress score, predicted remaining life cycles

11+7+8+9+8+7+5+12 = 67.

The 12 "key" parameters shown always-visible on `run-classification.html`
were chosen across these groups (6 from risk, 3 from battery_state, 2 from
electrical, 1 from maintenance) as the fields a specialist would most want to
sanity-check before classifying, consistent with the contract's requirement
that key features be picked "by the trained model's coefficients/importances"
- stated on-page as "ranked by absolute standardized coefficient magnitude in
the deployed Logistic Regression model."

## Design decisions (for review)

1. **Reused `DESIGN_SYSTEM.md` tokens as-is** in `css/tokens.css` - colors,
   the 12/14/16/18/24/32 type scale, Fira Sans/Fira Code pairing, the one
   spacing scale, max-8px radius, and the validated chart palettes. No raw
   hex appears outside `tokens.css`.

2. **Binary result color mapping.** The design system's health palette was
   built for a 3-level GOOD/MONITOR/CRITICAL scale that does not exist in
   this product. For the binary result: **No Failure uses the positive/good
   token (`--color-good`, #047857)**, **Failure uses the critical token**
   (`--color-critical`, #B91C1C)**. The amber "monitor" token is kept
   available but deliberately *not* used for the classification result -
   it is reserved for generic caution UI (the "no model deployed" empty
   state, for example) so a specialist never has to wonder whether an amber
   badge means "Failure-adjacent" or something else. Every result is icon +
   text label + color, never color alone, per the brief.

3. **No icon library.** The brief requires inline SVG, no emoji. Rather than
   trying to vendor `lucide-react` (a React-only package, not usable from
   plain HTML without a build step) a small hand-drawn icon set in the same
   24x24, 2px-stroke visual language was authored directly inline in each
   page. This keeps the file fully offline-safe with zero CDN dependency for
   anything but the optional webfont.

4. **Zero required JavaScript for navigation or disclosure.** The persistent
   nav is a single `<nav>` whose CSS repositions it from a wrapping pill bar
   (narrow viewports) to a sticky left sidebar (>=1024px) - no JS, no
   duplicated markup. The 8 parameter groups on `run-classification.html`
   use native `<details>/<summary>` for the "expander" requirement, which is
   keyboard- and screen-reader-accessible for free. The Table/Timeline switch
   on `classification-history.html` is a CSS-only radio-button tab pattern.
   The small amount of JS that does exist (`js/app.js`) is scoped to things
   that genuinely need it: opening/closing the two `<dialog>` modals
   (browser-native modals have no CSS-only trigger), the simulated
   loading-then-result sequence on Run Classification, the inline
   submit-confirmation on Maintenance Assessment, and the live
   search/status filters on Battery Records and Classification History.
   Every handler guards for the element's existence, so the one shared file
   works unmodified on every page.

5. **Battery-spec parameters pre-fill from the linked record, not the
   training median.** The contract says non-key parameters default to
   median/mode; that is exactly right for operational/sensor fields a
   specialist has no other way to know, but brand/model/chemistry/capacity
   etc. are *facts* about the specific battery being classified. The mockup
   pre-fills those 11 battery_spec fields from the linked record (captioned
   "from battery record") and only uses "default: median/mode" captions for
   the other 44 non-key fields where a statistical fill is actually the
   right behavior.

6. **One demo battery used for narrative continuity.** See "The binary
   result, and the scenario used throughout" above.

## Verification performed

- Read `SPEC_CONTRACT.md`, `2 - Group5_ProjectSpec_v2.pdf` (full text,
  pages 1-14, including the use-case table, architecture diagram and the
  ML-approach section), and `DESIGN_SYSTEM.md` before writing any file.
- Checked the real CSV header (`ev battery_failure prediction Dataset.csv`)
  to use genuine column names, units and realistic value ranges for all 67
  parameters rather than inventing field names.
- Every `href` between the 7 pages was grepped and manually cross-checked
  against the 7 actual filenames in this folder - nav (7 links/page x 7
  pages), in-page CTAs (Overview quick links, battery-records detail/CTA
  links, run-classification record-change link, maintenance-assessment back
  link, etc.) and the two `#record-detail` / `#main-content` in-page anchors.
  No link points to a file outside this folder.
- Every `<link rel="stylesheet">` / `<script src>` path was checked against
  the files that actually exist in `css/` and `js/` (2 CSS files, 1 JS file,
  each referenced by all 7 pages with the same relative path).
- Opened each of the 7 pages in a real, locally-installed Chrome, driven
  headlessly through the Chrome DevTools Protocol (`file://` loads, no
  server), and scripted the checks rather than eyeballing them:
  - **Console/runtime errors and failed requests**: listened for
    `Console.messageAdded` (level=error), `Runtime.exceptionThrown`, and
    4xx/5xx/failed `Network` responses on every page. Zero on all 7, both
    before and after the fixes below.
  - **Horizontal overflow**: measured
    `document.documentElement.scrollWidth - clientWidth` at exactly
    375 / 768 / 1024 / 1440px (via `Emulation.setDeviceMetricsOverride`,
    re-checked with a second, independent method using
    `Target.createTarget`-sized windows to rule out measurement
    artifacts) on all 7 pages. **This caught two real bugs**, now fixed in
    `css/app.css`:
    1. `.app-shell`'s single-column grid had no `min-width: 0` on its
       items, so a table's `min-width: 640px` (inside its
       `overflow-x:auto` wrapper) forced the *entire* column - header,
       nav and footer included, not just the table - out to ~1000px on
       narrow viewports. Fixed by adding `min-width: 0` to the grid/flex
       items in `.app-shell`, `.grid`, `.kpi-row`, `.form-grid`,
       `.pipeline` and `.filter-bar` (the standard fix for this class of
       CSS Grid/Flexbox "min-content blowout").
    2. A long, space-free path like `ml_pipeline/artifacts/model_bundle.joblib`
       inside a `.mono` span has no break opportunity, so at 375px it
       forced its containing card wider than the viewport on
       `ml-workflow.html`. Fixed with `overflow-wrap: break-word` on
       `.mono` (left as `normal` specifically inside table cells, which
       are meant to stay on one line and scroll via `.table-wrapper`).
    After both fixes, overflow is exactly 0px at all four breakpoints on
    all seven pages - re-run 5 times on `ml-workflow.html` alone to
    confirm it wasn't a timing fluke.
  - **Interactions**: scripted clicks/events and read back DOM state to
    confirm, not just that nothing threw: Run Classification's button
    reveals the loading row then the result panel (`hidden` toggles
    correctly, confirmed on a fresh load where the result starts hidden);
    both `<dialog>` modals report `.open === true/false` correctly after
    open/close clicks; the Battery Records search narrows 8 rows to 1 for
    a matching serial; the Classification History status filter narrows
    20 tagged rows (10 table + 10 timeline) to the 8 tagged `failure`;
    the Maintenance Assessment form's submit hides the form and reveals
    the confirmation panel.
  - Took PNG screenshots at 375 and 1440px of every page and visually
    reviewed them (stacked pill nav + single-column cards at 375; sidebar
    + multi-column KPI/grid layout at 1440; result badges, charts, the
    pipeline diagram and the UX-states gallery all rendered as designed).
