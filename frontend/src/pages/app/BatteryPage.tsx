import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { PageHeader } from '../../components/layout/PageHeader'
import { BatterySummaryCard } from '../../components/battery/BatterySummaryCard'
import { TrendChart } from '../../components/charts/TrendChart'
import { useMyBattery, useMyBatteryHistory } from '../../hooks/useMe'
import { useThresholds } from '../../hooks/useThresholds'

export function BatteryPage() {
  const batteryQuery = useMyBattery()
  const historyQuery = useMyBatteryHistory()
  const thresholdsQuery = useThresholds()

  const isLoading = batteryQuery.isLoading || historyQuery.isLoading
  const firstError = batteryQuery.error ?? historyQuery.error

  if (isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Battery Detail" />
        <LoadingSkeleton variant="card" />
        <LoadingSkeleton variant="chart" />
      </div>
    )
  }

  if (firstError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Battery Detail" />
        <ErrorState
          error={firstError}
          onRetry={() => {
            batteryQuery.refetch()
            historyQuery.refetch()
          }}
        />
      </div>
    )
  }

  const overview = batteryQuery.data
  if (!overview) return null

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="Battery Detail" description={overview.vehicle.vehicle_code} />
      <BatterySummaryCard vehicle={overview.vehicle} battery={overview.battery} />
      <TrendChart measurements={historyQuery.data ?? []} thresholds={thresholdsQuery.data} />
    </div>
  )
}
