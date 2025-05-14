'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { auth } from '@/lib/firebase'
import {
  ChartBarIcon,
  Cog6ToothIcon,
  ChatBubbleLeftRightIcon,
  ArrowLeftOnRectangleIcon,
  PuzzlePieceIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Overview', href: '/dashboard', icon: ChartBarIcon },
  { name: 'Chatbots', href: '/dashboard/chatbots', icon: ChatBubbleLeftRightIcon },
  { name: 'Data Sources', href: '/dashboard/datasources', icon: DocumentTextIcon },
  { name: 'Integrations', href: '/dashboard/integrations', icon: PuzzlePieceIcon },
  { name: 'Settings', href: '/dashboard/settings', icon: Cog6ToothIcon },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  const handleSignOut = async () => {
    try {
      await auth.signOut()
      router.push('/')
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <motion.div
        className="fixed inset-y-0 left-0 z-50 w-64 bg-muted/50 backdrop-blur-xl border-r border-border"
        initial={{ x: -256 }}
        animate={{ x: isSidebarOpen ? 0 : -256 }}
        transition={{ duration: 0.2 }}
      >
        <div className="flex h-full flex-col">
          {/* Sidebar header */}
          <div className="flex h-16 items-center justify-between px-4">
            <Link href="/" className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
              ChatSphere
            </Link>
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="p-2 rounded-md hover:bg-muted transition-colors"
              aria-label="Collapse sidebar"
            >
              <ChevronLeftIcon className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-foreground hover:bg-muted'
                  }`}
                >
                  <item.icon
                    className={`mr-3 h-5 w-5 flex-shrink-0 ${
                      isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground'
                    }`}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* Sidebar footer */}
          <div className="border-t border-border p-4">
            <button
              onClick={handleSignOut}
              className="group flex w-full items-center px-2 py-2 text-sm font-medium text-foreground rounded-md hover:bg-muted transition-colors"
            >
              <ArrowLeftOnRectangleIcon
                className="mr-3 h-5 w-5 text-muted-foreground group-hover:text-foreground"
                aria-hidden="true"
              />
              Sign out
            </button>
          </div>
        </div>
      </motion.div>

      {/* Floating expand button */}
      <motion.button
        initial={{ opacity: 0, x: -20 }}
        animate={{ 
          opacity: isSidebarOpen ? 0 : 1,
          x: isSidebarOpen ? -20 : 0
        }}
        transition={{ duration: 0.2 }}
        onClick={() => setIsSidebarOpen(true)}
        className="fixed left-0 top-4 z-50 p-2 bg-primary text-primary-foreground rounded-r-md shadow-md hover:bg-primary/90 transition-colors"
        aria-label="Expand sidebar"
      >
        <ChevronRightIcon className="h-5 w-5" aria-hidden="true" />
      </motion.button>

      {/* Main content */}
      <div className={`${isSidebarOpen ? 'pl-64' : 'pl-0'} transition-[padding] duration-200`}>
        <main className="py-10">
          <div className="px-4 sm:px-6 lg:px-8">{children}</div>
        </main>
      </div>
    </div>
  )
}