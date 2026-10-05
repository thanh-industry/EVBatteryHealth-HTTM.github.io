import { BatteryCharging, Car } from 'lucide-react'
import type { Battery, Vehicle } from '../../types/api'
import { HealthStatusBadge } from '../data/HealthStatusBadge'
import { formatNumber } from '../../lib/utils'

export interface BatterySummaryCardProps {
  vehicle: Vehicle
  battery: Battery
}

export function BatterySummaryCard({ vehicle, battery }: BatterySummaryCardProps) {
  return (
    <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
      <div className="flex items-start justify-between gap-md">
        <div className="flex items-center gap-md">
          <Car className="h-6 w-6 text-primary" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-text-primary">{vehicle.vehicle_code}</p>
            <p className="text-caption text-text-muted">
              {[vehicle.brand, vehicle.model].filter(Boolean).join(' ') || 'Unknown model'}
            </p>
          </div>
        </div>
        <HealthStatusBadge healthClass={vehicle.health_class} />
      </div>

      <dl className="mt-lg grid grid-cols-2 gap-md sm:grid-cols-3">
        <div>
          <dt className="flex items-center gap-xs text-caption text-text-muted">
            <BatteryCharging className="h-3.5 w-3.5" aria-hidden="true" /> SoH
          </dt>
          <dd className="font-mono text-base font-semibold tabular-nums text-text-primary">
            {vehicle.current_soh !== null ? `${vehicle.current_soh.toFixed(1)}%` : '--'}
          </dd>
        </div>
        <div>
          <dt className="text-caption text-text-muted">Serial</dt>
          <dd className="font-mono text-sm text-text-primary">{battery.serial}</dd>
        </div>
        <div>
          <dt className="text-caption text-text-muted">Capacity</dt>
          <dd className="font-mono text-sm text-text-primary">
            {battery.capacity_kwh !== null ? `${formatNumber(battery.capacity_kwh, 1)} kWh` : '--'}
          </dd>
        </div>
        <div>
          <dt className="text-caption text-text-muted">Chemistry</dt>
          <dd className="text-sm text-text-primary">{battery.chemistry ?? '--'}</dd>
        </div>
        <div>
          <dt className="text-caption text-text-muted">Cycles</dt>
          <dd className="font-mono text-sm text-text-primary">{battery.cycle_count ?? '--'}</dd>
        </div>
        <div>
          <dt className="text-caption text-text-muted">Odometer</dt>
          <dd className="font-mono text-sm text-text-primary">
            {vehicle.odometer_km !== null ? `${formatNumber(vehicle.odometer_km, 0)} km` : '--'}
          </dd>
        </div>
      </dl>
    </div>
  )
}
