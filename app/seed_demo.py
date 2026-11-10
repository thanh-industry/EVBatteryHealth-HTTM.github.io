#!/usr/bin/env python
"""
seed_demo.py - populate the local database with realistic demo data.

Samples ~25 battery records directly from the real project CSV (so every
parameter value is genuine, not invented), spanning both the Failure and No
Failure classes, and - if a model is currently deployed - also runs each
through classification and attaches a maintenance assessment to a subset of
the results.

Prior inspections (--history)
-----------------------------
The source dataset is cross-sectional: one row per battery, no repeat
measurements. To give the measurement-trend panel something to draw, this
script can also create earlier inspections for a few records. Be clear about
what those are:

  - the MOST RECENT reading of every record is the genuine CSV row;
  - earlier readings are DERIVED from it by walking the condition metrics
    back along a monotonic ageing path (health higher, capacity loss lower,
    cycles and odometer lower);
  - each derived reading is then classified by the real deployed model, so
    the stored prediction and probability are genuine model output for those
    inputs, not invented numbers.

This is demo data, in a script whose entire purpose is demo data. Pass
--history 0 to seed only the genuine present-day reading.

Idempotent: a record is only created if its (real) battery_serial is not
already in the database; re-running does not duplicate records,
classifications, or assessments.

Usage:
    python app/seed_demo.py
    python app/seed_demo.py --n 25 --random-state 42
    python app/seed_demo.py --history 0        # present-day reading only
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
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


# How a battery's condition is walked backwards to build a prior inspection.
# Signs are chosen so the derived history is physically coherent: a battery in
# the past was healthier, had lost less capacity, ran slightly cooler, and had
# fewer cycles and kilometres on it. Magnitudes are per 30-day step.
_AGEING_PER_STEP: dict[str, float] = {
    "state_of_health": +0.95,
    "battery_health_percent": +0.90,
    "capacity_loss_percent": -0.95,
    "remaining_capacity": +0.70,
    "cell_temperature_avg": -0.35,
    "cell_temperature_max": -0.40,
    "cycle_count": -28.0,
    "odometer_km": -2100.0,
    "vehicle_age_years": -0.08,
}

# Days between seeded inspections.
_HISTORY_INTERVAL_DAYS = 45


def _derive_prior_reading(
    values: dict[str, Any], steps_back: int, feature_spec: dict[str, Any]
) -> dict[str, Any]:
    """Return `values` as it plausibly looked `steps_back` inspections ago.

    Only the metrics in _AGEING_PER_STEP move; everything else is carried
    over unchanged. Results are clamped to the feature spec's trained range so
    a derived reading can never fall outside what the model has seen.
    """
    bounds = {
        f["name"]: (f.get("min"), f.get("max"))
        for f in feature_spec["features"]
        if f["kind"] == "numeric"
    }
    out = dict(values)
    for name, per_step in _AGEING_PER_STEP.items():
        if name not in out:
            continue
        try:
            current = float(out[name])
        except (TypeError, ValueError):
            continue
        shifted = current + per_step * steps_back
        low, high = bounds.get(name, (None, None))
        if low is not None:
            shifted = max(shifted, float(low))
        if high is not None:
            shifted = min(shifted, float(high))
        out[name] = round(shifted, 4)
    return out


def seed(
    n: int = 25,
    random_state: int = 42,
    csv_path: Optional[Path] = None,
    db_path: Optional[Path | str] = None,
    history: int = 4,
    history_records: int = 8,
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

        # Prior inspections first, so they carry earlier timestamps than the
        # present-day reading created below.
        if history > 0 and created_records <= history_records:
            for steps_back in range(history, 0, -1):
                prior_values = _derive_prior_reading(
                    values, steps_back, bundle["feature_spec"]
                )
                prior_ok, _ = model_service.validate_input(
                    prior_values, bundle["feature_spec"]
                )
                if not prior_ok:
                    continue
                prior_result = model_service.predict(bundle, prior_values)
                db.create_classification(
                    battery_record_id=record_id,
                    prediction=prior_result.prediction,
                    prediction_label=prior_result.label,
                    probability=prior_result.probability,
                    model_algorithm=prior_result.model_algorithm,
                    model_trained_at=prior_result.model_trained_at,
                    input_snapshot=prior_values,
                    created_at=(
                        datetime.now(timezone.utc)
                        - timedelta(days=_HISTORY_INTERVAL_DAYS * steps_back)
                    ).isoformat(timespec="seconds"),
                    db_path=db_path,
                )
                created_classifications += 1

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
    parser.add_argument(
        "--history",
        type=int,
        default=4,
        help=(
            "Number of DERIVED prior inspections to create per record, so the "
            "measurement-trend panel has a series to draw. 0 seeds only the "
            "genuine present-day reading. See the module docstring."
        ),
    )
    parser.add_argument("--n", type=int, default=25, help="Number of records to seed")
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args(argv)

    summary = seed(n=args.n, random_state=args.random_state, history=args.history)
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
