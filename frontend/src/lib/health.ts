// Single source of truth for mapping a health classification to its
// label, icon and token classes. Do not duplicate this mapping elsewhere.
// Thresholds that decide the classification are never hardcoded here -
// they come from GET /api/config/thresholds (see hooks/useThresholds.ts).

import { AlertOctagon, AlertTriangle, ShieldCheck, type LucideIcon } from 'lucide-react'
import type { HealthClass, Thresholds } from '../types/api'

export interface HealthMeta {
  value: HealthClass
  label: string
  Icon: LucideIcon
  textClass: string
  bgClass: string
  borderClass: string
}

export const HEALTH_META: Record<HealthClass, HealthMeta> = {
  GOOD: {
    value: 'GOOD',
    label: 'Good',
    Icon: ShieldCheck,
    textClass: 'text-good',
    bgClass: 'bg-good-bg',
    borderClass: 'border-good',
  },
  MONITOR: {
    value: 'MONITOR',
    label: 'Needs Monitoring',
    Icon: AlertTriangle,
    textClass: 'text-monitor',
    bgClass: 'bg-monitor-bg',
    borderClass: 'border-monitor',
  },
  CRITICAL: {
    value: 'CRITICAL',
    label: 'Dangerous',
    Icon: AlertOctagon,
    textClass: 'text-critical',
    bgClass: 'bg-critical-bg',
    borderClass: 'border-critical',
  },
}

export function getHealthMeta(healthClass: HealthClass | null | undefined): HealthMeta | null {
  if (!healthClass) return null
  return HEALTH_META[healthClass] ?? null
}

/**
 * Derive a health class from a raw SoH value using thresholds fetched from
 * the backend. Returns null if either input is missing - callers must then
 * render an "unknown" state rather than guessing.
 */
export function classifySoh(
  soh: number | null | undefined,
  thresholds: Thresholds | null | undefined,
): HealthClass | null {
  if (soh === null || soh === undefined || Number.isNaN(soh) || !thresholds) return null
  if (soh >= thresholds.good_min) return 'GOOD'
  if (soh >= thresholds.monitor_min) return 'MONITOR'
  return 'CRITICAL'
}
