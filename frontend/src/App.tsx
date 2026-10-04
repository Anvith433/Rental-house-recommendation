import { lazy, Suspense, type ReactNode } from 'react'
import { createBrowserRouter, Outlet } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { AdminRoute, GuestRoute, ProtectedRoute } from './components/layout/RouteGuards'
import { Spinner } from './components/ui/Feedback'
import { AuthProvider } from './context/AuthProvider'
import { CompareProvider } from './context/CompareProvider'
import { FavoritesProvider } from './context/FavoritesProvider'
import { ToastProvider } from './context/ToastProvider'
import { MainLayout } from './layouts/MainLayout'
import { LandingPage } from './pages/LandingPage'
import { NotFoundPage } from './pages/NotFoundPage'

const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })))
const RegisterPage = lazy(() => import('./pages/RegisterPage').then((m) => ({ default: m.RegisterPage })))
const SearchPage = lazy(() => import('./pages/SearchPage').then((m) => ({ default: m.SearchPage })))
const PropertyDetailPage = lazy(() => import('./pages/PropertyDetailPage').then((m) => ({ default: m.PropertyDetailPage })))
const RecommendPage = lazy(() => import('./pages/RecommendPage').then((m) => ({ default: m.RecommendPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const FavoritesPage = lazy(() => import('./pages/FavoritesPage').then((m) => ({ default: m.FavoritesPage })))
const ComparePage = lazy(() => import('./pages/ComparePage').then((m) => ({ default: m.ComparePage })))
const ProfilePage = lazy(() => import('./pages/ProfilePage').then((m) => ({ default: m.ProfilePage })))
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage').then((m) => ({ default: m.AdminDashboardPage })))

function Lazy({ children }: { children: ReactNode }) {
  return <Suspense fallback={<Spinner />}>{children}</Suspense>
}

/** Providers that need router context (navigation) live inside the router. */
function AppProviders() {
  return (
    <FavoritesProvider>
      <CompareProvider>
        <Outlet />
      </CompareProvider>
    </FavoritesProvider>
  )
}

const router = createBrowserRouter([
  {
    element: <AppProviders />,
    children: [
      {
        element: <MainLayout />,
        children: [
          { index: true, element: <LandingPage /> },
          { path: 'login', element: <GuestRoute><Lazy><LoginPage /></Lazy></GuestRoute> },
          { path: 'register', element: <GuestRoute><Lazy><RegisterPage /></Lazy></GuestRoute> },
          { path: 'properties', element: <Lazy><SearchPage /></Lazy> },
          { path: 'properties/:id', element: <Lazy><PropertyDetailPage /></Lazy> },
          { path: 'recommendations', element: <Lazy><RecommendPage /></Lazy> },
          { path: 'compare', element: <Lazy><ComparePage /></Lazy> },
          { path: 'dashboard', element: <ProtectedRoute><Lazy><DashboardPage /></Lazy></ProtectedRoute> },
          { path: 'favorites', element: <ProtectedRoute><Lazy><FavoritesPage /></Lazy></ProtectedRoute> },
          { path: 'profile', element: <ProtectedRoute><Lazy><ProfilePage /></Lazy></ProtectedRoute> },
          { path: 'admin', element: <AdminRoute><Lazy><AdminDashboardPage /></Lazy></AdminRoute> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
])

export function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ToastProvider>
  )
}
