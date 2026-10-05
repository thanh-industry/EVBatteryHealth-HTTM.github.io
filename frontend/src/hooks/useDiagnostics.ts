import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { DiagnosticRequest } from '../types/api'

export function useDiagnosticsList(params?: { code?: string; limit?: number }) {
  return useQuery({
    queryKey: ['diagnostics', params ?? {}],
    queryFn: () => api.diagnostics.list(params),
  })
}

export function useDiagnosticsSummary() {
  return useQuery({
    queryKey: ['diagnostics', 'summary'],
    queryFn: () => api.diagnostics.summary(),
  })
}

export function useBatteryLookup(code: string | undefined) {
  return useQuery({
    queryKey: ['batteries', 'lookup', code],
    queryFn: () => api.batteries.lookup(code as string),
    enabled: !!code,
    retry: false,
  })
}

export function useRunDiagnostic() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: DiagnosticRequest) => api.diagnostics.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diagnostics'] })
    },
  })
}
