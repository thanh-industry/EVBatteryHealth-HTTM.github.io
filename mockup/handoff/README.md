# Engineering Handoff

This folder is the implementation-ready half of the UI/UX mockup. The app
screens one level up (`mockup/*.html`) show what the product looks like;
these seven pages document it precisely enough that a Software Developer can
build the real Streamlit application without guessing a pixel, a color, a
spacing value, or a validation message.

Open `index.html` first (double-click it, same as the rest of the mockup --
no server, no build step, no network).

## Files

```
mockup/handoff/
  index.html            Overview, how to use this section, table of contents
  design-tokens.html    Every tokens.css value as a live specimen + measured contrast
  components.html       Component anatomy + redlines (button, input, table,
                         result panel, chip, expander, modal, tabs, search, pagination)
  patterns.html         App shell, responsive rules, Run Classification flow,
                         12-key + 9-group pattern, table overflow, min-width:0
  states.html           Loading, empty, no-model-deployed, validation error,
                         not-found, destructive confirmation
  ml-workflow.html      3-stage workflow, dataset facts, preprocessing,
                         six-candidate model comparison, accuracy-paradox chart
  traceability.html     FR-01..16 and UC-01..09 mapped to screen/component
  handoff.css           This section's only stylesheet, built on ../css/tokens.css
  README.md             This file
```

`handoff.css` is the only stylesheet these pages load besides
`../css/tokens.css`. It defines no raw colors, fonts, or off-scale spacing --
every value is `var(--c-*)`, `var(--fs-*)`, `var(--space-*)`, `var(--radius-*)`,
etc. from the locked token file. The one intentional exception is the modal
backdrop scrim (`rgba(15, 23, 42, 0.45)`), noted inline in
`components.html` -- `tokens.css` does not define a backdrop-scrim token.

## How to use it

1. Read `design-tokens.html` next to `tokens.css`. Every swatch names its
   variable, hex, where to use it, and (for text/background pairs) its
   measured WCAG contrast ratio -- computed, not estimated.
2. Read `components.html` for the exact CSS to write: padding, height,
   radius, border, type token, color tokens, and every interaction state,
   for every component the app screens use.
3. Read `patterns.html` for how screens are assembled and how they adapt
   across 375/768/1024/1440.
4. Read `states.html` for everything that is not the happy path.
5. Read `ml-workflow.html` for the model story behind the Overview and Run
   Classification screens.
6. Use `traceability.html` as the grading/review checklist against the spec.

## Source of truth and how numbers were checked

Every number on these pages traces to exactly one of three sources:

- `mockup/css/tokens.css` (locked) -- every color, type size, spacing value,
  radius, shadow, and layout constant.
- `prod_content.md` (real production output) -- the deployed model's
  measured metrics, the 12 key features with real medians/min/max, the real
  per-group field counts (identity 4, battery_spec 3, battery_state 6,
  electrical 8, charging 12, driving 9, environment 7, maintenance 4, risk 2
  = 55 + 12 key = 67), real battery serials/classifications, and all six
  trained model candidates.
- `2 - Group5_ProjectSpec_v2.pdf` -- FR-01..16, UC-01..09, the 3-stage
  workflow (section 4.3), the architecture (section 5), and the ML approach
  (section 6: 20,000 rows, 70 columns, 93.08%/6.92% class split).

Contrast ratios on `design-tokens.html` were computed with the WCAG 2.1
relative-luminance formula applied directly to each token's hex pair -- not
estimated, and not rounded up. Two failures were found and are called out on
that page rather than hidden:

- `--c-text-muted` on `--c-surface-sunken` measures 4.35:1, under the 4.5:1
  AA floor for normal text, even though the same color passes against
  `--c-surface`/`--c-bg`. `tokens.css`'s own comment ("5.4:1 - still AA")
  is true only against the two backgrounds it was likely checked against,
  not the sunken one it names as a valid use ("table headers, inset wells,
  code blocks"). This handoff uses `--c-text-secondary` instead wherever
  muted text sits directly on a sunken surface.
- `--focus-ring` (`rgba(29, 78, 216, 0.35)`) alone measures roughly 1.79:1
  against white when the alpha is composited -- under the 3:1 AA minimum for
  a non-text focus indicator. Every interactive element in this handoff
  section pairs it with a solid `2px solid var(--c-primary)` outline (6.70:1)
  so the ring's soft glow and AA compliance are both satisfied; the
  production app should adopt the same pairing.

`--c-text` and `--c-text-secondary` also measure higher/lower than the inline
comments in `tokens.css` claim (17.74:1 vs. the claimed 16.1:1; 7.56:1 vs. the
claimed 8.6:1) -- both still pass AA, the comments are just imprecise, not
wrong in direction.

## Reconciliation with the app screens

This section and the five app screens in `mockup/` were built in parallel, so
three mismatches existed while they were in flight. All three have since been
resolved; they are recorded here because the resolution is the useful part.

1. **Feature group counts.** An earlier draft of `run-classification.html`
   split the 55 non-key fields across 8 groups with different counts. The
   rebuilt screen now uses the real 9-group breakdown taken from the deployed
   bundle's `feature_spec`: Identity 4 / Battery Specification 3 / Battery
   State 6 / Electrical 8 / Charging 12 / Driving 9 / Environment 7 /
   Maintenance 4 / Risk Indicators 2 = 55, plus the 12 always-visible key
   features = 67 model inputs. These are *non-key* counts per group, which is
   why they are smaller than each group's total size in `feature_spec`.
2. **Random Forest metrics.** The project `README.md`
   carried `0.9480` accuracy / `0.3610` recall, which predated the final
   training run. The deployed bundle's own `all_model_results` gives
   `0.9487` / `0.7687` / `0.3718` / `0.5012`. The source documents have been
   corrected to match the bundle; this handoff already used the real figures.
3. **Token naming.** `app.css` was rebuilt against the current `tokens.css`,
   so both halves of the deliverable now resolve the same `--c-*` / `--fs-*` /
   `--space-*` variables and render as one product.

Every number in this handoff traces to `models/model_bundle.joblib` metadata
or to the live application, never to an estimate.
