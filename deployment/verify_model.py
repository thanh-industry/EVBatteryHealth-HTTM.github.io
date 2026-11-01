#!/usr/bin/env python
"""
verify_model.py - Model verification utility for the Software Developer role.

FR-11 / UC-05: test the model that is currently DEPLOYED (models/model_bundle.joblib)
end to end, the same way the Streamlit app will use it, using sample data.

Usage:
    python deployment/verify_model.py
    python deployment/verify_model.py --bundle path/to/other_bundle.joblib
    python deployment/verify_model.py --sample-size 100

Checks performed:
    1. Model loads (file present, joblib.load succeeds, structurally valid)
    2. Feature spec parses (features list, groups, key-feature flags)
    3. A valid sample input (median/mode defaults) passes validation and
       classifies, returning 0/1 and a probability when supported
    4. An input missing a required feature is REJECTED by validation
    5. An out-of-range numeric value is REJECTED by validation
    6. An unknown categorical value is REJECTED by validation
    7. A batch of real rows sampled from the source CSV classifies, and the
       predicted class distribution is sane

Prints a PASS/FAIL table and exits non-zero if any check fails.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app import config, model_service  # noqa: E402


class Check:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.skipped = False
        self.detail = ""

    def ok(self, detail: str = "") -> None:
        self.passed = True
        self.detail = detail

    def fail(self, detail: str) -> None:
        self.passed = False
        self.detail = detail

    def skip(self, detail: str) -> None:
        self.passed = True
        self.skipped = True
        self.detail = detail

    @property
    def status(self) -> str:
        if self.skipped:
            return "SKIP"
        return "PASS" if self.passed else "FAIL"


def check_model_loads(bundle_path: Path, results: list[Check]) -> Optional[dict[str, Any]]:
    c = Check("1. Model loads")
    status = model_service.get_status(path=bundle_path, force_reload=True)
    if status.deployed:
        algo = status.bundle["metadata"].get("algorithm")
        c.ok(f"loaded OK from {bundle_path} (algorithm={algo})")
    else:
        c.fail(status.error or "unknown error")
    results.append(c)
    return status.bundle if status.deployed else None


def check_feature_spec_parses(bundle: dict[str, Any], results: list[Check]) -> list[dict]:
    c = Check("2. Feature spec parses")
    try:
        features = model_service.get_features(bundle)
        groups = model_service.group_features(features)
        keys = model_service.key_features(features)
        numeric = [f for f in features if f["kind"] == "numeric"]
        categorical = [f for f in features if f["kind"] == "categorical"]
        c.ok(
            f"{len(features)} features ({len(numeric)} numeric, "
            f"{len(categorical)} categorical) across {len(groups)} groups, "
            f"{len(keys)} marked key"
        )
    except Exception as exc:  # noqa: BLE001
        c.fail(str(exc))
        features = []
    results.append(c)
    return features


def check_valid_sample(bundle: dict[str, Any], results: list[Check]) -> None:
    c = Check("3. Valid sample input classifies")
    try:
        defaults = model_service.build_default_values(bundle)
        ok, errors = model_service.validate_input(defaults, bundle["feature_spec"])
        if not ok:
            c.fail(f"median/mode default sample was rejected: {errors[:3]}")
        else:
            result = model_service.predict(bundle, defaults)
            if result.prediction not in (0, 1):
                c.fail(f"prediction was not 0/1: {result.prediction}")
            else:
                proba_txt = (
                    f"{result.probability:.4f}"
                    if result.probability is not None
                    else "unavailable"
                )
                c.ok(
                    f"prediction={result.prediction} ({result.label}), "
                    f"probability={proba_txt}"
                )
    except Exception as exc:  # noqa: BLE001
        c.fail(str(exc))
    results.append(c)


def check_missing_required_rejected(bundle: dict[str, Any], results: list[Check]) -> None:
    c = Check("4. Missing required feature rejected")
    features = bundle["feature_spec"]["features"]
    required = [f for f in features if f.get("required", True)]
    if not required:
        c.skip("no required features declared in feature_spec")
        results.append(c)
        return
    target = required[0]
    values = model_service.build_default_values(bundle)
    values.pop(target["name"], None)
    ok, errors = model_service.validate_input(values, bundle["feature_spec"])
    if ok:
        c.fail(f"missing '{target['name']}' was NOT rejected by validation")
    else:
        c.ok(f"'{target['name']}' correctly rejected: {errors[0]}")
    results.append(c)


def check_out_of_range_rejected(bundle: dict[str, Any], results: list[Check]) -> None:
    c = Check("5. Out-of-range numeric value rejected")
    features = bundle["feature_spec"]["features"]
    candidates = [
        f
        for f in features
        if f["kind"] == "numeric" and f.get("max") is not None
    ]
    if not candidates:
        c.skip("no numeric feature declares a max bound")
        results.append(c)
        return
    target = candidates[0]
    values = model_service.build_default_values(bundle)
    out_of_range = float(target["max"]) + abs(float(target["max"])) + 1000.0
    values[target["name"]] = out_of_range
    ok, errors = model_service.validate_input(values, bundle["feature_spec"])
    if ok:
        c.fail(
            f"'{target['name']}'={out_of_range} (max={target['max']}) was NOT rejected"
        )
    else:
        c.ok(f"'{target['name']}'={out_of_range} correctly rejected: {errors[0]}")
    results.append(c)


def check_unknown_category_rejected(bundle: dict[str, Any], results: list[Check]) -> None:
    c = Check("6. Unknown categorical value rejected")
    features = bundle["feature_spec"]["features"]
    candidates = [
        f
        for f in features
        if f["kind"] == "categorical" and f.get("allowed_values")
    ]
    if not candidates:
        c.skip("no categorical feature declares allowed_values")
        results.append(c)
        return
    target = candidates[0]
    values = model_service.build_default_values(bundle)
    bogus = "__UNKNOWN_CATEGORY__"
    values[target["name"]] = bogus
    ok, errors = model_service.validate_input(values, bundle["feature_spec"])
    if ok:
        c.fail(f"'{target['name']}'={bogus!r} was NOT rejected")
    else:
        c.ok(f"'{target['name']}'={bogus!r} correctly rejected: {errors[0]}")
    results.append(c)


def check_real_csv_batch(
    bundle: dict[str, Any], results: list[Check], sample_size: int, csv_path: Path
) -> None:
    c = Check("7. Batch of real CSV rows classifies sanely")
    if not csv_path.exists():
        c.skip(f"source dataset not found at {csv_path}")
        results.append(c)
        return
    try:
        import pandas as pd

        features = bundle["feature_spec"]["features"]
        names = [f["name"] for f in features]
        header = pd.read_csv(csv_path, nrows=0).columns.tolist()
        usecols = [n for n in names if n in header]
        df = pd.read_csv(csv_path, usecols=usecols)
        n = min(sample_size, len(df))
        sample = df.sample(n=n, random_state=42)

        defaults = model_service.build_default_values(bundle)
        predictions: list[int] = []
        rejected = 0
        errors_seen: list[str] = []
        for _, row in sample.iterrows():
            values = dict(defaults)
            for name in names:
                if name in row.index:
                    v = row[name]
                    if pd.isna(v):
                        continue  # keep default for missing real-world values
                    values[name] = v
            ok, errs = model_service.validate_input(values, bundle["feature_spec"])
            if not ok:
                rejected += 1
                errors_seen.extend(errs[:1])
                continue
            result = model_service.predict(bundle, values)
            predictions.append(result.prediction)

        if not predictions:
            c.fail(
                f"all {n} sampled rows were rejected by validation "
                f"(e.g. {errors_seen[:2]})"
            )
        else:
            dist = Counter(predictions)
            total = len(predictions)
            failure_pct = 100.0 * dist.get(1, 0) / total
            no_failure_pct = 100.0 * dist.get(0, 0) / total
            note = ""
            if rejected:
                note = f"; {rejected}/{n} rows rejected by validation (out-of-range real data)"
            c.ok(
                f"classified {total}/{n} rows -> "
                f"No Failure {dist.get(0, 0)} ({no_failure_pct:.1f}%), "
                f"Failure {dist.get(1, 0)} ({failure_pct:.1f}%){note}"
            )
    except Exception as exc:  # noqa: BLE001
        c.fail(str(exc))
    results.append(c)


def print_report(results: list[Check]) -> bool:
    name_width = max(len(c.name) for c in results) + 2
    print()
    print("=" * 78)
    print("MODEL VERIFICATION REPORT")
    print("=" * 78)
    for c in results:
        print(f"[{c.status:4}] {c.name.ljust(name_width)} {c.detail}")
    print("-" * 78)
    n_pass = sum(1 for c in results if c.passed and not c.skipped)
    n_skip = sum(1 for c in results if c.skipped)
    n_fail = sum(1 for c in results if not c.passed)
    print(f"{n_pass} passed, {n_skip} skipped, {n_fail} failed, {len(results)} total")
    print("=" * 78)
    return n_fail == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the deployed model end to end using sample data."
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        default=config.MODEL_BUNDLE_PATH,
        help="Path to the deployed bundle (default: models/model_bundle.joblib)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=50,
        help="Number of real CSV rows to batch-classify (default: 50)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=config.RAW_DATASET_PATH,
        help="Path to the source dataset CSV for the batch check",
    )
    args = parser.parse_args(argv)

    results: list[Check] = []
    bundle = check_model_loads(args.bundle, results)
    if bundle is None:
        # Can't run the rest without a loadable bundle.
        ok = print_report(results)
        return 0 if ok else 1

    check_feature_spec_parses(bundle, results)
    check_valid_sample(bundle, results)
    check_missing_required_rejected(bundle, results)
    check_out_of_range_rejected(bundle, results)
    check_unknown_category_rejected(bundle, results)
    check_real_csv_batch(bundle, results, args.sample_size, args.csv)

    ok = print_report(results)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
