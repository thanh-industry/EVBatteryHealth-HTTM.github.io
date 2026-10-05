import { describe, expect, it } from 'vitest'
import { classifySoh, getHealthMeta, HEALTH_META } from '../health'

describe('getHealthMeta', () => {
  it('maps every health class to a label, icon and token classes - never color alone', () => {
    expect(getHealthMeta('GOOD')?.label).toBe('Good')
    expect(getHealthMeta('MONITOR')?.label).toBe('Needs Monitoring')
    expect(getHealthMeta('CRITICAL')?.label).toBe('Dangerous')
    for (const cls of ['GOOD', 'MONITOR', 'CRITICAL'] as const) {
      expect(HEALTH_META[cls].Icon).toBeTruthy()
      expect(HEALTH_META[cls].textClass).toMatch(/^text-/)
    }
  })

  it('returns null for a missing classification rather than guessing', () => {
    expect(getHealthMeta(null)).toBeNull()
    expect(getHealthMeta(undefined)).toBeNull()
  })
})

describe('classifySoh', () => {
  const thresholds = { good_min: 85, monitor_min: 70 }

  it('classifies using thresholds from the API, never hardcoded inline', () => {
    expect(classifySoh(90, thresholds)).toBe('GOOD')
    expect(classifySoh(85, thresholds)).toBe('GOOD')
    expect(classifySoh(75, thresholds)).toBe('MONITOR')
    expect(classifySoh(70, thresholds)).toBe('MONITOR')
    expect(classifySoh(50, thresholds)).toBe('CRITICAL')
  })

  it('returns null rather than guessing when inputs are missing', () => {
    expect(classifySoh(null, thresholds)).toBeNull()
    expect(classifySoh(90, null)).toBeNull()
    expect(classifySoh(undefined, undefined)).toBeNull()
  })
})
