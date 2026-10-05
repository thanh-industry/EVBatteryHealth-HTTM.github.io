import { Menu, X } from 'lucide-react'
import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { useAuth } from '../../lib/auth'
import { NAV_BY_ROLE } from '../../lib/nav'
import { cx } from '../../lib/utils'
import { MobileNav } from './MobileNav'
import { Sidebar } from './Sidebar'

export function AppShell() {
  const { user, logout } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)

  if (!user) return null

  const items = NAV_BY_ROLE[user.role]
  const useBottomNav = items.length <= 5

  return (
    <div className="flex min-h-screen bg-bg">
      <aside className="hidden w-64 shrink-0 border-r border-border md:flex">
        <Sidebar items={items} user={user} onLogout={logout} />
      </aside>

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-surface px-xl py-md md:hidden">
          <span className="text-sm font-semibold text-text-primary">EV Battery SoH</span>
          <button
            type="button"
            aria-label="Open navigation menu"
            onClick={() => setDrawerOpen(true)}
            className="flex h-[44px] w-[44px] items-center justify-center rounded-md text-text-primary hover:bg-muted"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
        </header>

        <main className={cx('min-w-0 flex-1 overflow-x-hidden px-xl py-xl', useBottomNav && 'pb-[96px]')}>
          <div className="mx-auto w-full min-w-0 max-w-[1280px]">
            <Outlet />
          </div>
        </main>

        {useBottomNav && <MobileNav items={items} />}
      </div>

      {drawerOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setDrawerOpen(false)} aria-hidden="true" />
          <div className="absolute inset-y-0 left-0 w-64 bg-surface shadow-lg">
            <div className="flex justify-end p-md">
              <button
                type="button"
                aria-label="Close navigation menu"
                onClick={() => setDrawerOpen(false)}
                className="flex h-[44px] w-[44px] items-center justify-center rounded-md text-text-primary hover:bg-muted"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <Sidebar items={items} user={user} onLogout={logout} onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}
    </div>
  )
}
