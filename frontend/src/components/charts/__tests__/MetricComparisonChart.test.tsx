import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Metrics } from '../../../types/api'
import { ALGORITHM_COLORS } from '../../../lib/chartColors'
import { MetricComparisonChart } from '../MetricComparisonChart'

const metrics: Metrics = {
  accuracy: 0.87,
  precision_macro: 0.85,
  recall_macro: 0.84,
  f1_macro: 0.86,
  per_class: [],
}

describe('MetricComparisonChart', () => {
  it('shows the empty state with no entries', () => {
    render(<MetricComparisonChart entries={[]} />)
    expect(screen.getByText('Train at least one model to see a comparison.')).toBeInTheDocument()
  })

  it('renders without crashing for a single series and for three series', () => {
    const { rerender } = render(<MetricComparisonChart entries={[{ algorithm: 'random_forest', metrics }]} />)
    expect(screen.getByText('Model Comparison')).toBeInTheDocument()

    rerender(
      <MetricComparisonChart
        entries={[
          { algorithm: 'random_forest', metrics },
          { algorithm: 'svm', metrics },
          { algorithm: 'logistic_regression', metrics },
        ]}
      />,
    )
    expect(screen.getByText('Model Comparison')).toBeInTheDocument()
  })
})

describe('ALGORITHM_COLORS', () => {
  it('assigns each algorithm a fixed categorical color, never cycled by render order', () => {
    expect(ALGORITHM_COLORS.svm).toBe('var(--chart-cat-1)')
    expect(ALGORITHM_COLORS.random_forest).toBe('var(--chart-cat-2)')
    expect(ALGORITHM_COLORS.logistic_regression).toBe('var(--chart-cat-3)')
    // Every algorithm maps to a distinct color.
    const values = Object.values(ALGORITHM_COLORS)
    expect(new Set(values).size).toBe(values.length)
  })
})
