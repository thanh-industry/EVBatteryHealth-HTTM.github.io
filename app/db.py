"""
SQLite persistence layer (FR-09).

Schema is fixed by SPEC_CONTRACT.md section 4 and must not be changed:

    battery_records(id, battery_serial UNIQUE, vehicle_id, parameters_json,
                     created_at, updated_at)
    classifications(id, battery_record_id FK, prediction, prediction_label,
                     probability, model_algorithm, model_trained_at,
                     input_snapshot_json, created_at)
    maintenance_assessments(id, classification_id FK UNIQUE, assessment,
                             recommendation, assessed_by, created_at)

Every public function accepts an optional `db_path` override (used by tests
to point at a throwaway database) and otherwise uses config.DB_PATH.
Connections are short-lived and opened per call, which keeps this module
free of Streamlit-specific caching concerns and safe to use from plain
pytest tests.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS battery_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battery_serial TEXT UNIQUE NOT NULL,
    vehicle_id TEXT NOT NULL,
    parameters_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battery_record_id INTEGER NOT NULL,
    prediction INTEGER NOT NULL,
    prediction_label TEXT NOT NULL,
    probability REAL,
    model_algorithm TEXT NOT NULL,
    model_trained_at TEXT NOT NULL,
    input_snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (battery_record_id) REFERENCES battery_records(id)
);

CREATE TABLE IF NOT EXISTS maintenance_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    classification_id INTEGER NOT NULL UNIQUE,
    assessment TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    assessed_by TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (classification_id) REFERENCES classifications(id)
);

CREATE INDEX IF NOT EXISTS idx_battery_records_serial
    ON battery_records(battery_serial);
CREATE INDEX IF NOT EXISTS idx_battery_records_vehicle
    ON battery_records(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_classifications_record
    ON classifications(battery_record_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _resolve_path(db_path: Optional[Path | str]) -> Path:
    return Path(db_path) if db_path is not None else config.DB_PATH


@contextmanager
def _connect(db_path: Optional[Path | str] = None) -> Iterator[sqlite3.Connection]:
    path = _resolve_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Optional[Path | str] = None) -> None:
    """Create tables/indexes if they do not already exist. Idempotent."""
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)


# --------------------------------------------------------------------- #
# battery_records
# --------------------------------------------------------------------- #

def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["parameters"] = json.loads(d.pop("parameters_json"))
    return d


def create_battery_record(
    battery_serial: str,
    vehicle_id: str,
    parameters: dict[str, Any],
    db_path: Optional[Path | str] = None,
) -> int:
    """Insert a new battery record. Raises ValueError if the serial already exists."""
    battery_serial = battery_serial.strip()
    vehicle_id = vehicle_id.strip()
    if not battery_serial:
        raise ValueError("battery_serial is required")
    if not vehicle_id:
        raise ValueError("vehicle_id is required")
    now = _now()
    try:
        with _connect(db_path) as conn:
            cur = conn.execute(
                "INSERT INTO battery_records "
                "(battery_serial, vehicle_id, parameters_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (battery_serial, vehicle_id, json.dumps(parameters), now, now),
            )
            return int(cur.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            f"battery_serial '{battery_serial}' already exists"
        ) from exc


def update_battery_record(
    record_id: int,
    vehicle_id: Optional[str] = None,
    parameters: Optional[dict[str, Any]] = None,
    db_path: Optional[Path | str] = None,
) -> bool:
    """Update vehicle_id and/or parameters for an existing record."""
    existing = get_battery_record(record_id, db_path=db_path)
    if existing is None:
        return False
    new_vehicle_id = vehicle_id if vehicle_id is not None else existing["vehicle_id"]
    new_parameters = parameters if parameters is not None else existing["parameters"]
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE battery_records "
            "SET vehicle_id = ?, parameters_json = ?, updated_at = ? "
            "WHERE id = ?",
            (new_vehicle_id, json.dumps(new_parameters), _now(), record_id),
        )
    return True


def get_battery_record(
    record_id: int, db_path: Optional[Path | str] = None
) -> Optional[dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM battery_records WHERE id = ?", (record_id,)
        ).fetchone()
    return _row_to_record(row) if row else None


def get_battery_record_by_serial(
    battery_serial: str, db_path: Optional[Path | str] = None
) -> Optional[dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM battery_records WHERE battery_serial = ?",
            (battery_serial.strip(),),
        ).fetchone()
    return _row_to_record(row) if row else None


def search_battery_records(
    query: str, db_path: Optional[Path | str] = None
) -> list[dict[str, Any]]:
    """Search by battery serial OR vehicle id (case-insensitive substring)."""
    query = (query or "").strip()
    if not query:
        return list_battery_records(db_path=db_path)
    like = f"%{query}%"
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM battery_records "
            "WHERE battery_serial LIKE ? COLLATE NOCASE "
            "   OR vehicle_id LIKE ? COLLATE NOCASE "
            "ORDER BY updated_at DESC",
            (like, like),
        ).fetchall()
    return [_row_to_record(r) for r in rows]


def list_battery_records(
    limit: Optional[int] = None, offset: int = 0, db_path: Optional[Path | str] = None
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM battery_records ORDER BY updated_at DESC"
    params: tuple[Any, ...] = ()
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params = (limit, offset)
    with _connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_record(r) for r in rows]


def count_battery_records(db_path: Optional[Path | str] = None) -> int:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM battery_records").fetchone()
    return int(row["n"])


# --------------------------------------------------------------------- #
# classifications
# --------------------------------------------------------------------- #

def _row_to_classification(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["input_snapshot"] = json.loads(d.pop("input_snapshot_json"))
    return d


def create_classification(
    battery_record_id: int,
    prediction: int,
    prediction_label: str,
    probability: Optional[float],
    model_algorithm: str,
    model_trained_at: str,
    input_snapshot: dict[str, Any],
    db_path: Optional[Path | str] = None,
    created_at: Optional[str] = None,
) -> int:
    """Insert a classification. `created_at` defaults to now; it is accepted
    so seed_demo.py can backdate derived prior inspections, which is the only
    legitimate reason to set it."""
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO classifications "
            "(battery_record_id, prediction, prediction_label, probability, "
            " model_algorithm, model_trained_at, input_snapshot_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                battery_record_id,
                int(prediction),
                prediction_label,
                probability,
                model_algorithm,
                model_trained_at,
                json.dumps(input_snapshot),
                created_at or _now(),
            ),
        )
        return int(cur.lastrowid)


def get_classification(
    classification_id: int, db_path: Optional[Path | str] = None
) -> Optional[dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM classifications WHERE id = ?", (classification_id,)
        ).fetchone()
    return _row_to_classification(row) if row else None


def list_classifications_for_record(
    battery_record_id: int, db_path: Optional[Path | str] = None
) -> list[dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM classifications WHERE battery_record_id = ? "
            "ORDER BY created_at DESC, id DESC",
            (battery_record_id,),
        ).fetchall()
    return [_row_to_classification(r) for r in rows]


def count_classifications(db_path: Optional[Path | str] = None) -> int:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM classifications").fetchone()
    return int(row["n"])


# --------------------------------------------------------------------- #
# maintenance_assessments
# --------------------------------------------------------------------- #

def create_assessment(
    classification_id: int,
    assessment: str,
    recommendation: str,
    assessed_by: Optional[str] = None,
    db_path: Optional[Path | str] = None,
) -> int:
    """Attach an assessment to a classification. One assessment per classification."""
    assessment = (assessment or "").strip()
    recommendation = (recommendation or "").strip()
    if not assessment:
        raise ValueError("assessment text is required")
    if not recommendation:
        raise ValueError("recommendation text is required")
    try:
        with _connect(db_path) as conn:
            cur = conn.execute(
                "INSERT INTO maintenance_assessments "
                "(classification_id, assessment, recommendation, assessed_by, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (classification_id, assessment, recommendation, assessed_by, _now()),
            )
            return int(cur.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            f"classification {classification_id} already has an assessment"
        ) from exc


def get_assessment_for_classification(
    classification_id: int, db_path: Optional[Path | str] = None
) -> Optional[dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM maintenance_assessments WHERE classification_id = ?",
            (classification_id,),
        ).fetchone()
    return dict(row) if row else None


# --------------------------------------------------------------------- #
# Combined history view (UC-09 / FR-16)
# --------------------------------------------------------------------- #

def list_classification_history(
    serial: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    limit: Optional[int] = None,
    db_path: Optional[Path | str] = None,
) -> list[dict[str, Any]]:
    """Classifications joined with their battery record and assessment (if any),
    newest first. Optionally filtered by exact-ish serial/vehicle substring."""
    sql = """
        SELECT
            c.id AS classification_id,
            c.prediction, c.prediction_label, c.probability,
            c.model_algorithm, c.model_trained_at,
            c.input_snapshot_json, c.created_at AS classified_at,
            r.id AS battery_record_id, r.battery_serial, r.vehicle_id,
            a.id AS assessment_id, a.assessment, a.recommendation,
            a.assessed_by, a.created_at AS assessed_at
        FROM classifications c
        JOIN battery_records r ON r.id = c.battery_record_id
        LEFT JOIN maintenance_assessments a ON a.classification_id = c.id
        WHERE 1 = 1
    """
    params: list[Any] = []
    if serial:
        sql += " AND r.battery_serial LIKE ? COLLATE NOCASE"
        params.append(f"%{serial.strip()}%")
    if vehicle_id:
        sql += " AND r.vehicle_id LIKE ? COLLATE NOCASE"
        params.append(f"%{vehicle_id.strip()}%")
    sql += " ORDER BY c.created_at DESC, c.id DESC"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    with _connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    results = []
    for row in rows:
        d = dict(row)
        d["input_snapshot"] = json.loads(d.pop("input_snapshot_json"))
        results.append(d)
    return results
