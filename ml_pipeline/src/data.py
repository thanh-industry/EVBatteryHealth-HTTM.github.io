"""Data loading and profiling for the EV battery failure dataset.

Also holds the static feature metadata (group + human readable label) used
later by export.py to build the feature_spec shipped in the model bundle.
See SPEC_CONTRACT.md section 1 for the measured dataset facts this module
encodes (column counts, identifier columns, categorical columns).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

# --- Column roles (measured facts, see SPEC_CONTRACT.md section 1) ---------

TARGET_COL = "battery_failure"

# Record identifiers: never enter the feature matrix.
ID_COLS: List[str] = ["vehicle_id", "battery_serial"]

CLASS_LABELS: Dict[int, str] = {0: "No Failure", 1: "Failure"}

# The 8 categorical columns (measured). Everything else except target/ids is numeric.
CATEGORICAL_COLS: List[str] = [
    "vehicle_brand",
    "vehicle_model",
    "vehicle_type",
    "battery_manufacturer",
    "battery_chemistry",
    "drive_type",
    "fleet_or_private",
    "terrain_type",
]

# --- Feature groups (spec section 3.1: UI layout order) --------------------

FEATURE_GROUPS: Dict[str, str] = {
    # identity (8)
    "vehicle_brand": "identity",
    "vehicle_model": "identity",
    "vehicle_type": "identity",
    "manufacturing_year": "identity",
    "drive_type": "identity",
    "fleet_or_private": "identity",
    "odometer_km": "identity",
    "vehicle_age_years": "identity",
    # battery_spec (3)
    "battery_manufacturer": "battery_spec",
    "battery_chemistry": "battery_spec",
    "battery_capacity_kwh": "battery_spec",
    # battery_state (8)
    "cycle_count": "battery_state",
    "battery_health_percent": "battery_state",
    "state_of_charge": "battery_state",
    "depth_of_discharge": "battery_state",
    "state_of_health": "battery_state",
    "remaining_capacity": "battery_state",
    "capacity_loss_percent": "battery_state",
    "predicted_remaining_life_cycles": "battery_state",
    # electrical (8)
    "cell_voltage_avg": "electrical",
    "cell_voltage_std": "electrical",
    "pack_voltage": "electrical",
    "cell_temperature_avg": "electrical",
    "cell_temperature_max": "electrical",
    "internal_resistance": "electrical",
    "voltage_imbalance": "electrical",
    "temperature_variance": "electrical",
    # charging (12)
    "charge_efficiency": "charging",
    "discharge_efficiency": "charging",
    "charging_cycles_last_month": "charging",
    "fast_charge_ratio": "charging",
    "slow_charge_ratio": "charging",
    "average_charge_power_kw": "charging",
    "average_charging_time": "charging",
    "overnight_charging_ratio": "charging",
    "home_charging_ratio": "charging",
    "charging_interruptions": "charging",
    "overcharge_events": "charging",
    "charging_quality_score": "charging",
    # driving (9)
    "average_speed": "driving",
    "average_trip_distance": "driving",
    "aggressive_acceleration_score": "driving",
    "hard_braking_score": "driving",
    "regenerative_braking_usage": "driving",
    "highway_driving_ratio": "driving",
    "city_driving_ratio": "driving",
    "daily_distance": "driving",
    "driving_stress_score": "driving",
    # environment (7)
    "average_ambient_temperature": "environment",
    "maximum_temperature": "environment",
    "minimum_temperature": "environment",
    "humidity": "environment",
    "altitude": "environment",
    "terrain_type": "environment",
    "dust_exposure": "environment",
    # maintenance (5)
    "last_service_days": "maintenance",
    "cooling_system_health": "maintenance",
    "firmware_updates": "maintenance",
    "previous_faults": "maintenance",
    "maintenance_score": "maintenance",
    # risk (7)
    "thermal_runaway_risk": "risk",
    "sensor_fault_count": "risk",
    "BMS_warning_count": "risk",
    "abnormal_voltage_events": "risk",
    "battery_stress_index": "risk",
    "aging_score": "risk",
    "thermal_health_score": "risk",
}

FEATURE_GROUP_ORDER: List[str] = [
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

# --- Human readable labels --------------------------------------------------
# Explicit overrides for units / acronyms; anything not listed falls back to
# `humanize()` below (title-cased, underscores to spaces).

FEATURE_LABEL_OVERRIDES: Dict[str, str] = {
    "manufacturing_year": "Manufacturing Year",
    "odometer_km": "Odometer Reading (km)",
    "vehicle_age_years": "Vehicle Age (years)",
    "battery_capacity_kwh": "Battery Capacity (kWh)",
    "cycle_count": "Charge Cycle Count",
    "battery_health_percent": "Battery Health (%)",
    "state_of_charge": "State of Charge (%)",
    "depth_of_discharge": "Depth of Discharge (%)",
    "state_of_health": "State of Health (%)",
    "remaining_capacity": "Remaining Capacity (kWh)",
    "capacity_loss_percent": "Capacity Loss (%)",
    "predicted_remaining_life_cycles": "Predicted Remaining Life (cycles)",
    "cell_voltage_avg": "Average Cell Voltage (V)",
    "cell_voltage_std": "Cell Voltage Std. Dev. (V)",
    "pack_voltage": "Pack Voltage (V)",
    "cell_temperature_avg": "Average Cell Temperature (C)",
    "cell_temperature_max": "Maximum Cell Temperature (C)",
    "internal_resistance": "Internal Resistance (mOhm)",
    "voltage_imbalance": "Cell Voltage Imbalance (V)",
    "temperature_variance": "Cell Temperature Variance",
    "charge_efficiency": "Charge Efficiency (%)",
    "discharge_efficiency": "Discharge Efficiency (%)",
    "charging_cycles_last_month": "Charging Cycles (last month)",
    "fast_charge_ratio": "Fast Charge Ratio",
    "slow_charge_ratio": "Slow Charge Ratio",
    "average_charge_power_kw": "Average Charge Power (kW)",
    "average_charging_time": "Average Charging Time (h)",
    "overnight_charging_ratio": "Overnight Charging Ratio",
    "home_charging_ratio": "Home Charging Ratio",
    "charging_interruptions": "Charging Interruptions (count)",
    "overcharge_events": "Overcharge Events (count)",
    "charging_quality_score": "Charging Quality Score",
    "average_speed": "Average Speed (km/h)",
    "average_trip_distance": "Average Trip Distance (km)",
    "aggressive_acceleration_score": "Aggressive Acceleration Score",
    "hard_braking_score": "Hard Braking Score",
    "regenerative_braking_usage": "Regenerative Braking Usage",
    "highway_driving_ratio": "Highway Driving Ratio",
    "city_driving_ratio": "City Driving Ratio",
    "daily_distance": "Daily Distance (km)",
    "driving_stress_score": "Driving Stress Score",
    "average_ambient_temperature": "Average Ambient Temperature (C)",
    "maximum_temperature": "Maximum Ambient Temperature (C)",
    "minimum_temperature": "Minimum Ambient Temperature (C)",
    "humidity": "Humidity (%)",
    "altitude": "Altitude (m)",
    "dust_exposure": "Dust Exposure Level",
    "last_service_days": "Days Since Last Service",
    "cooling_system_health": "Cooling System Health (%)",
    "firmware_updates": "Firmware Update Count",
    "previous_faults": "Previous Fault Count",
    "maintenance_score": "Maintenance Score",
    "thermal_runaway_risk": "Thermal Runaway Risk Score",
    "sensor_fault_count": "Sensor Fault Count",
    "BMS_warning_count": "BMS Warning Count",
    "abnormal_voltage_events": "Abnormal Voltage Events (count)",
    "battery_stress_index": "Battery Stress Index",
    "aging_score": "Aging Score",
    "thermal_health_score": "Thermal Health Score",
    "vehicle_brand": "Vehicle Brand",
    "vehicle_model": "Vehicle Model",
    "vehicle_type": "Vehicle Type",
    "drive_type": "Drive Type",
    "fleet_or_private": "Fleet or Private",
    "battery_manufacturer": "Battery Manufacturer",
    "battery_chemistry": "Battery Chemistry",
    "terrain_type": "Terrain Type",
}


def humanize(column_name: str) -> str:
    """Fallback human-readable label: underscores to spaces, title case."""
    return column_name.replace("_", " ").strip().title()


def feature_label(column_name: str) -> str:
    """Human readable label for a feature, preferring the curated override."""
    return FEATURE_LABEL_OVERRIDES.get(column_name, humanize(column_name))


# --- Loading and profiling --------------------------------------------------


def load_dataset(csv_path: str) -> pd.DataFrame:
    """Load the EV battery dataset from a CSV file."""
    return pd.read_csv(csv_path)


def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """All feature columns (not id, not target) that are not categorical."""
    feature_cols = get_feature_columns(df)
    return [c for c in feature_cols if c not in CATEGORICAL_COLS]


def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    """The categorical feature columns present in df, in canonical order."""
    return [c for c in CATEGORICAL_COLS if c in df.columns]


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """All 67 feature columns: every column except identifiers and the target."""
    exclude = set(ID_COLS) | {TARGET_COL}
    return [c for c in df.columns if c not in exclude]


def split_features_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) with identifier columns and the target removed from X."""
    feature_cols = get_feature_columns(df)
    X = df[feature_cols].copy()
    y = df[TARGET_COL].astype(int).copy()
    return X, y


def missing_value_profile(df: pd.DataFrame) -> pd.Series:
    """Percentage of missing values per column, sorted descending."""
    return (df.isna().mean() * 100.0).sort_values(ascending=False)


def class_balance(y: pd.Series) -> pd.DataFrame:
    """Class counts and percentages, labelled with CLASS_LABELS."""
    counts = y.value_counts().sort_index()
    pct = (y.value_counts(normalize=True).sort_index() * 100.0)
    out = pd.DataFrame({"count": counts, "percent": pct})
    out.index = [CLASS_LABELS.get(i, str(i)) for i in out.index]
    return out
