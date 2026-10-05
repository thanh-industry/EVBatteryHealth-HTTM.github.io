import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Dataset, TrainingRun } from '../../../types/api'
import { OverviewPage } from '../OverviewPage'

vi.mock('../../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../../lib/api')>('../../../lib/api')
  return {
    ...actual,
    api: {
      ...actual.api,
      datasets: { ...actual.api.datasets, list: vi.fn() },
      training: { ...actual.api.training, list: vi.fn() },
      models: { ...actual.api.models, active: vi.fn() },
    },
  }
})

import { api } from '../../../lib/api'

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <OverviewPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const sampleDataset: Dataset = {
  id: 1,
  name: 'battery_data_v1',
  filename: 'battery.csv',
  row_count: 20000,
  column_count: 70,
  missing_cells: 1000,
  missing_pct: 3.5,
  duplicate_rows: 0,
  uploaded_at: '2026-01-01T00:00:00Z',
  status: 'ready',
  message: null,
}

const sampleRun: TrainingRun = {
  id: 1,
  dataset_id: 1,
  dataset_name: 'battery_data_v1',
  algorithm: 'random_forest',
  params: { n_estimators: 200 },
  test_size: 0.2,
  status: 'completed',
  error: null,
  started_at: '2026-01-02T00:00:00Z',
  completed_at: '2026-01-02T00:05:00Z',
  duration_seconds: 42,
  train_rows: 16000,
  test_rows: 4000,
  metrics: {
    accuracy: 0.91,
    precision_macro: 0.88,
    recall_macro: 0.85,
    f1_macro: 0.86,
    per_class: [],
  },
  confusion_matrix: null,
  feature_importance: null,
  supports_probability: true,
  is_deployed: false,
  version: 'v1',
}

describe('OverviewPage', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows the empty state when no training runs exist yet', async () => {
    vi.mocked(api.datasets.list).mockResolvedValue([])
    vi.mocked(api.training.list).mockResolvedValue([])
    vi.mocked(api.models.active).mockResolvedValue(null)

    renderWithProviders()

    expect(await screen.findByText('No model trained yet')).toBeInTheDocument()
  })

  it('renders real KPI numbers from the API once data has loaded - never hardcoded', async () => {
    vi.mocked(api.datasets.list).mockResolvedValue([sampleDataset])
    vi.mocked(api.training.list).mockResolvedValue([sampleRun])
    vi.mocked(api.models.active).mockResolvedValue(null)

    renderWithProviders()

    expect(await screen.findByRole('heading', { name: 'Recent training runs' })).toBeInTheDocument()
    expect(screen.getByText('Datasets')).toBeInTheDocument()
    expect(screen.getAllByText('1').length).toBeGreaterThan(0)
    expect(screen.getByText('91.0')).toBeInTheDocument()
  })

  it('shows an error state when the API is unreachable', async () => {
    const { ApiError } = await vi.importActual<typeof import('../../../lib/api')>('../../../lib/api')
    vi.mocked(api.datasets.list).mockRejectedValue(new ApiError('Unable to reach the server.', 0))
    vi.mocked(api.training.list).mockResolvedValue([])
    vi.mocked(api.models.active).mockResolvedValue(null)

    renderWithProviders()

    expect(await screen.findByText('Unable to reach the server.')).toBeInTheDocument()
  })
})
