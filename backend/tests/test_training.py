import numpy as np
import pytest
from sklearn.model_selection import train_test_split

from app.core.config import settings
from app.ml import features, labeling
from app.ml.train import run_training


@pytest.mark.parametrize("algorithm", ["svm", "random_forest", "logistic_regression"])
def test_all_algorithms_train_end_to_end(sample_df, algorithm):
    result = run_training(sample_df, algorithm, {}, 0.3)

    m = result.metrics
    for key in ["accuracy", "precision_macro", "recall_macro", "f1_macro"]:
        assert 0.0 <= m[key] <= 1.0

    for per_class in m["per_class"]:
        assert 0.0 <= per_class["precision"] <= 1.0
        assert 0.0 <= per_class["recall"] <= 1.0
        assert 0.0 <= per_class["f1"] <= 1.0
        assert per_class["support"] >= 0

    cm = result.confusion_matrix
    assert cm["labels"] == settings.SOH_CLASSES
    matrix = cm["matrix"]
    assert len(matrix) == 3
    assert all(len(row) == 3 for row in matrix)

    support_by_class = {pc["class"]: pc["support"] for pc in m["per_class"]}
    for label, row in zip(cm["labels"], matrix):
        assert sum(row) == support_by_class[label]

    assert result.supports_probability is True  # all 3 are configured with probability=True
    assert result.train_rows > 0
    assert result.test_rows > 0


def test_svm_subsamples_large_train_set(sample_df, monkeypatch):
    monkeypatch.setattr(settings, "SVM_MAX_TRAIN_ROWS", 10)
    result = run_training(sample_df, "svm", {}, 0.3)
    assert result.train_rows == 10


def test_dropped_missing_label_is_reported(sample_df_with_missing_labels):
    result = run_training(sample_df_with_missing_labels, "logistic_regression", {}, 0.3)
    assert result.dropped_missing_label == 5


def test_feature_importance_present_for_random_forest(sample_df):
    result = run_training(sample_df, "random_forest", {}, 0.3)
    assert result.feature_importance is not None
    assert len(result.feature_importance) > 0
    for item in result.feature_importance:
        assert item["importance"] >= 0.0


def test_feature_importance_present_for_logistic_regression(sample_df):
    result = run_training(sample_df, "logistic_regression", {}, 0.3)
    assert result.feature_importance is not None
    assert len(result.feature_importance) > 0


def test_feature_importance_null_for_svm(sample_df):
    result = run_training(sample_df, "svm", {}, 0.3)
    assert result.feature_importance is None


def test_no_nan_reaches_estimator_after_imputation(sample_df):
    """Preprocessing must handle missing values: the numeric branch's
    imputer output (fed to the estimator) must contain no NaN.
    """
    result = run_training(sample_df, "logistic_regression", {}, 0.3)

    labelled_df, _ = labeling.drop_missing_label(sample_df)
    y = labeling.labels_from_soh(labelled_df[settings.LABEL_SOURCE_COLUMN])
    X = features.build_feature_frame(labelled_df)
    X_train, X_test, _, _ = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=settings.RANDOM_STATE
    )
    assert X_test.isna().any().any()  # the raw test split genuinely has missing values to handle

    preprocessor = result.pipeline.named_steps["preprocess"]
    transformed = preprocessor.transform(X_test)
    dense = transformed.toarray() if hasattr(transformed, "toarray") else transformed
    assert not np.isnan(dense).any()


def test_pipeline_fitted_only_on_train_partition(sample_df):
    """The imputer/scaler statistics must match the TRAIN subset, never the
    full frame - proof the split happened before fit, not after.
    """
    result = run_training(sample_df, "logistic_regression", {}, 0.3)

    labelled_df, _ = labeling.drop_missing_label(sample_df)
    y = labeling.labels_from_soh(labelled_df[settings.LABEL_SOURCE_COLUMN])
    X = features.build_feature_frame(labelled_df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=settings.RANDOM_STATE
    )
    numeric_cols, _ = features.split_numeric_categorical(X_train)

    preprocessor = result.pipeline.named_steps["preprocess"]
    numeric_pipeline = preprocessor.named_transformers_["numeric"]
    imputer = numeric_pipeline.named_steps["impute"]
    scaler = numeric_pipeline.named_steps["scale"]

    expected_medians = X_train[numeric_cols].median()
    for i, col in enumerate(numeric_cols):
        assert imputer.statistics_[i] == pytest.approx(expected_medians[col], abs=1e-9)

    expected_filled = X_train[numeric_cols].fillna(expected_medians)
    expected_means = expected_filled.mean()
    for i, col in enumerate(numeric_cols):
        assert scaler.mean_[i] == pytest.approx(expected_means[col], abs=1e-6)


def test_predict_returns_valid_class(sample_df):
    result = run_training(sample_df, "random_forest", {}, 0.3)

    labelled_df, _ = labeling.drop_missing_label(sample_df)
    X = features.build_feature_frame(labelled_df)
    prediction = result.pipeline.predict(X.iloc[[0]])[0]
    assert prediction in settings.SOH_CLASSES


def test_supports_probability_truthful_for_svc(sample_df):
    result = run_training(sample_df, "svm", {}, 0.3)
    assert result.supports_probability is True

    labelled_df, _ = labeling.drop_missing_label(sample_df)
    X = features.build_feature_frame(labelled_df)
    proba = result.pipeline.predict_proba(X.iloc[[0]])
    assert proba.shape[1] == 3
    assert abs(proba.sum() - 1.0) < 1e-6
