"""
Central configuration: filesystem paths and constants shared across the app.

All paths are resolved relative to the repository root so the app works the
same whether launched via `streamlit run app/main.py` from the repo root or
from inside app/.
"""
from __future__ import annotations

from pathlib import Path

# --- Filesystem layout -------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent

MODELS_DIR = REPO_ROOT / "models"
MODEL_BUNDLE_PATH = MODELS_DIR / "model_bundle.joblib"

DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "app.db"

ML_PIPELINE_ARTIFACTS_DIR = REPO_ROOT / "ml_pipeline" / "artifacts"
DEFAULT_SOURCE_BUNDLE_PATH = ML_PIPELINE_ARTIFACTS_DIR / "model_bundle.joblib"

RAW_DATASET_PATH = REPO_ROOT / "ev battery_failure prediction Dataset.csv"

# --- Identifier / target columns (per SPEC_CONTRACT.md section 1) ------
IDENTIFIER_FIELDS = ["vehicle_id", "battery_serial"]
TARGET_COLUMN = "battery_failure"

# The 8 categorical feature columns in the raw dataset (SPEC_CONTRACT.md
# section 1). Fixed by the dataset itself, independent of which model is
# deployed - used by seed_demo.py and the test bundle factory so both agree
# on which raw CSV columns are text vs numeric without duplicating the list.
CATEGORICAL_COLUMNS = [
    "vehicle_brand",
    "vehicle_model",
    "vehicle_type",
    "battery_manufacturer",
    "battery_chemistry",
    "drive_type",
    "fleet_or_private",
    "terrain_type",
]

# --- Feature UI grouping order (per SPEC_CONTRACT.md section 3.1) ------
FEATURE_GROUP_ORDER = [
    "identity",
    "battery_spec",
    "battery_state",
    "electrical",
    "charging",
    "driving",
    "environment",
    "maintenance",
    "risk",
]

FEATURE_GROUP_LABELS = {
    "identity": "Identity",
    "battery_spec": "Battery Specification",
    "battery_state": "Battery State",
    "electrical": "Electrical",
    "charging": "Charging",
    "driving": "Driving",
    "environment": "Environment",
    "maintenance": "Maintenance",
    "risk": "Risk Indicators",
}

# --- Classification labels ----------------------------------------------
CLASS_LABELS = {0: "No Failure", 1: "Failure"}

# --- Student / course information (SPEC_CONTRACT.md section 7) ---------
COURSE_INFO = {
    "university_line1": "Vietnam National University, Ho Chi Minh City",
    "university_line2": "University of Technology",
    "faculty": "Faculty of Computer Science and Engineering",
    "course": "Intelligent Systems",
    "instructor": "Assoc. Prof. Quản Thành Thơ",
    "group": "Group 5",
    "students": [
        "Phạm Văn Thành - 2570496",
        "Đồng Quang Trí - 2570523",
    ],
}

APP_TITLE = "EV Battery Failure Classification"
