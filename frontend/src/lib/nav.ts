import {
  BarChart3,
  BatteryCharging,
  Bell,
  Boxes,
  Cpu,
  Database,
  FlaskConical,
  History,
  LayoutDashboard,
  Search,
  Wrench,
  type LucideIcon,
} from 'lucide-react'
import type { Role } from '../types/api'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

export const NAV_BY_ROLE: Record<Role, NavItem[]> = {
  data_scientist: [
    { to: '/ds/overview', label: 'Overview', icon: LayoutDashboard },
    { to: '/ds/datasets', label: 'Datasets', icon: Database },
    { to: '/ds/training', label: 'Training', icon: Cpu },
    { to: '/ds/experiments', label: 'Experiments', icon: FlaskConical },
    { to: '/ds/compare', label: 'Compare', icon: BarChart3 },
    { to: '/ds/models', label: 'Models', icon: Boxes },
  ],
  technician: [
    { to: '/tech/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/tech/lookup', label: 'Lookup', icon: Search },
    { to: '/tech/history', label: 'History', icon: History },
  ],
  ev_user: [
    { to: '/app/home', label: 'Home', icon: LayoutDashboard },
    { to: '/app/battery', label: 'Battery', icon: BatteryCharging },
    { to: '/app/maintenance', label: 'Maintenance', icon: Wrench },
    { to: '/app/notifications', label: 'Notifications', icon: Bell },
  ],
}

export const HOME_ROUTE_BY_ROLE: Record<Role, string> = {
  data_scientist: '/ds/overview',
  technician: '/tech/dashboard',
  ev_user: '/app/home',
}
