# EV Battery Failure Classification - UI/UX Mockup

Static HTML + CSS mockup of the EV Maintenance Specialist web application,
built to mirror the running production system (`frontend/` / Streamlit app)
and the project specification (`2 - Group5_ProjectSpec_v2.pdf`). It is a
design deliverable only: no build step, no framework, no backend, no network
calls. Every number on these pages is a real figure from the deployed model
and the seeded database, not sample/placeholder data.

## How to open it

Double-click `index.html` (or any other `.html` file in this folder) to open
it directly in a browser. No server, no `npm install`, no internet
connection required or used. CSS is loaded only via relative paths
(`css/tokens.css`, `css/app.css`); fonts are self-hosted in `../fonts/`
(Inter 400/500/600/700 with Vietnamese subsets, JetBrains Mono 400/600) and
declared in `css/tokens.css` - there is no Google Fonts or other CDN
reference anywhere in this folder.

```
mockup/
  index.html                   Overview - deployed model status, counts, activity
  battery-records.html         UC-06, FR-09/FR-12 - search, view, create
  run-classification.html      UC-07, FR-06/07/08/13/14 - 2-step flow + result
  maintenance-assessment.html  UC-08, FR-09/FR-15 - assessment + recommendation
  classification-history.html  UC-09, FR-09/FR-16 - filterable history, table + timeline
  css/tokens.css                locked design tokens (owned by another agent, not edited here)
  css/app.css                   component styles, built entirely on tokens.css
  js/app.js                     modal open/close, step 1->2 flow, +/- steppers,
                                 search/filter, simulated "classify" loading -> result
  fonts/                        self-hosted Inter + JetBrains Mono (not edited here)
  handoff/                      engineering handoff reference (owned by another agent)
```

## Data provenance

Every figure traces to one of two sources, never invented:

- **Deployed model** (Overview, and the result panel on Run Classification /
  Maintenance Assessment): Logistic Regression, trained 01 Nov 2026 05:10
  UTC, 67 features, Failure-class precision 0.838 / recall 0.693 / F1 0.759 /
  support 277, accuracy 0.9695, confusion matrix [[3686,37],[85,192]] on a
  4,000-row held-out test set.
- **Database** (Battery Records, Run Classification step 1, Classification
  History): the real seeded rows - 25 battery records, 27 classifications
  (8 Failure / 19 No Failure), 16 maintenance assessments. Only 8 of the 25
  records/classifications were available in the extracted content, so every
  table is captioned honestly as "8 of 25" / "8 most recent of 27" rather
  than padded out with invented serials.

The 12 key model parameters on Run Classification (labels, groups, and the
training-set median/mode default shown in each field) and the real per-group
field counts for the remaining 55 parameters (identity 4, battery_spec 3,
battery_state 6, electrical 8, charging 12, driving 9, environment 7,
maintenance 4, risk 2) are the real values from the deployed feature
specification. The individual field names inside those 9 collapsed groups
are **not** itemized in this mockup: only their counts and defaulting
behavior are known from the extracted content, so each group shows an
honest note instead of invented field labels.

The two maintenance-assessment text patterns quoted on
`maintenance-assessment.html` ("Elevated thermal and electrical stress
indicators..." / "Submitted parameters are within normal operating
range...") are the real, verbatim text recurring in the seeded database.

## The binary result

The classification result is strictly **Failure** or **No Failure** - every
occurrence ships the literal word plus an icon, never color alone (checked
against deuteranopia/protanopia per the token file's own note on the
failure/ok pair).

## Design decisions beyond mirroring Streamlit

- **Confusion matrix on Overview.** Production's Streamlit home screen only
  shows the four Failure-class metrics as numbers. This mockup adds a small
  hand-authored SVG 2x2 confusion matrix (3686/37/85/192) so an engineer can
  see at a glance what "96.95% accuracy" is actually made of - a deliberate
  elevation, not a Streamlit default.
- **Sidebar is the single source of navigation + model status + course
  info**, matching the real app's layout exactly (one left column, not a
  separate top bar), rather than inventing a second navigation surface.
- **Two-step Run Classification flow is a real toggle**, not two static
  screenshots glued together: selecting a record in step 1 hides it and
  reveals step 2 via `js/app.js`, with a "Change battery record" link back,
  matching the two production screenshots of this flow.
- **Numeric key parameters use a stepper (-/input/+) control** sized to the
  44px touch-target minimum, wired up in `js/app.js` to respect each field's
  real min/max/step - a concrete, buildable affordance rather than a bare
  `<input type="number">`.
- Dense table row actions (`.btn-sm`, 36px) are a deliberate exception to
  the 44px touch-target rule: they comfortably clear the WCAG 2.5.8 AA
  minimum (24px) and keep the records/history tables scannable, consistent
  with the token file's own "dense operational tool" rationale for the
  15px body size.
