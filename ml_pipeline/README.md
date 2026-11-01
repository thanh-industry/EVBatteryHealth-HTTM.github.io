# ml_pipeline - Offline ML Pipeline

Offline machine learning pipeline for the EV Battery Failure Classification
project. Implements FR-01..FR-05 and UC-01..UC-03 of the project
specification: import the dataset, preprocess it, train and compare three
classifiers, select one, and export it for the Streamlit application in
`app/` (owned by a different agent; this directory never imports from or
writes to `app/`, `backend/`, `frontend/`, `deployment/`, or `mockup/`).

Binding interface: `../SPEC_CONTRACT.md` section 3 defines the exact shape
of `artifacts/model_bundle.joblib`.

## Directory layout

```
ml_pipeline/
  notebook/
    ev_battery_failure_classification.ipynb   narrative notebook (Colab/Jupyter)
  src/
    data.py        load + profile + feature metadata (groups, labels)
    preprocess.py   ColumnTransformer builder
    models.py       the 3 estimators x 2 class weights, SVM row cap
    evaluate.py     metrics: per-class P/R/F1, confusion matrix, PR-AUC, CV
    pipeline.py     orchestration shared by the notebook and train.py
    export.py       feature_spec + metadata builder, bundle writer
  train.py          headless CLI: reproduces the whole pipeline
  artifacts/
    model_bundle.joblib   pipeline + feature_spec + metadata (the A -> B interface)
    feature_spec.json     human-readable copy of the feature spec
    metrics.json           human-readable copy of metrics / comparison
  tests/            pytest suite
```

All training logic lives once, in `src/`. The notebook and `train.py` both
import it; neither duplicates it.

## Running the notebook

### Locally (Jupyter / VS Code)

```
pip install pandas numpy scikit-learn joblib matplotlib seaborn
pip install notebook   # or: jupyter lab
jupyter notebook ml_pipeline/notebook/ev_battery_failure_classification.ipynb
```

Open it from inside the cloned repository and "Run All". The setup cell
auto-detects `ml_pipeline/src/` and the dataset CSV (`../ev battery_failure
prediction Dataset.csv` relative to the notebook) via relative paths, so no
edits are needed if the repository layout is unchanged.

### Google Colab

1. Upload or `git clone` the repository so `ml_pipeline/src/*.py` and the
   dataset CSV are both available to the Colab runtime.
2. Open `ml_pipeline/notebook/ev_battery_failure_classification.ipynb` from
   that checkout (File > Open Notebook > GitHub, or upload the file
   directly after cloning into the Colab filesystem).
3. If the CSV lives somewhere other than the repository root, edit
   `CSV_PATH` in the setup cell.
4. Runtime > Run All.

The notebook installs no packages itself; Colab ships pandas, numpy,
scikit-learn, matplotlib and seaborn by default. If running on a bare
environment, `pip install` them first (see above).

## Running train.py (headless)

```
python ml_pipeline/train.py --csv "ev battery_failure prediction Dataset.csv" --out ml_pipeline/artifacts/
```

From the repository root (`Assigment/`). Prints dataset shape, class
balance, the trivial-baseline accuracy trap, a per-configuration comparison
table (6 configurations: Logistic Regression / SVM / Random Forest, each
plain and `class_weight="balanced"`), the selected model and why, the key
features, and writes the three artifact files. Optional `--cv-folds N`
(default 5) controls stratified cross-validation fold count.

## Artifacts

- `model_bundle.joblib` - `{"pipeline", "feature_spec", "metadata"}`, exactly
  per SPEC_CONTRACT.md section 3. `pipeline` is a fitted scikit-learn
  `Pipeline` (preprocessing + estimator together) that accepts a DataFrame
  with the 67 raw feature columns and returns 0/1 predictions.
- `feature_spec.json` - human-readable copy of `feature_spec` (FR-05):
  all 67 features with kind, required, numeric min/max/median or categorical
  allowed_values/mode, a human-readable label, a UI group, and `"key": true`
  on the ~12 most predictive features.
- `metrics.json` - human-readable copy of the selected model's metrics, all
  6 configurations' results, and the trivial baseline.

Re-running `train.py` or the notebook regenerates all three deterministically
(`random_state=42` throughout); the numbers only change if the dataset file
changes.

## Tests

```
pytest ml_pipeline/tests -v
```

Run from the repository root. Most tests use a small (300-row) stratified
sample of the real dataset for speed; `test_bundle_roundtrip.py` and
`test_feature_spec.py` load `artifacts/model_bundle.joblib`, so run
`train.py` (or the notebook) at least once first.

## Notes

- SVM (`SVC`, RBF kernel) training cost grows faster than linearly with row
  count, so SVM configurations are capped to a stratified 6,000-row subsample
  of the training partition (`src.models.SVM_TRAIN_ROW_CAP`). This is
  reported truthfully in the printed comparison table and the exported
  metadata (`svm_row_cap_applied`, `train_rows` per configuration); it is
  not applied to Logistic Regression or Random Forest.
- The selected model is picked by the highest F1-score on the Failure class
  (`src.pipeline.select_best_result`), never by accuracy - see the
  notebook's "Model Selection" section for the full reasoning, including why
  Random Forest's higher accuracy is misleading and the precision/recall
  trade-off of the `class_weight="balanced"` variants.
