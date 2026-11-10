"""
Per-prediction feature attribution (explainability for FR-14).

FR-14 requires the result to be displayed. It does not require it to be
explained - but a specialist deciding whether to act on a Failure prediction
needs to see which inputs drove it, and a bare probability is not reviewable.

Why this is exact rather than approximate
-----------------------------------------
The deployed estimator is a linear model, so a prediction decomposes with no
approximation at all:

    log_odds = intercept + SUM_j( coef_j * transformed_value_j )
    P(failure) = 1 / (1 + exp(-log_odds))

That identity IS the explanation. No SHAP or LIME dependency is needed, and
nothing here is sampled, estimated, or fitted - which also means the result is
deterministic and can be asserted in a test: reconstructing the probability
from the contributions must reproduce pipeline.predict_proba exactly.

For a non-linear estimator (e.g. RandomForest, or an RBF-kernel SVM) no such
identity exists. This module then reports that attribution is unavailable and
says why, rather than silently showing a different quantity - a tree model's
`feature_importances_` is a global property of the model, not an explanation of
one prediction, and presenting it as one would be misleading.

One-hot aggregation
-------------------
The ColumnTransformer expands 8 categorical columns into many indicator
columns. Contributions are summed back onto the originating feature, so each
reported row is one model input - the thing the specialist actually typed -
rather than a dummy variable they have never seen.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from app.model_service import _build_row, get_features


@dataclass
class Contribution:
    name: str
    label: str
    value: Any
    contribution: float

    @property
    def toward_failure(self) -> bool:
        return self.contribution >= 0


@dataclass
class Attribution:
    intercept: float
    top: list[Contribution]
    other_total: float
    other_count: int
    logit: float
    probability: float

    @property
    def top_total(self) -> float:
        return sum(c.contribution for c in self.top)

    @property
    def max_abs(self) -> float:
        """Largest absolute contribution among the shown rows, used to scale
        the bars. Per-prediction, never global: the question is which inputs
        mattered for THIS classification."""
        return max((abs(c.contribution) for c in self.top), default=0.0) or 1.0


def _split_pipeline(pipeline: Any) -> tuple[Any, Any]:
    """Return (transform_steps, final_estimator).

    Written against the Pipeline API rather than assuming the two-step
    (preprocessor, estimator) shape, so inserting a step (e.g. feature
    selection) does not silently break attribution.
    """
    estimator = pipeline[-1]
    transformer = pipeline[:-1]
    return transformer, estimator


def unavailable_reason(bundle: dict[str, Any]) -> Optional[str]:
    """None when attribution can be computed, otherwise a plain-language
    reason suitable for showing to a maintenance specialist."""
    try:
        _, estimator = _split_pipeline(bundle["pipeline"])
    except Exception:  # noqa: BLE001 - never break the result screen
        return "The deployed pipeline has an unexpected shape."

    coef = getattr(estimator, "coef_", None)
    if coef is None:
        algorithm = type(estimator).__name__
        return (
            f"The deployed model ({algorithm}) is not a linear model, so a "
            "prediction cannot be decomposed into exact per-feature "
            "contributions. Attribution is shown only when it is exact."
        )
    if np.asarray(coef).ndim != 2 or np.asarray(coef).shape[0] != 1:
        return (
            "Attribution is supported for binary classification only; the "
            "deployed model reports more than two classes."
        )
    return None


def compute_attribution(
    bundle: dict[str, Any], values: dict[str, Any], top_n: int = 8
) -> Optional[Attribution]:
    """Decompose one prediction into per-feature log-odds contributions.

    Returns None when the deployed model is not linear - callers should use
    unavailable_reason() to tell the user why.
    """
    if unavailable_reason(bundle) is not None:
        return None

    pipeline = bundle["pipeline"]
    features = get_features(bundle)
    transformer, estimator = _split_pipeline(pipeline)

    row = _build_row(values, features)
    transformed = transformer.transform(row)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    transformed = np.asarray(transformed, dtype=float)[0]

    coef = np.asarray(estimator.coef_, dtype=float)[0]
    intercept = float(np.asarray(estimator.intercept_, dtype=float)[0])

    # coef_ is expressed with respect to classes_[1]. For this project that is
    # the Failure class, but assert rather than assume: if a bundle were ever
    # fitted with the labels the other way round, every sign below would be
    # inverted and the explanation would be exactly backwards.
    classes = list(getattr(estimator, "classes_", [0, 1]))
    sign = 1.0
    if len(classes) == 2 and int(classes[1]) == 0:
        sign = -1.0
        intercept = -intercept

    contributions = sign * coef * transformed

    expanded_names = _expanded_names(transformer, len(contributions))
    spec_by_name = {f["name"]: f for f in features}
    totals: dict[str, float] = {}
    for expanded, value in zip(expanded_names, contributions):
        base = _base_feature(expanded, spec_by_name)
        totals[base] = totals.get(base, 0.0) + float(value)

    ordered = sorted(totals.items(), key=lambda kv: -abs(kv[1]))
    top_items = ordered[:top_n]
    rest = ordered[top_n:]

    top = [
        Contribution(
            name=name,
            label=spec_by_name.get(name, {}).get("label", name),
            value=values.get(name),
            contribution=total,
        )
        for name, total in top_items
    ]

    logit = intercept + float(contributions.sum())
    return Attribution(
        intercept=intercept,
        top=top,
        other_total=sum(t for _, t in rest),
        other_count=len(rest),
        logit=logit,
        probability=1.0 / (1.0 + math.exp(-logit)),
    )


def _expanded_names(transformer: Any, n_columns: int) -> list[str]:
    try:
        return [str(n) for n in transformer.get_feature_names_out()]
    except Exception:  # noqa: BLE001 - older/custom transformers
        return [f"col_{i}" for i in range(n_columns)]


def _base_feature(expanded: str, spec_by_name: dict[str, Any]) -> str:
    """Map a transformed column name back to the model input it came from.

    ColumnTransformer prefixes names with the transformer that produced them
    ("num__odometer_km"), and OneHotEncoder appends the category
    ("cat__drive_type_AWD"). The longest matching feature name wins, because
    one feature name can be a prefix of another.
    """
    name = expanded.split("__", 1)[1] if "__" in expanded else expanded
    if name in spec_by_name:
        return name
    candidates = [k for k in spec_by_name if name.startswith(k + "_")]
    if candidates:
        return max(candidates, key=len)
    return name
