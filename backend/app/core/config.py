"""Centralized settings. No magic numbers or strings anywhere else."""
from pathlib import Path


class Settings:
    # --- Paths ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "app.db"
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"
    MODELS_DIR: Path = DATA_DIR / "models"
    DATASETS_DIR: Path = DATA_DIR / "datasets"
    SOURCE_CSV_PATH: Path = BASE_DIR.parent / "ev battery_failure prediction Dataset.csv"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- SoH classification thresholds (single source of truth) ---
    SOH_GOOD_MIN: float = 85.0
    SOH_MONITOR_MIN: float = 70.0
    SOH_CLASSES: list[str] = ["GOOD", "MONITOR", "CRITICAL"]

    # --- Label source column ---
    LABEL_SOURCE_COLUMN: str = "state_of_health"

    # --- Derived label column name (e.g. used transiently while seeding to
    # stratify-sample rows per class). Never a real CSV column, but must be
    # excluded from the feature frame exactly like the label source itself -
    # single source of truth so it is never hardcoded a second time. ---
    DERIVED_LABEL_COLUMN: str = "health_class"

    # --- Leakage blocklist (ARCHITECTURE.md 2.2). Enforced in ml/features.py. ---
    LEAKAGE_BLOCKLIST: list[str] = [
        "state_of_health",
        "battery_health_percent",
        "capacity_loss_percent",
        "remaining_capacity",
        "vehicle_id",
        "battery_serial",
        "battery_failure",
    ]
    LEAKAGE_REASONS: dict[str, str] = {
        "state_of_health": "this is the label source itself",
        "battery_health_percent": "restatement of the label (|r| = 0.9898 with SoH)",
        "capacity_loss_percent": "exact algebraic identity: battery_health_percent + capacity_loss_percent == 100.0 (std 0.0)",
        "remaining_capacity": "reconstructs the label by ratio (remaining_capacity / battery_capacity_kwh * 100 has r = 0.9898 with SoH)",
        "vehicle_id": "pure row identifier (20,000 unique values)",
        "battery_serial": "pure row identifier (20,000 unique values)",
        "battery_failure": "a second label, not a model input",
    }

    # --- Algorithms ---
    ALGORITHMS: list[str] = ["svm", "random_forest", "logistic_regression"]

    DEFAULT_PARAMS: dict[str, dict] = {
        "svm": {"C": 1.0, "kernel": "rbf", "gamma": "scale"},
        "random_forest": {"n_estimators": 200, "max_depth": None, "min_samples_leaf": 1},
        "logistic_regression": {"C": 1.0, "max_iter": 1000},
    }

    # --- Training performance guardrails ---
    # SVC is superlinear in n (O(n^2)+). Orchestrator-measured: 8000 rows ~5s,
    # within 0.3pp accuracy of the full 15235-row fit (18.2s). Cap keeps a
    # single run well under 60s while staying honest (train_rows is reported).
    SVM_MAX_TRAIN_ROWS: int = 8000

    DEFAULT_TEST_SIZE: float = 0.2
    MIN_TEST_SIZE: float = 0.1
    MAX_TEST_SIZE: float = 0.4
    RANDOM_STATE: int = 42

    # --- Upload validation ---
    MAX_UPLOAD_MB: int = 50
    ALLOWED_UPLOAD_EXTENSION: str = ".csv"

    # --- Data quality ---
    SOH_HISTOGRAM_BIN_WIDTH: float = 5.0
    SOH_HISTOGRAM_MIN: float = 40.0
    SOH_HISTOGRAM_MAX: float = 100.0

    # --- Auth (demo token, signed with HMAC; not JWT, no extra dependency) ---
    SECRET_KEY: str = "ev-soh-demo-secret-key-do-not-use-in-production"
    TOKEN_TTL_SECONDS: int = 60 * 60 * 12  # 12 hours
    PBKDF2_ITERATIONS: int = 120_000
    DEMO_PASSWORD: str = "demo1234"

    ROLES: list[str] = ["data_scientist", "technician", "ev_user"]

    # --- Seed data sizing ---
    SEED_VEHICLE_COUNT: int = 60
    SEED_MEASUREMENTS_PER_BATTERY: int = 12
    SEED_DIAGNOSTICS_COUNT: int = 25


settings = Settings()

settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATASETS_DIR.mkdir(parents=True, exist_ok=True)
