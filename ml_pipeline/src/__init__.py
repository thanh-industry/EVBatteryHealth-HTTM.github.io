"""Source package for the EV battery failure offline ML pipeline.

Modules:
    data        - dataset loading, profiling, feature/target split, feature metadata.
    preprocess  - ColumnTransformer builder (imputation + scaling + one-hot encoding).
    models      - the 3 estimators (6 configurations) and SVM row-cap subsampling.
    evaluate    - metrics: accuracy, per-class precision/recall/f1, confusion matrix,
                  PR-AUC, cross-validation, trivial baseline.
    pipeline    - orchestration: split -> train -> evaluate -> select, shared by the
                  notebook and train.py so training logic is never duplicated.
    export      - feature_spec + metadata builder and model_bundle.joblib writer.
"""
