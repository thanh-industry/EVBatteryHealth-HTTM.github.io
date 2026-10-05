import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { AuthProvider, useAuth } from './lib/auth'
import { queryClient } from './lib/queryClient'
import { HOME_ROUTE_BY_ROLE } from './lib/nav'
import { FullPageSpinner, RoleRoute } from './routes/RoleRoute'
import { LoginPage } from './pages/LoginPage'
import { ForbiddenPage } from './pages/ForbiddenPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { OverviewPage } from './pages/ds/OverviewPage'
import { DatasetsPage } from './pages/ds/DatasetsPage'
import { DatasetDetailPage } from './pages/ds/DatasetDetailPage'
import { TrainingPage } from './pages/ds/TrainingPage'
import { ExperimentsPage } from './pages/ds/ExperimentsPage'
import { ComparePage } from './pages/ds/ComparePage'
import { ModelsPage } from './pages/ds/ModelsPage'
import { DashboardPage as TechDashboardPage } from './pages/tech/DashboardPage'
import { LookupPage } from './pages/tech/LookupPage'
import { DiagnosticDetailPage } from './pages/tech/DiagnosticDetailPage'
import { HistoryPage } from './pages/tech/HistoryPage'
import { HomePage as AppHomePage } from './pages/app/HomePage'
import { BatteryPage } from './pages/app/BatteryPage'
import { MaintenancePage } from './pages/app/MaintenancePage'
import { NotificationsPage } from './pages/app/NotificationsPage'

function RootRedirect() {
  const { user, status } = useAuth()
  if (status === 'loading') return <FullPageSpinner />
  if (status === 'unauthenticated' || !user) return <Navigate to="/login" replace />
  return <Navigate to={HOME_ROUTE_BY_ROLE[user.role]} replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/403" element={<ForbiddenPage />} />

      <Route element={<RoleRoute allow={['data_scientist']} />}>
        <Route element={<AppShell />}>
          <Route path="/ds/overview" element={<OverviewPage />} />
          <Route path="/ds/datasets" element={<DatasetsPage />} />
          <Route path="/ds/datasets/:id" element={<DatasetDetailPage />} />
          <Route path="/ds/training" element={<TrainingPage />} />
          <Route path="/ds/experiments" element={<ExperimentsPage />} />
          <Route path="/ds/compare" element={<ComparePage />} />
          <Route path="/ds/models" element={<ModelsPage />} />
        </Route>
      </Route>

      <Route element={<RoleRoute allow={['technician']} />}>
        <Route element={<AppShell />}>
          <Route path="/tech/dashboard" element={<TechDashboardPage />} />
          <Route path="/tech/lookup" element={<LookupPage />} />
          <Route path="/tech/diagnostics/:id" element={<DiagnosticDetailPage />} />
          <Route path="/tech/history" element={<HistoryPage />} />
        </Route>
      </Route>

      <Route element={<RoleRoute allow={['ev_user']} />}>
        <Route element={<AppShell />}>
          <Route path="/app/home" element={<AppHomePage />} />
          <Route path="/app/battery" element={<BatteryPage />} />
          <Route path="/app/maintenance" element={<MaintenancePage />} />
          <Route path="/app/notifications" element={<NotificationsPage />} />
        </Route>
      </Route>

      <Route path="/" element={<RootRedirect />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
