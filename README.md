# EV Battery Failure Classification

Machine learning system that classifies the condition of an electric-vehicle
battery as **Failure** or **No Failure**, to support EV fleet maintenance
decisions.

**Course:** Intelligent Systems
**Instructor:** Assoc. Prof. Quản Thành Thơ
**Group 5**
- Phạm Văn Thành - 2570496
- Đồng Quang Trí - 2570523

Vietnam National University, Ho Chi Minh City - University of Technology,
Faculty of Computer Science and Engineering.

---

## What the system does

Three stakeholders, three stages:

| Stage | Actor | What happens |
|---|---|---|
| 1. Offline ML | Data Scientist | Import the dataset, train and compare Logistic Regression / SVM / Random Forest, select a model, export it with its preprocessing pipeline and feature definitions |
| 2. Deployment | Software Developer | Validate and deploy the exported pipeline, then verify loading, input validation and inference on sample data |
| 3. Operation | EV Maintenance Specialist | Manage battery records, run Failure / No Failure classification, record a maintenance assessment, review history |

The model supports a maintenance decision. It does not replace professional
inspection, and the system performs no physical maintenance action.

---

## Repository layout

```
ml_pipeline/     Stage 1 - offline training (Colab notebook + headless CLI)
  notebook/      ev_battery_failure_classification.ipynb
  src/           data, preprocess, models, evaluate, export
  artifacts/     model_bundle.joblib, feature_spec.json, metrics.json
  tests/
deployment/      Stage 2 - deploy_model.py, verify_model.py
app/             Stage 3 - Streamlit web application
  pages_/        home, records, classify, assessment, history
  components/    shared UI
  tests/
mockup/          Static HTML+CSS UI/UX mockup (open index.html directly)
  fonts/         Self-hosted woff2, so the mockup works with no network
  handoff/       Engineering spec: tokens, components, patterns, traceability
models/          Deployed model bundle (created by deploy_model.py)
data/            SQLite database (created at runtime)
```

`backend/` and `frontend/` contain an earlier React + FastAPI prototype that
addressed a different formulation of the problem (multi-class state of health).
They are retained as prior work and are **not** part of this deliverable.

---

## Requirements

Python 3.11 or newer (tested on 3.11 and 3.12).

```bash
python -m pip install -r app/requirements.txt
```

---

## Running the system

### 1. Train and export a model (Stage 1)

Either open `ml_pipeline/notebook/ev_battery_failure_classification.ipynb` in
Google Colab or Jupyter and run all cells, or run the headless equivalent:

```bash
python ml_pipeline/train.py --csv "ev battery_failure prediction Dataset.csv" --out ml_pipeline/artifacts/
```

This writes `model_bundle.joblib` (fitted pipeline + feature definitions +
metrics), plus human-readable `feature_spec.json` and `metrics.json`.

### 2. Deploy and verify the model (Stage 2)

```bash
python deployment/deploy_model.py --bundle ml_pipeline/artifacts/model_bundle.joblib --target models/
python deployment/verify_model.py
```

`deploy_model.py` validates the bundle before copying it and refuses to deploy
anything malformed. `verify_model.py` then checks that the deployed model loads,
that valid input classifies, that invalid input is rejected, and that a batch of
real rows classifies sensibly. Both exit non-zero on failure.

### 3. Run the application (Stage 3)

```bash
python app/seed_demo.py          # optional: 25 demo records from the real dataset
python -m streamlit run app/main.py
```

Open http://localhost:8501

If no model has been deployed yet, the application says so clearly instead of
failing. That is the expected state before Stage 2 has been run.

---

## Dataset

`ev battery_failure prediction Dataset.csv` - **20,000 rows, 70 columns**, from
the Kaggle EV Battery Failure Prediction dataset.

Target: **`battery_failure`**

| Class | Count | Share |
|---|---|---|
| 0 - No Failure | 18,616 | 93.08% |
| 1 - Failure | 1,384 | 6.92% |

`vehicle_id` and `battery_serial` are used for record management, not as
predictors, leaving **67 features (59 numeric + 8 categorical)**.

Missing values affect roughly 3-5% of nearly every column, so imputation is part
of the pipeline rather than an optional step.

---

## Machine learning approach

Preprocessing and classification are combined in a single scikit-learn
`Pipeline` so the exact transformations used in training are reproduced at
inference:

- Numeric: median imputation then `StandardScaler`
- Categorical: most-frequent imputation then `OneHotEncoder(handle_unknown="ignore")`

`train_test_split(test_size=0.2, stratify=y, random_state=42)` runs **before**
any fitting, so preprocessing parameters are learned from training data only and
no information leaks from the test set.

### Why accuracy is not the selection metric

With 93.08% of records in one class, a model that always predicts "No Failure"
scores **93.08% accuracy while detecting zero failures**. Model selection is
therefore driven by Precision, Recall and F1 on the **Failure** class.

Measured results, stratified 80/20 split, `random_state=42`:

| Model | Accuracy | Precision (Failure) | Recall (Failure) | **F1 (Failure)** |
|---|---|---|---|---|
| **Logistic Regression** | 0.9695 | 0.8384 | 0.6931 | **0.7589** |
| Logistic Regression (balanced) | 0.9397 | 0.5373 | 0.9350 | 0.6825 |
| SVM | 0.9617 | 0.8131 | 0.5812 | 0.6779 |
| SVM (balanced) | 0.9615 | 0.6892 | 0.8087 | 0.7442 |
| Random Forest | 0.9487 | 0.7687 | 0.3718 | 0.5012 |
| Random Forest (balanced) | 0.9415 | 0.7529 | 0.2310 | 0.3536 |

Random Forest illustrates the point: 94.9% accuracy, but it detects only 37% of
real failures.

**Selected model: Logistic Regression**, the highest Failure-class F1 of the six
candidates. The balanced variant catches far more failures (93.5% recall) but at
53.7% precision, meaning most alarms would be false. Since the system is a
human-reviewed decision-support tool, the deployed configuration favours
trustworthy alerts; the balanced variant remains available in the notebook if
the operator later prefers recall over precision.

---

## Testing

```bash
python -m pytest ml_pipeline/tests -q     # pipeline, preprocessing, leakage, export
python -m pytest app/tests -q             # database, validation, inference, screens
python deployment/verify_model.py         # deployed-model verification
```

---

## UI/UX mockup

`mockup/` holds a standalone static mockup of the interface. It needs no build
step, server or network connection - open `mockup/index.html` in a browser.
Fonts are self-hosted in `mockup/fonts/`, so it renders identically offline.

Two parts:

- **Five production screens** mirroring the running application: overview,
  battery records, run classification (including the live step 1 -> step 2 ->
  result flow), maintenance assessment, and classification history. Every
  value shown is real - model metrics, feature medians and ranges, battery
  serials and classification outcomes all come from the deployed bundle and
  the application database.
- **`mockup/handoff/`** - the engineering specification an implementer builds
  from: design tokens with measured contrast ratios, every component with its
  states and redlined dimensions, layout and responsive patterns, the states
  catalogue, the ML workflow, and an FR-01..16 / UC-01..09 traceability table.

Two components go beyond the specification, added after design review and
recorded as additions in the traceability table: **feature attribution**, which
decomposes a single prediction into the exact per-input contributions that
produced it (possible without any approximation because the deployed estimator
is linear), and a **measurement trend** panel showing State of Health, Capacity
Loss and temperature across inspections as three separate charts.

See `mockup/README.md` and `mockup/handoff/README.md`.

---

## Troubleshooting

**"No model deployed".** Run Stage 1 then Stage 2. This is expected on a fresh
checkout, not a fault.

**Port 8501 already in use.** `python -m streamlit run app/main.py --server.port 8502`

**Database looks stale.** Delete `data/app.db` and re-run `python app/seed_demo.py`.
