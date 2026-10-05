import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useDatasets() {
  return useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.datasets.list(),
  })
}

export function useDataset(id: number | undefined) {
  return useQuery({
    queryKey: ['datasets', id],
    queryFn: () => api.datasets.get(id as number),
    enabled: id !== undefined,
  })
}

export function useDatasetPreview(id: number | undefined, limit = 20) {
  return useQuery({
    queryKey: ['datasets', id, 'preview', limit],
    queryFn: () => api.datasets.preview(id as number, limit),
    enabled: id !== undefined,
  })
}

export function useDatasetQuality(id: number | undefined) {
  return useQuery({
    queryKey: ['datasets', id, 'quality'],
    queryFn: () => api.datasets.quality(id as number),
    enabled: id !== undefined,
  })
}

export function useUploadDataset() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => api.datasets.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })
}

export function useDeleteDataset() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.datasets.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })
}
