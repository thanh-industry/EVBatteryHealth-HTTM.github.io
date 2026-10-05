import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useMyBattery() {
  return useQuery({
    queryKey: ['me', 'battery'],
    queryFn: () => api.me.battery(),
  })
}

export function useMyBatteryHistory() {
  return useQuery({
    queryKey: ['me', 'battery', 'history'],
    queryFn: () => api.me.batteryHistory(),
  })
}

export function useMyMaintenance() {
  return useQuery({
    queryKey: ['me', 'maintenance'],
    queryFn: () => api.me.maintenance(),
  })
}
