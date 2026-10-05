import { NavLink } from 'react-router-dom'
import type { NavItem } from '../../lib/nav'
import { cx } from '../../lib/utils'

export interface MobileNavProps {
  items: NavItem[]
}

/** Bottom tab bar for small screens. Caps at 5 items by design. */
export function MobileNav({ items }: MobileNavProps) {
  const visible = items.slice(0, 5)
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-surface shadow-lg md:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      {visible.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            cx(
              'flex min-h-[44px] flex-1 flex-col items-center justify-center gap-xs py-sm text-caption font-medium',
              isActive ? 'text-primary' : 'text-text-muted',
            )
          }
        >
          <item.icon className="h-5 w-5" aria-hidden="true" />
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}
