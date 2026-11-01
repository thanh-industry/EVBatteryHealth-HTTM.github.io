from __future__ import annotations

from app.format_utils import format_algorithm_name, format_timestamp


def test_format_timestamp_with_utc_offset():
    assert format_timestamp("2026-11-01T05:10:21+00:00") == "01 Nov 2026, 05:10 UTC"


def test_format_timestamp_with_z_suffix():
    assert format_timestamp("2026-11-01T05:10:21Z") == "01 Nov 2026, 05:10 UTC"


def test_format_timestamp_naive_datetime_no_crash():
    # No timezone info - still formats, just without the UTC suffix.
    assert format_timestamp("2026-11-01T05:10:21") == "01 Nov 2026, 05:10"


def test_format_timestamp_none_and_empty():
    assert format_timestamp(None) == "n/a"
    assert format_timestamp("") == "n/a"
    assert format_timestamp("   ") == "n/a"


def test_format_timestamp_unparseable_falls_back_to_raw_without_raising():
    assert format_timestamp("not-a-timestamp") == "not-a-timestamp"


def test_format_timestamp_converts_non_utc_offset_to_utc():
    # +05:00 at 10:10 is 05:10 UTC
    assert format_timestamp("2026-11-01T10:10:00+05:00") == "01 Nov 2026, 05:10 UTC"


def test_format_algorithm_name_known_patterns():
    assert format_algorithm_name("logistic_regression") == "Logistic Regression"
    assert format_algorithm_name("random_forest") == "Random Forest"
    assert format_algorithm_name("svm") == "SVM"


def test_format_algorithm_name_unseen_algorithm_degrades_gracefully():
    # No hardcoded per-algorithm table, so a model this app has never
    # heard of must still produce a readable label, not a crash or 'n/a'.
    assert format_algorithm_name("gradient_boosted_trees") == "Gradient Boosted Trees"
    assert format_algorithm_name("xgboost") == "Xgboost"


def test_format_algorithm_name_none_and_empty():
    assert format_algorithm_name(None) == "n/a"
    assert format_algorithm_name("") == "n/a"
