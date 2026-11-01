#!/usr/bin/env python
"""
deploy_model.py - Model deployment utility for the Software Developer role.

FR-10 / UC-04: validate an exported model bundle produced by the offline ML
pipeline produced by the Data Scientist and, only if it is structurally sound,
copy it into the application's local model directory where the Streamlit
app (app/model_service.py) will load it from.

Usage:
    python deployment/deploy_model.py --bundle ml_pipeline/artifacts/model_bundle.joblib --target models/

Exit codes:
    0  validated and deployed
    1  validation failed - nothing was deployed
    2  unexpected error (I/O, etc.)

Validation performed (per SPEC_CONTRACT.md section 3), in order:
    1. the bundle file exists and loads with joblib
    2. it is a dict containing "pipeline", "feature_spec", "metadata"
    3. pipeline exposes a callable predict()
    4. feature_spec.features is a non-empty list and every entry has the
       required keys for its kind (numeric / categorical)
    5. metadata has the required fields, including Failure-class metrics

On any failure, a clear reason is printed and the process exits non-zero
WITHOUT touching the target directory. On success the bundle is copied
atomically (write to a temp file in the target dir, then os.replace) and a
deployment summary is printed.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import joblib

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app import config  # noqa: E402

REQUIRED_TOP_KEYS = ["pipeline", "feature_spec", "metadata"]

REQUIRED_FEATURE_KEYS_COMMON = ["name", "kind", "required", "label", "group"]
REQUIRED_FEATURE_KEYS_NUMERIC = ["min", "max", "median"]
REQUIRED_FEATURE_KEYS_CATEGORICAL = ["allowed_values", "mode"]

REQUIRED_METADATA_FIELDS = [
    "algorithm",
    "trained_at",
    "train_rows",
    "test_rows",
    "class_labels",
    "decision_threshold",
    "supports_probability",
    "metrics",
]
REQUIRED_METRICS_FIELDS = ["accuracy", "failure", "no_failure", "macro_f1"]
REQUIRED_CLASS_METRIC_FIELDS = ["precision", "recall", "f1", "support"]


class ValidationError(Exception):
    """Raised with a human-readable reason when the bundle fails validation."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValidationError(reason)


def load_bundle_for_validation(bundle_path: Path) -> dict[str, Any]:
    _require(bundle_path.exists(), f"bundle file not found: {bundle_path}")
    _require(bundle_path.is_file(), f"bundle path is not a file: {bundle_path}")
    try:
        bundle = joblib.load(bundle_path)
    except Exception as exc:  # noqa: BLE001 - we want to report any load failure
        raise ValidationError(f"bundle failed to load with joblib: {exc}") from exc
    _require(isinstance(bundle, dict), "bundle must deserialize to a dict")
    return bundle


def validate_bundle(bundle: dict[str, Any]) -> list[str]:
    """Return a list of human-readable problems. Empty list means valid."""
    problems: list[str] = []

    for key in REQUIRED_TOP_KEYS:
        if key not in bundle:
            problems.append(f"missing top-level key '{key}'")
    if problems:
        return problems  # no point checking deeper without the basics

    pipeline = bundle["pipeline"]
    if not hasattr(pipeline, "predict") or not callable(getattr(pipeline, "predict")):
        problems.append("pipeline does not expose a callable predict()")

    feature_spec = bundle["feature_spec"]
    if not isinstance(feature_spec, dict):
        problems.append("feature_spec must be a dict")
    else:
        features = feature_spec.get("features")
        if not isinstance(features, list) or len(features) == 0:
            problems.append("feature_spec.features must be a non-empty list")
        else:
            for idx, feat in enumerate(features):
                if not isinstance(feat, dict):
                    problems.append(f"feature_spec.features[{idx}] is not a dict")
                    continue
                label = feat.get("name", f"index {idx}")
                missing = [k for k in REQUIRED_FEATURE_KEYS_COMMON if k not in feat]
                if missing:
                    problems.append(
                        f"feature '{label}' missing keys: {', '.join(missing)}"
                    )
                    continue
                kind = feat.get("kind")
                if kind == "numeric":
                    missing = [
                        k for k in REQUIRED_FEATURE_KEYS_NUMERIC if k not in feat
                    ]
                    if missing:
                        problems.append(
                            f"numeric feature '{label}' missing keys: "
                            f"{', '.join(missing)}"
                        )
                elif kind == "categorical":
                    missing = [
                        k for k in REQUIRED_FEATURE_KEYS_CATEGORICAL if k not in feat
                    ]
                    if missing:
                        problems.append(
                            f"categorical feature '{label}' missing keys: "
                            f"{', '.join(missing)}"
                        )
                    allowed = feat.get("allowed_values")
                    if kind == "categorical" and not missing and not allowed:
                        problems.append(
                            f"categorical feature '{label}' has empty allowed_values"
                        )
                else:
                    problems.append(
                        f"feature '{label}' has invalid kind '{kind}' "
                        "(expected 'numeric' or 'categorical')"
                    )
            names = [f.get("name") for f in features if isinstance(f, dict)]
            dupes = {n for n in names if names.count(n) > 1}
            if dupes:
                problems.append(f"duplicate feature names: {sorted(dupes)}")

    metadata = bundle["metadata"]
    if not isinstance(metadata, dict):
        problems.append("metadata must be a dict")
    else:
        missing = [k for k in REQUIRED_METADATA_FIELDS if k not in metadata]
        if missing:
            problems.append(f"metadata missing fields: {', '.join(missing)}")
        else:
            metrics = metadata.get("metrics", {})
            if not isinstance(metrics, dict):
                problems.append("metadata.metrics must be a dict")
            else:
                missing_m = [k for k in REQUIRED_METRICS_FIELDS if k not in metrics]
                if missing_m:
                    problems.append(
                        f"metadata.metrics missing fields: {', '.join(missing_m)}"
                    )
                failure_metrics = metrics.get("failure", {})
                if not isinstance(failure_metrics, dict):
                    problems.append("metadata.metrics.failure must be a dict")
                else:
                    missing_f = [
                        k
                        for k in REQUIRED_CLASS_METRIC_FIELDS
                        if k not in failure_metrics
                    ]
                    if missing_f:
                        problems.append(
                            "metadata.metrics.failure missing fields: "
                            f"{', '.join(missing_f)}"
                        )
            if metadata.get("algorithm") not in (
                "logistic_regression",
                "svm",
                "random_forest",
            ):
                problems.append(
                    "metadata.algorithm must be one of logistic_regression/svm/"
                    f"random_forest, got {metadata.get('algorithm')!r}"
                )

    return problems


def deploy(bundle_path: Path, target_dir: Path) -> Path:
    """Validate then atomically copy bundle_path into target_dir. Raises
    ValidationError on failure (target_dir is left untouched)."""
    bundle = load_bundle_for_validation(bundle_path)
    problems = validate_bundle(bundle)
    if problems:
        raise ValidationError(
            "bundle failed validation:\n  - " + "\n  - ".join(problems)
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    final_path = target_dir / "model_bundle.joblib"

    fd, tmp_name = tempfile.mkstemp(
        dir=str(target_dir), prefix=".model_bundle_", suffix=".tmp"
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        tmp_path.write_bytes(bundle_path.read_bytes())
        os.replace(tmp_path, final_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    return final_path


def print_summary(bundle: dict[str, Any], deployed_path: Path) -> None:
    metadata = bundle["metadata"]
    features = bundle["feature_spec"]["features"]
    failure = metadata.get("metrics", {}).get("failure", {})

    print()
    print("=" * 60)
    print("DEPLOYMENT SUCCESSFUL")
    print("=" * 60)
    print(f"Deployed to      : {deployed_path}")
    print(f"Algorithm        : {metadata.get('algorithm')}")
    print(f"Trained at       : {metadata.get('trained_at')}")
    print(f"Feature count    : {len(features)}")
    print(f"Supports proba   : {metadata.get('supports_probability')}")
    print("Failure-class metrics:")
    print(f"  precision      : {failure.get('precision')}")
    print(f"  recall         : {failure.get('recall')}")
    print(f"  f1             : {failure.get('f1')}")
    print(f"  support        : {failure.get('support')}")
    if metadata.get("selection_rationale"):
        print(f"Selection reason : {metadata['selection_rationale']}")
    print("=" * 60)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and deploy an exported model bundle."
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        default=config.DEFAULT_SOURCE_BUNDLE_PATH,
        help="Path to the exported model_bundle.joblib "
        "(default: ml_pipeline/artifacts/model_bundle.joblib)",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=config.MODELS_DIR,
        help="Directory to deploy into (default: models/)",
    )
    args = parser.parse_args(argv)

    bundle_path: Path = args.bundle
    target_dir: Path = args.target

    print(f"Validating bundle: {bundle_path}")
    try:
        bundle = load_bundle_for_validation(bundle_path)
        problems = validate_bundle(bundle)
        if problems:
            print("VALIDATION FAILED. Reasons:", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            print("\nNothing was deployed.", file=sys.stderr)
            return 1
    except ValidationError as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        print("\nNothing was deployed.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"UNEXPECTED ERROR during validation: {exc}", file=sys.stderr)
        return 2

    print("Validation passed. Deploying...")
    try:
        deployed_path = deploy(bundle_path, target_dir)
    except ValidationError as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        print("\nNothing was deployed.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"UNEXPECTED ERROR during deployment: {exc}", file=sys.stderr)
        return 2

    print_summary(bundle, deployed_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
