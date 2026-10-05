// TypeScript interfaces mirroring ARCHITECTURE.md section 4 (API contract) exactly.
// Do not add fields that are not in the contract. Do not rename wire values.

export type Role = 'data_scientist' | 'technician' | 'ev_user'

export interface User {
  id: number
  email: string
  name: string
  role: Role
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  token: string
  user: User
}

// ---- Config ----

export interface Thresholds {
  good_min: number
  monitor_min: number
}

// ---- Health classification ----

export type HealthClass = 'GOOD' | 'MONITOR' | 'CRITICAL'

// ---- Datasets ----

export interface Dataset {
  id: number
  name: string
  filename: string
  row_count: number
  column_count: number
  missing_cells: number
  missing_pct: number
  duplicate_rows: number
  uploaded_at: string
  status: 'ready' | 'invalid'
  message: string | null
}

export interface DatasetPreview {
  columns: string[]
  rows: Record<string, unknown>[]
}

export interface ClassDistributionEntry {
  class: HealthClass
  count: number
}

export interface MissingByColumnEntry {
  column: string
  missing: number
  missing_pct: number
}

export interface NumericSummaryEntry {
  column: string
  min: number
  max: number
  mean: number
  std: number
}

export interface SohHistogramBin {
  bin_start: number
  bin_end: number
  count: number
}

export interface ExcludedColumnEntry {
  column: string
  reason: string
}

export interface DataQuality {
  dataset_id: number
  row_count: number
  labelled_rows: number
  dropped_missing_label: number
  duplicate_rows: number
  class_distribution: ClassDistributionEntry[]
  missing_by_column: MissingByColumnEntry[]
  numeric_summary: NumericSummaryEntry[]
  soh_histogram: SohHistogramBin[]
  excluded_columns: ExcludedColumnEntry[]
}

// ---- Training ----

export type Algorithm = 'svm' | 'random_forest' | 'logistic_regression'

export interface TrainingRequest {
  dataset_id: number
  algorithm: Algorithm
  test_size?: number
  params?: Record<string, number | string | boolean>
}

export interface PerClassMetric {
  class: string
  precision: number
  recall: number
  f1: number
  support: number
}

export interface Metrics {
  accuracy: number
  precision_macro: number
  recall_macro: number
  f1_macro: number
  per_class: PerClassMetric[]
}

export interface ConfusionMatrix {
  labels: string[]
  matrix: number[][]
}

export interface FeatureImportanceEntry {
  feature: string
  importance: number
}

export type TrainingStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface TrainingRun {
  id: number
  dataset_id: number
  dataset_name: string
  algorithm: Algorithm
  params: Record<string, unknown>
  test_size: number
  status: TrainingStatus
  error: string | null
  started_at: string
  completed_at: string | null
  duration_seconds: number | null
  train_rows: number | null
  test_rows: number | null
  metrics: Metrics | null
  confusion_matrix: ConfusionMatrix | null
  feature_importance: FeatureImportanceEntry[] | null
  supports_probability: boolean
  is_deployed: boolean
  version: string | null
}

// ---- Models & deployment ----

export interface ActiveModel {
  run_id: number
  version: string
  algorithm: string
  dataset_name: string
  deployed_at: string
  metrics: Metrics
  supports_probability: boolean
}

// ---- Vehicles / batteries ----

export interface Vehicle {
  vehicle_code: string
  brand: string | null
  model: string | null
  vehicle_type: string | null
  manufacturing_year: number | null
  drive_type: string | null
  odometer_km: number | null
  fleet_or_private: string | null
  battery_serial: string
  current_soh: number | null
  health_class: HealthClass | null
}

export interface Battery {
  serial: string
  manufacturer: string | null
  chemistry: string | null
  capacity_kwh: number | null
  cycle_count: number | null
  current_soh: number | null
  health_class: HealthClass | null
}

export interface Measurement {
  recorded_at: string
  soh: number
  state_of_charge: number | null
  internal_resistance: number | null
  cell_voltage_avg: number | null
  cell_temperature_avg: number | null
  cell_temperature_max: number | null
  charge_efficiency: number | null
  cycle_count: number | null
}

export interface VehicleDetail {
  vehicle: Vehicle
  battery: Battery
  latest_measurement: Measurement | null
  measurement_count: number
  last_diagnostic_at: string | null
}

// ---- Diagnostics ----

export interface DiagnosticRequest {
  code: string
  notes?: string
}

export interface ClassProbability {
  class: string
  probability: number
}

export interface Diagnostic {
  id: number
  vehicle_code: string
  battery_serial: string
  created_at: string
  soh: number
  predicted_class: HealthClass
  confidence: number | null
  class_probabilities: ClassProbability[] | null
  model_version: string
  model_algorithm: string
  technician_name: string | null
  recommendation: string
  notes: string | null
}

export interface DiagnosticSummary {
  today_count: number
  good_count: number
  monitor_count: number
  critical_count: number
  recent: Diagnostic[]
}

// ---- EV user ----

export interface UserBatteryOverview {
  vehicle: Vehicle
  battery: Battery
  current_soh: number | null
  health_class: HealthClass | null
  last_checked_at: string | null
  soh_change_30d: number | null
  recommendation: string
  history: Measurement[]
}

export interface MaintenanceItem {
  id: number
  title: string
  description: string
  severity: 'info' | 'warning' | 'critical'
  due_at: string | null
  completed: boolean
}

// ---- Notifications ----

export type NotificationType = 'degradation' | 'critical_health' | 'maintenance_reminder' | 'system'

export interface Notification {
  id: number
  type: NotificationType
  severity: 'info' | 'warning' | 'critical'
  title: string
  body: string
  created_at: string
  read_at: string | null
}

// ---- Error envelope ----

export interface ValidationErrorItem {
  loc: (string | number)[]
  msg: string
  type: string
}

export interface ApiErrorEnvelope {
  detail: string | ValidationErrorItem[]
}
