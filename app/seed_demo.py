#!/usr/bin/env python
"""
seed_demo.py - populate the local database with realistic demo data.

Samples ~25 battery records directly from the real project CSV (so every
parameter value is genuine, not invented), spanning both the Failure and No
Failure classes, and - if a model is currently deployed - also runs each
through classification and attaches a maintenance assessment to a subset of
the results.

Idempotent: a record is only created if its (real) battery_serial is not
already in the database; re-running does not duplicate records,
classifications, or assessments.

Usage:
    python app/seed_demo.py
    python app/seed_demo.py --n 25 --random-state 42
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402

from app import config, db, model_service  # noqa: E402

ASSESSMENT_TEMPLATES_FAILURE = [
    (
        "Elevated thermal and electrical stress indicators consistent with "
        "the model's Failure prediction.",
        "Schedule a pack inspection within 7 days; avoid fast-charging "
        "until the battery has been inspected.",
    ),
    (
        "Abnormal voltage/temperature pattern observed in the submitted "
        "parameters, aligned with a predicted failure.",
        "Flag the vehicle for a workshop diagnostic test and restrict "
        "high-load driving in the interim.",
    ),
]
ASSESSMENT_TEMPLATES_OK = [
    (
        "Submitted parameters are within normal operating range; no "
        "failure indicators detected.",
        "Continue the routine maintenance schedule; re-check at the next "
        "service interval.",
    ),
    (
        "Battery state is consistent with healthy operation.",
        "No immediate action required; monitor at the next scheduled "
        "inspection.",
    ),
]


def _sample_rows(csv_path: Path, n: int, random_state: int) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    failure = df[df[config.TARGET_COLUMN] == 1]
    no_failure = df[df[config.TARGET_COLUMN] == 0]
    n_failure = min(max(1, round(n * 0.4)), len(failure))
    n_no_failure = min(n - n_failure, len(no_failure))
    sampled = pd.concat(
        [
            failure.sample(n=n_failure, random_state=random_state),
            no_failure.sample(n=n_no_failure, random_state=random_state),
        ]
    )
    return sampled.sample(frac=1, random_state=random_state)  # shuffle order


def _row_to_parameters(row: pd.Series, feature_cols: list[str]) -> dict[str, Any]:
    parameters: dict[str, Any] = {}
    for col in feature_cols:
        value = row[col]
        if pd.isna(value):
            continue
        if col in config.CATEGORICAL_COLUMNS:
            parameters[col] = str(value)
        else:
            parameters[col] = float(value)
    return parameters


def seed(
    n: int = 25,
    random_state: int = 42,
    csv_path: Optional[Path] = None,
    db_path: Optional[Path | str] = None,
) -> dict[str, Any]:
    csv_path = csv_path or config.RAW_DATASET_PATH
    db.init_db(db_path=db_path)

    header = pd.read_csv(csv_path, nrows=0).columns.tolist()
    feature_cols = [
        c for c in header if c not in config.IDENTIFIER_FIELDS and c != config.TARGET_COLUMN
    ]

    sample = _sample_rows(csv_path, n, random_state)
    status = model_service.get_status(force_reload=True)

    created_records = 0
    skipped_existing = 0
    created_classifications = 0
    created_assessments = 0

    for i, (_, row) in enumerate(sample.iterrows()):
        serial = str(row["battery_serial"])
        vehicle_id = str(row["vehicle_id"])

        if db.get_battery_record_by_serial(serial, db_path=db_path) is not None:
            skipped_existing += 1
            continue

        parameters = _row_to_parameters(row, feature_cols)
        record_id = db.create_battery_record(serial, vehicle_id, parameters, db_path=db_path)
        created_records += 1

        if not status.deployed:
            continue

        bundle = status.bundle
        values = dict(model_service.build_default_values(bundle))
        values.update(parameters)
        ok, _errors = model_service.validate_input(values, bundle["feature_spec"])
        if not ok:
            continue  # real-world edge case outside this bundle's trained range; skip quietly

        result = model_service.predict(bundle, values)
        classification_id = db.create_classification(
            battery_record_id=record_id,
            prediction=result.prediction,
            prediction_label=result.label,
            probability=result.probability,
            model_algorithm=result.model_algorithm,
            model_trained_at=result.model_trained_at,
            input_snapshot=values,
            db_path=db_path,
        )
        created_classifications += 1

        attach_assessment = result.prediction == 1 or (i % 2 == 0)
        if attach_assessment:
            templates = (
                ASSESSMENT_TEMPLATES_FAILURE
                if result.prediction == 1
                else ASSESSMENT_TEMPLATES_OK
            )
            assessment_text, recommendation_text = templates[i % len(templates)]
            db.create_assessment(
                classification_id=classification_id,
                assessment=assessment_text,
                recommendation=recommendation_text,
                assessed_by="EV Maintenance Specialist (demo seed)",
                db_path=db_path,
            )
            created_assessments += 1

    return {
        "records_created": created_records,
        "records_skipped_existing": skipped_existing,
        "classifications_created": created_classifications,
        "assessments_created": created_assessments,
        "model_deployed": status.deployed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed demo data from the real dataset.")
    parser.add_argument("--n", type=int, default=25, help="Number of records to seed")
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args(argv)

    summary = seed(n=args.n, random_state=args.random_state)
    print("Seed summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    if not summary["model_deployed"]:
        print(
            "\nNote: no model is currently deployed, so only battery records "
            "were seeded (no classifications/assessments). Deploy a model "
            "with deployment/deploy_model.py and re-run this script to add "
            "demo classifications and assessments."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
