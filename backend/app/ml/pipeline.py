"""Builds the sklearn Pipeline for a given algorithm and hyperparameters.

Numeric branch: median impute -> StandardScaler.
Categorical branch: most_frequent impute -> OneHotEncoder(handle_unknown="ignore").
SVM and Logistic Regression require the scaler; Random Forest tolerates it,
so one ColumnTransformer configuration is reused for all three algorithms.
"""
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

from app.core.config import settings


def _build_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_branch = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical_branch = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_branch, numeric_cols),
            ("categorical", categorical_branch, categorical_cols),
        ]
    )


def _build_estimator(algorithm: str, params: dict):
    if algorithm == "svm":
        return SVC(
            C=float(params.get("C", 1.0)),
            kernel=str(params.get("kernel", "rbf")),
            gamma=params.get("gamma", "scale"),
            probability=True,
            random_state=settings.RANDOM_STATE,
        )
    if algorithm == "random_forest":
        max_depth = params.get("max_depth")
        return RandomForestClassifier(
            n_estimators=int(params.get("n_estimators", 200)),
            max_depth=int(max_depth) if max_depth is not None else None,
            min_samples_leaf=int(params.get("min_samples_leaf", 1)),
            random_state=settings.RANDOM_STATE,
        )
    if algorithm == "logistic_regression":
        return LogisticRegression(
            C=float(params.get("C", 1.0)),
            max_iter=int(params.get("max_iter", 1000)),
            random_state=settings.RANDOM_STATE,
        )
    raise ValueError(f"Unknown algorithm: {algorithm}")


def supports_probability(algorithm: str) -> bool:
    # SVC is configured with probability=True in _build_estimator, so all
    # three supported algorithms genuinely expose predict_proba.
    return algorithm in settings.ALGORITHMS


def build_pipeline(
    algorithm: str, params: dict, numeric_cols: list[str], categorical_cols: list[str]
) -> Pipeline:
    preprocessor = _build_preprocessor(numeric_cols, categorical_cols)
    estimator = _build_estimator(algorithm, params)
    return Pipeline(steps=[("preprocess", preprocessor), ("estimator", estimator)])
