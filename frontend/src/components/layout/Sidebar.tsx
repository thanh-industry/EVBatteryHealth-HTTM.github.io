import { BatteryCharging, LogOut } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import type { NavItem } from '../../lib/nav'
import type { User } from '../../types/api'
import { cx } from '../../lib/utils'

export interface SidebarProps {
  items: NavItem[]
  user: User
  onLogout: () => void
  onNavigate?: () => void
}

const ROLE_LABEL: Record<User['role'], string> = {
  data_scientist: 'Data Scientist',
  technician: 'Technician',
  ev_user: 'EV Owner',
}

export function Sidebar({ items, user, onLogout, onNavigate }: SidebarProps) {
  return (
    <div className="flex h-full w-full flex-col bg-surface">
      <div className="flex items-center gap-md px-xl py-xl">
        <BatteryCharging className="h-6 w-6 text-primary" aria-hidden="true" />
        <span className="text-sm font-semibold text-text-primary">EV Battery SoH</span>
      </div>
      <nav className="flex-1 overflow-y-auto px-md" aria-label="Primary">
        <ul className="flex flex-col gap-md">
          {items.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                onClick={onNavigate}
                className={({ isActive }) =>
                  cx(
                    'flex min-h-[44px] items-center gap-md rounded-md px-lg text-sm font-medium transition-colors duration-200',
                    isActive
                      ? 'bg-primary text-on-primary'
                      : 'text-text-secondary hover:bg-muted hover:text-text-primary',
                  )
                }
              >
                <item.icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className="border-t border-border px-xl py-lg">
        <p className="text-sm font-medium text-text-primary">{user.name}</p>
        <p className="text-caption text-text-muted">{ROLE_LABEL[user.role]}</p>
        <button
          type="button"
          onClick={onLogout}
          className="mt-md flex min-h-[44px] w-full items-center gap-md rounded-md px-lg text-sm font-medium text-text-secondary hover:bg-muted hover:text-text-primary"
        >
          <LogOut className="h-4 w-4" aria-hidden="true" />
          Log out
        </button>
      </div>
    </div>
  )
}
