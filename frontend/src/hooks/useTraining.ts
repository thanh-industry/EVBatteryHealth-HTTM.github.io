import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { TrainingRequest, TrainingStatus } from '../types/api'

const ACTIVE_STATUSES: TrainingStatus[] = ['pending', 'running']

export function useTrainingRuns() {
  return useQuery({
    queryKey: ['training', 'runs'],
    queryFn: () => api.training.list(),
    refetchInterval: (query) => {
      const runs = query.state.data
      const hasActive = runs?.some((run) => ACTIVE_STATUSES.includes(run.status))
      return hasActive ? 3000 : false
    },
  })
}

export function useTrainingRun(id: number | undefined) {
  return useQuery({
    queryKey: ['training', 'runs', id],
    queryFn: () => api.training.get(id as number),
    enabled: id !== undefined,
    refetchInterval: (query) => {
      const run = query.state.data
      return run && ACTIVE_STATUSES.includes(run.status) ? 2000 : false
    },
  })
}

export function useCreateTrainingRun() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: TrainingRequest) => api.training.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training', 'runs'] })
    },
  })
}
