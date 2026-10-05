import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useDeployableModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: () => api.models.list(),
  })
}

export function useActiveModel() {
  return useQuery({
    queryKey: ['models', 'active'],
    queryFn: () => api.models.active(),
  })
}

export function useDeployModel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (runId: number) => api.models.deploy(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      queryClient.invalidateQueries({ queryKey: ['training', 'runs'] })
    },
  })
}
