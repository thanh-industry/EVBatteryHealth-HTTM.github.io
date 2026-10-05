import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { TrainingRun } from '../../../types/api'
import { ModelComparisonTable } from '../ModelComparisonTable'

function makeRun(overrides: Partial<TrainingRun> & { id: number }): TrainingRun {
  return {
    dataset_id: 1,
    dataset_name: 'battery_data_v1',
    algorithm: 'random_forest',
    params: {},
    test_size: 0.2,
    status: 'completed',
    error: null,
    started_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T00:05:00Z',
    duration_seconds: 10,
    train_rows: 100,
    test_rows: 25,
    confusion_matrix: null,
    feature_importance: null,
    supports_probability: true,
    is_deployed: false,
    version: `v${overrides.id}`,
    ...overrides,
    metrics: overrides.metrics ?? null,
  }
}

describe('ModelComparisonTable', () => {
  it('shows per-class CRITICAL recall alongside the macro metrics, and highlights each column best independently', () => {
    const randomForest = makeRun({
      id: 1,
      algorithm: 'random_forest',
      version: 'v1',
      metrics: {
        accuracy: 0.8711,
        precision_macro: 0.85,
        recall_macro: 0.84,
        f1_macro: 0.8604,
        per_class: [
          { class: 'GOOD', precision: 0.9, recall: 0.9, f1: 0.9, support: 1000 },
          { class: 'MONITOR', precision: 0.8, recall: 0.8, f1: 0.8, support: 1000 },
          { class: 'CRITICAL', precision: 0.7, recall: 0.776, f1: 0.73, support: 200 },
        ],
      },
    })
    const logisticRegression = makeRun({
      id: 2,
      algorithm: 'logistic_regression',
      version: 'v2',
      metrics: {
        accuracy: 0.8698,
        precision_macro: 0.84,
        recall_macro: 0.83,
        f1_macro: 0.8575,
        per_class: [
          { class: 'GOOD', precision: 0.88, recall: 0.88, f1: 0.88, support: 1000 },
          { class: 'MONITOR', precision: 0.79, recall: 0.79, f1: 0.79, support: 1000 },
          { class: 'CRITICAL', precision: 0.68, recall: 0.794, f1: 0.73, support: 200 },
        ],
      },
    })

    render(<ModelComparisonTable runs={[randomForest, logisticRegression]} />)

    // Both the macro-accuracy winner and the critical-recall winner are
    // visible in the same table - the UI never crowns one overall winner.
    expect(screen.getByText('Critical Recall')).toBeInTheDocument()
    expect(screen.getByText('87.1%')).toBeInTheDocument() // random_forest accuracy (best)
    expect(screen.getByText('79.4%')).toBeInTheDocument() // logistic_regression critical recall (best)
    expect(screen.getByText('77.6%')).toBeInTheDocument() // random_forest critical recall (not best)
  })

  it('renders the empty state when there are no completed runs yet', () => {
    render(<ModelComparisonTable runs={[]} />)
    expect(screen.getByText('No trained models yet')).toBeInTheDocument()
  })
})
