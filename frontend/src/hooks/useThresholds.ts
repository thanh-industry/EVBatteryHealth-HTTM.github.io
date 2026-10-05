import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useThresholds() {
  return useQuery({
    queryKey: ['config', 'thresholds'],
    queryFn: () => api.config.thresholds(),
    staleTime: Infinity,
  })
}
