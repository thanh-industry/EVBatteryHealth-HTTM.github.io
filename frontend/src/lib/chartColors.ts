// Chart color tokens as CSS variable references (SVG fill/stroke accept
// var(...) directly) - this keeps "no raw hex in components" true even
// inside Recharts, which needs real color strings rather than Tailwind
// classes. Values mirror DESIGN_SYSTEM.md section 1 exactly.

export const CATEGORICAL_COLORS = ['var(--chart-cat-1)', 'var(--chart-cat-2)', 'var(--chart-cat-3)'] as const

export const SEQUENTIAL_COLORS = [
  'var(--chart-seq-1)',
  'var(--chart-seq-2)',
  'var(--chart-seq-3)',
  'var(--chart-seq-4)',
] as const

export const STATUS_COLORS = {
  GOOD: 'var(--color-good)',
  MONITOR: 'var(--color-monitor)',
  CRITICAL: 'var(--color-critical)',
} as const

export const GRID_COLOR = 'var(--color-border)'
export const AXIS_TEXT_COLOR = 'var(--color-text-secondary)'

export const ALGORITHM_LABELS: Record<string, string> = {
  svm: 'SVM',
  random_forest: 'Random Forest',
  logistic_regression: 'Logistic Regression',
}
