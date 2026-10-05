import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useVehicles(q: string | undefined) {
  return useQuery({
    queryKey: ['vehicles', q ?? ''],
    queryFn: () => api.vehicles.list(q),
  })
}

export function useVehicleDetail(vehicleCode: string | undefined) {
  return useQuery({
    queryKey: ['vehicles', vehicleCode],
    queryFn: () => api.vehicles.get(vehicleCode as string),
    enabled: !!vehicleCode,
  })
}

export function useBatteryMeasurements(serial: string | undefined) {
  return useQuery({
    queryKey: ['batteries', serial, 'measurements'],
    queryFn: () => api.batteries.measurements(serial as string),
    enabled: !!serial,
  })
}
