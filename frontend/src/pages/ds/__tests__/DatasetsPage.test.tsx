import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Dataset } from '../../../types/api'
import { DatasetsPage } from '../DatasetsPage'

vi.mock('../../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../../lib/api')>('../../../lib/api')
  return {
    ...actual,
    api: {
      ...actual.api,
      datasets: { ...actual.api.datasets, list: vi.fn(), upload: vi.fn(), remove: vi.fn() },
    },
  }
})

import { api } from '../../../lib/api'

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DatasetsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DatasetsPage', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows the empty state and the uploader when there are no datasets', async () => {
    vi.mocked(api.datasets.list).mockResolvedValue([])

    renderWithProviders()

    expect(await screen.findByText('No datasets uploaded yet')).toBeInTheDocument()
    expect(screen.getByText(/drag and drop a csv file here/i)).toBeInTheDocument()
  })

  it('lists real datasets from the API with their row counts and status', async () => {
    const dataset: Dataset = {
      id: 7,
      name: 'ev_battery_2026',
      filename: 'ev_battery_2026.csv',
      row_count: 19044,
      column_count: 70,
      missing_cells: 500,
      missing_pct: 2.1,
      duplicate_rows: 3,
      uploaded_at: '2026-02-01T00:00:00Z',
      status: 'ready',
      message: null,
    }
    vi.mocked(api.datasets.list).mockResolvedValue([dataset])

    renderWithProviders()

    expect(await screen.findByText('ev_battery_2026')).toBeInTheDocument()
    expect(screen.getByText('19,044')).toBeInTheDocument()
    expect(screen.getByText('ready')).toBeInTheDocument()
  })
})
