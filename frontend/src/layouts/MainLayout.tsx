import { Outlet, ScrollRestoration } from 'react-router'
import { CompareTray } from '../components/layout/CompareTray'
import { Footer } from '../components/layout/Footer'
import { Navbar } from '../components/layout/Navbar'

export function MainLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:shadow"
      >
        Skip to content
      </a>
      <Navbar />
      <main id="main" className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <CompareTray />
      <ScrollRestoration />
    </div>
  )
}
