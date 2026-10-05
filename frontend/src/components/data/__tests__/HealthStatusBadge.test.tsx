import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { HealthStatusBadge } from '../HealthStatusBadge'

describe('HealthStatusBadge', () => {
  it('renders the text label for GOOD, not just a color', () => {
    render(<HealthStatusBadge healthClass="GOOD" />)
    expect(screen.getByText('Good')).toBeInTheDocument()
  })

  it('renders the text label for MONITOR', () => {
    render(<HealthStatusBadge healthClass="MONITOR" />)
    expect(screen.getByText('Needs Monitoring')).toBeInTheDocument()
  })

  it('renders the text label for CRITICAL', () => {
    render(<HealthStatusBadge healthClass="CRITICAL" />)
    expect(screen.getByText('Dangerous')).toBeInTheDocument()
  })

  it('renders an icon alongside the text (icon + text + color, never color alone)', () => {
    const { container } = render(<HealthStatusBadge healthClass="CRITICAL" />)
    expect(container.querySelector('svg')).toBeTruthy()
    expect(screen.getByText('Dangerous')).toBeInTheDocument()
  })

  it('renders an explicit "Unknown" label rather than nothing when the class is missing', () => {
    render(<HealthStatusBadge healthClass={null} />)
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })
})
