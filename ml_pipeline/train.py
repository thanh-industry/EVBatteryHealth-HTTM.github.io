#!/usr/bin/env python
"""Headless, reproducible training CLI for the EV battery failure classifier.

Usage:
    python ml_pipeline/train.py --csv "<path to csv>" --out ml_pipeline/artifacts/

Loads the dataset, splits it (stratified 80/20, random_state=42), trains the
6 configurations (Logistic Regression / SVM / Random Forest, each with and
without class_weight="balanced"), prints a comparison table, selects the
configuration with the best Failure-class F1, and writes:
    <out>/model_bundle.joblib  - pipeline + feature_spec + metadata
    <out>/feature_spec.json    - human-readable copy of the feature spec
    <out>/metrics.json         - human-readable copy of the metrics / comparison

All training logic lives in ml_pipeline/src/ and is shared with the notebook;
nothing here is duplicated there.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make `src` importable regardless of the current working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import data as data_mod  # noqa: E402
from src.evaluate import trivial_baseline_metrics  # noqa: E402
from src.export import (  # noqa: E402
    build_bundle,
    build_feature_spec,
    build_metadata,
    compute_key_features,
    key_feature_method_description,
    save_bundle,
    save_json,
)
from src.pipeline import (  # noqa: E402
    RANDOM_STATE,
    TEST_SIZE,
    results_as_table,
    run_all_experiments,
    select_best_result,
    split_data,
)

SVM_TRAIN_ROW_CAP_DOC = "6000"  # kept in sync with src/models.py SVM_TRAIN_ROW_CAP


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the EV battery failure classifier.")
    parser.add_argument("--csv", required=True, help="Path to the EV battery dataset CSV.")
    parser.add_argument("--out", required=True, help="Output directory for artifacts.")
    parser.add_argument("--cv-folds", type=int, default=5, help="Stratified CV folds (default 5).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading dataset from {args.csv}")
    df = data_mod.load_dataset(args.csv)
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")

    X, y = data_mod.split_features_target(df)
    numeric_cols = data_mod.get_numeric_columns(df)
    categorical_cols = data_mod.get_categorical_columns(df)
    print(f"Feature matrix: {X.shape[1]} columns "
          f"({len(numeric_cols)} numeric + {len(categorical_cols)} categorical)")

    balance = data_mod.class_balance(y)
    print("\nClass balance:")
    print(balance.to_string())

    X_train, X_test, y_train, y_test = split_data(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    print(f"\nSplit: train={len(X_train)} rows, test={len(X_test)} rows "
          f"(stratified, test_size={TEST_SIZE}, random_state={RANDOM_STATE})")

    baseline = trivial_baseline_metrics(y_test)
    print("\nTrivial all-No-Failure baseline on the test set:")
    print(f"  accuracy={baseline['accuracy']:.4f}  "
          f"recall(Failure)={baseline['failure']['recall']:.4f}  "
          f"f1(Failure)={baseline['failure']['f1']:.4f}")

    print(f"\nTraining 6 configurations (SVM capped at {SVM_TRAIN_ROW_CAP_DOC} train rows)...")
    results = run_all_experiments(
        X_train, y_train, X_test, y_test, numeric_cols, categorical_cols, cv_folds=args.cv_folds,
    )

    table = results_as_table(results)
    print("\nComparison table (Failure class foregrounded):")
    cols = ["model", "accuracy", "precision_failure", "recall_failure", "f1_failure",
            "cv_f1_failure_mean", "pr_auc", "fit_seconds"]
    print(table[cols].to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    best = select_best_result(results)
    print(f"\nSelected model: {best.display_name} "
          f"(highest F1 on the Failure class = {best.metrics['failure']['f1']:.4f})")

    key_features = set(compute_key_features(best.pipeline, numeric_cols, categorical_cols))
    print(f"\nKey features ({len(key_features)}): {sorted(key_features)}")

    feature_spec = build_feature_spec(X_train, numeric_cols, categorical_cols, key_features)

    other_configs_summary = []
    for r in results:
        if r is best:
            continue
        gap = best.metrics["failure"]["f1"] - r.metrics["failure"]["f1"]
        other_configs_summary.append(f"{r.display_name} (F1={r.metrics['failure']['f1']:.4f}, -{gap:.4f})")
    rationale = (
        f"{best.display_name} achieves the highest F1-score on the Failure class "
        f"({best.metrics['failure']['f1']:.4f}, precision={best.metrics['failure']['precision']:.4f}, "
        f"recall={best.metrics['failure']['recall']:.4f}) among all six trained configurations. "
        f"It is selected over: {'; '.join(other_configs_summary)}. "
        "Accuracy was not used for selection because the classes are imbalanced "
        f"(93.08% No Failure / 6.92% Failure): a trivial all-No-Failure classifier already "
        f"scores {baseline['accuracy']:.4f} accuracy with 0 Failure recall."
    )

    supports_probability = hasattr(best.pipeline, "predict_proba")
    all_model_results = []
    for r in results:
        entry = dict(r.metrics)
        entry["algorithm"] = r.algorithm
        entry["class_weight"] = r.class_weight
        entry["display_name"] = r.display_name
        entry["cv_f1_failure_mean"] = r.cv["f1_failure_mean"]
        entry["cv_f1_failure_std"] = r.cv["f1_failure_std"]
        entry["fit_seconds"] = r.fit_seconds
        entry["train_rows"] = r.train_rows
        entry["svm_row_cap_applied"] = r.svm_row_cap_applied
        all_model_results.append(entry)

    metadata = build_metadata(
        algorithm=best.algorithm,
        class_weight=best.class_weight,
        params=best.params,
        train_rows=best.train_rows,
        test_rows=best.test_rows,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        decision_threshold=0.5,
        supports_probability=supports_probability,
        metrics=best.metrics,
        all_model_results=all_model_results,
        selection_rationale=rationale,
        key_feature_method=key_feature_method_description(best.algorithm),
    )

    bundle = build_bundle(best.pipeline, feature_spec, metadata)

    bundle_path = out_dir / "model_bundle.joblib"
    save_bundle(bundle, str(bundle_path))
    save_json(feature_spec, str(out_dir / "feature_spec.json"))
    save_json({"selected": metadata, "all_model_results": all_model_results,
               "trivial_baseline": baseline}, str(out_dir / "metrics.json"))

    print(f"\nWrote {bundle_path}")
    print(f"Wrote {out_dir / 'feature_spec.json'}")
    print(f"Wrote {out_dir / 'metrics.json'}")


if __name__ == "__main__":
    main()
