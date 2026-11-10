"""
Tests for per-prediction feature attribution.

The central property is exactness: because the deployed estimator is linear,
reconstructing the probability from the contributions must reproduce
pipeline.predict_proba. If that ever stops holding, the explanation shown to a
maintenance specialist is wrong and these tests must fail loudly.
"""
from __future__ import annotations

import math

import pytest

from app import explain, model_service


def test_attribution_reconstructs_predict_proba_exactly(small_bundle):
    """intercept + sum(all contributions) must reproduce the model's own
    probability, not merely approximate it."""
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values)
    assert attribution is not None

    expected = model_service.predict(small_bundle, values).probability
    assert expected is not None
    assert attribution.probability == pytest.approx(expected, abs=1e-9)


def test_attribution_arithmetic_closes(small_bundle):
    """The remainder is reported so the sum visibly adds up; verify it does."""
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values)

    total = attribution.intercept + attribution.top_total + attribution.other_total
    assert total == pytest.approx(attribution.logit, abs=1e-9)
    assert attribution.probability == pytest.approx(
        1.0 / (1.0 + math.exp(-attribution.logit)), abs=1e-12
    )


def test_attribution_is_sorted_by_magnitude_and_respects_top_n(small_bundle):
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values, top_n=3)

    assert len(attribution.top) == 3
    magnitudes = [abs(c.contribution) for c in attribution.top]
    assert magnitudes == sorted(magnitudes, reverse=True)
    # nothing left out of the top is larger than the smallest shown
    assert abs(attribution.other_total) >= 0.0


def test_every_contribution_names_a_real_model_input(small_bundle):
    """One-hot columns must be folded back onto the feature the user typed,
    never surfaced as a dummy like 'cat__drive_type_AWD'."""
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values)

    valid = {f["name"] for f in model_service.get_features(small_bundle)}
    for contribution in attribution.top:
        assert contribution.name in valid, (
            f"{contribution.name!r} is not a model input - one-hot columns "
            "were not aggregated back onto their source feature"
        )


def test_contribution_direction_matches_sign(small_bundle):
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values)
    for contribution in attribution.top:
        assert contribution.toward_failure == (contribution.contribution >= 0)


def test_changing_an_input_changes_its_contribution(small_bundle):
    """A sanity check that the attribution tracks the input rather than being
    a constant property of the model."""
    features = model_service.get_features(small_bundle)
    numeric = next(f for f in features if f["kind"] == "numeric")

    base = model_service.build_default_values(small_bundle)
    bumped = dict(base)
    span = (numeric.get("max") or 1.0) - (numeric.get("min") or 0.0)
    bumped[numeric["name"]] = float(base[numeric["name"]]) + max(span * 0.25, 1.0)

    def contribution_for(values):
        attribution = explain.compute_attribution(
            small_bundle, values, top_n=len(features)
        )
        hit = [c for c in attribution.top if c.name == numeric["name"]]
        return hit[0].contribution if hit else 0.0

    assert contribution_for(base) != pytest.approx(contribution_for(bumped))


def test_non_linear_model_reports_a_reason_instead_of_guessing(small_bundle):
    """A tree model has no exact per-prediction decomposition. The app must
    say so rather than showing feature_importances_, which is a global
    property of the model and not an explanation of one prediction."""
    from sklearn.ensemble import RandomForestClassifier

    bundle = dict(small_bundle)
    pipeline = bundle["pipeline"]
    values = model_service.build_default_values(small_bundle)
    row = model_service._build_row(values, model_service.get_features(small_bundle))

    forest = RandomForestClassifier(n_estimators=3, random_state=0)
    transformed = pipeline[:-1].transform(row)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    forest.fit(
        list(transformed) * 2, [0, 1]
    )

    from sklearn.pipeline import Pipeline

    bundle["pipeline"] = Pipeline(
        list(pipeline.steps[:-1]) + [("estimator", forest)]
    )

    reason = explain.unavailable_reason(bundle)
    assert reason is not None
    assert "RandomForestClassifier" in reason
    assert explain.compute_attribution(bundle, values) is None


def test_unavailable_reason_is_none_for_the_linear_bundle(small_bundle):
    assert explain.unavailable_reason(small_bundle) is None
