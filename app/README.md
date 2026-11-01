# EV Battery Failure Classification - Streamlit Application

Software Developer deliverable (Agent B) for Group 5's EV Battery Failure
Classification project. Binary classification - **Failure** / **No
Failure** - built with Python + Streamlit + SQLite, single process, no
separate backend service, per `SPEC_CONTRACT.md` section 5 / spec section 5.

This directory (`app/`) and `../deployment/` are owned by the Software
Developer role. `../ml_pipeline/` (offline model training) is owned by the
Data Scientist role and is not part of this deliverable.

## 1. How to run

From the repository root (`Assigment/`):

```bash
python -m pip install -r app/requirements.txt

# Stage 2 - deploy a trained model (must run before classification works)
python deployment/deploy_model.py --bundle ml_pipeline/artifacts/model_bundle.joblib --target models/

# Optional but recommended - verify the deployed model end to end
python deployment/verify_model.py

# Optional - seed ~25 realistic demo records (sampled from the real CSV)
python app/seed_demo.py

# Stage 3 - run the web application
streamlit run app/main.py
```

If no model has been deployed yet, the app still starts. Every
classification-dependent screen shows a clear "no model deployed" state
with the exact command to run, instead of crashing. This is a real, expected
state in the spec's 3-stage workflow (stage 2 precedes stage 3), not an
error condition.

### Running the test suite

```bash
python -m pip install -r app/requirements.txt
python -m pytest app/tests -v
```

Tests build a small, structurally-valid synthetic model bundle in-process
(`app/tests/fixtures/bundle_factory.py`) so the whole suite is independent
of whether a real model has been deployed yet.

## 2. Project structure

```
app/
  main.py                 entry point: streamlit run app/main.py
  config.py                paths, constants, course/student info
  db.py                     SQLite schema + queries (FR-09)
  model_service.py        load bundle, validate input (FR-07), predict (FR-08)
  seed_demo.py             populate realistic demo data from the real CSV
  components/
    layout.py               sidebar navigation + footer
    status.py                deployed-model status / "no model" messaging
    forms.py                  67-feature input form (key fields + grouped expanders)
    results.py                Failure / No Failure result display
  pages_/
    home.py                  Home / Overview
    records.py                Battery Records (UC-06)
    classify.py                Run Classification (UC-07)
    assessment.py               Maintenance Assessment (UC-08)
    history.py                   Classification History (UC-09)
  tests/
    conftest.py               shared pytest fixtures
    fixtures/bundle_factory.py  synthetic model_bundle.joblib builders (tests only)
    test_db.py, test_model_service.py, test_deployment.py,
    test_pages_smoke.py, test_app_integration.py, test_seed_demo.py

deployment/
  deploy_model.py          FR-10 / UC-04: validate + deploy a model bundle
  verify_model.py           FR-11 / UC-05: verify the deployed model end to end
```

## 3. Screens and use-case coverage

| Screen | Use case(s) | Functional requirements |
|---|---|---|
| Home / Overview | - | FR-06 (shows deployed-model status read from bundle metadata) |
| Battery Records | UC-06 | FR-09, FR-12 |
| Run Classification | UC-07 | FR-06, FR-07, FR-08, FR-13, FR-14 |
| Maintenance Assessment | UC-08 | FR-09, FR-15 |
| Classification History | UC-09 | FR-09, FR-16 |

| CLI utility | Use case | Functional requirements |
|---|---|---|
| `deployment/deploy_model.py` | UC-04 | FR-10 |
| `deployment/verify_model.py` | UC-05 | FR-07, FR-08, FR-11 |

Full FR/UC traceability (including the Data Scientist's FR-01..FR-05,
owned by `ml_pipeline/`) is in `../SPEC_CONTRACT.md` section 5.

### Home / Overview
Explains what the system does, shows the deployed model's algorithm,
trained date and Failure-class precision/recall/F1 (read live from the
bundle's `metadata` - never hardcoded), database record/classification
counts, and the Group 5 student/course information.

### Battery Records (UC-06, FR-12)
Search by battery serial or vehicle id (case-insensitive substring match on
either field); list results; create a new record (serial uniqueness is
enforced - duplicate serials are rejected with a clear error); view and
update an existing record's parameters. Creating/editing parameters
requires a deployed model (to know the 67 feature definitions); search and
read-only viewing of previously-stored records still work without one.

### Run Classification (UC-07, FR-13, FR-14)
Search/select an existing battery record, review and edit its 67
parameters (key features always visible, the rest in collapsed per-group
expanders pre-filled with median/mode defaults), validate against the
bundle's `feature_spec` (FR-07), classify (FR-08), and display **Failure**
or **No Failure** prominently - with an icon (⚠️ / ✅) plus the literal text
label, never color alone - alongside the associated battery record.
Probability is shown only when `metadata.supports_probability` is true;
otherwise the UI explicitly states it is unavailable rather than fabricating
a number.

### Maintenance Assessment (UC-08, FR-15)
Pick a classification that does not yet have an assessment, review its
result, and record a free-text assessment + recommendation (+ optional
assessor name). One assessment per classification is enforced at the
database layer.

### Classification History (UC-09, FR-16)
All classifications newest-first, each with its linked battery record and
(if present) maintenance assessment, filterable by battery serial and/or
vehicle id.

## 4. Deployment utilities

### `deployment/deploy_model.py` (FR-10, UC-04)

```
python deployment/deploy_model.py --bundle ml_pipeline/artifacts/model_bundle.joblib --target models/
```

Validates, before touching the target directory, that: the bundle file
exists and loads with `joblib`; it is a dict containing `pipeline`,
`feature_spec`, `metadata`; `pipeline` exposes a callable `predict`;
`feature_spec.features` is a non-empty list where every entry has the
required keys for its kind (numeric: `min`/`max`/`median`; categorical:
`allowed_values`/`mode`); `metadata` has the required fields including
Failure-class precision/recall/F1/support. On any failure it prints the
specific reason(s) and exits non-zero **without** deploying. On success it
copies the bundle atomically (temp file + `os.replace`) to
`models/model_bundle.joblib` and prints a deployment summary.

### `deployment/verify_model.py` (FR-11, UC-05)

```
python deployment/verify_model.py
```

Tests the currently **deployed** model end to end, the same way the app
uses it: (1) model loads, (2) feature spec parses, (3) a valid
median/mode-default sample passes validation and classifies, returning
0/1 plus a probability when supported, (4) an input missing a required
feature is rejected by validation, (5) an out-of-range numeric value is
rejected, (6) an unknown categorical value is rejected, (7) a batch of real
rows sampled from the project CSV classifies and the predicted class
distribution is reported. Prints a PASS/FAIL table and exits non-zero if
any check fails.

## 5. Demo data (`app/seed_demo.py`)

```
python app/seed_demo.py
```

Samples ~25 real rows from the project CSV (both classes represented),
creates battery records from them (every parameter value is a genuine CSV
value, never invented), and - if a model is currently deployed - also runs
each through classification and attaches a maintenance assessment to a
representative subset. Idempotent: records are matched by their real,
unique `battery_serial`, so re-running does not create duplicates.

## 6. Notes on the Agent A / Agent B contract

`app/` and `deployment/` are built strictly against `SPEC_CONTRACT.md`
section 3 (the model bundle format) and section 4 (the SQLite schema), not
against any particular trained model. While `ml_pipeline/artifacts/model_bundle.joblib`
was not yet available, `app/tests/fixtures/bundle_factory.py` builds
synthetic-but-structurally-valid bundles (including one fitted on all 67
real feature columns from the project CSV) so that `app/`, `deployment/`,
and the full pytest suite could be built and tested end to end ahead of the
real artifact, and used to demonstrate `deploy_model.py` / `verify_model.py`
against a realistic 67-feature model. These fixtures are clearly labeled as
synthetic test fixtures (see their `metadata.selection_rationale`) and are
not the graded machine-learning deliverable. Once Agent A's real bundle is
available, redeploy with:

```
python deployment/deploy_model.py --bundle ml_pipeline/artifacts/model_bundle.joblib --target models/
python deployment/verify_model.py
```

No contract mismatches were found; `app/` and `deployment/` require no
changes once the real bundle is deployed.
