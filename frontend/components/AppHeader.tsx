'use client'

import { useRouter } from 'next/navigation'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  href: string
  label: string
}

interface AppHeaderProps {
  title: string
  icon?: React.ReactNode
  showBack?: boolean
  backHref?: string
  navItems?: NavItem[]
  lastRefresh?: string
  isRefreshing?: boolean
  onRefresh?: () => void
  rightExtra?: React.ReactNode
  variant?: 'sticky' | 'fixed'
  scrolled?: boolean
  statusBar?: React.ReactNode
}

export default function AppHeader({
  title,
  icon,
  showBack = true,
  backHref = '/',
  navItems,
  lastRefresh,
  isRefreshing = false,
  onRefresh,
  rightExtra,
  variant = 'sticky',
  scrolled = false,
  statusBar,
}: AppHeaderProps) {
  const router = useRouter()

  const headerClass = variant === 'fixed'
    ? `fixed top-0 left-0 right-0 z-50 transition-colors duration-200 ${
        scrolled
          ? 'bg-[hsl(var(--bg-surface))] border-b border-border'
          : 'bg-transparent'
      }`
    : 'border-b border-border sticky top-0 bg-[hsl(var(--bg-surface))] z-10'

  return (
    <header className={headerClass}>
      <div className="max-w-6xl mx-auto px-4 h-12 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {showBack && (
            <button
              onClick={() => router.push(backHref)}
              className="text-muted-foreground hover:text-foreground transition-colors p-1 -ml-1"
              aria-label="返回"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <div className="flex items-center gap-2">
            {icon}
            <span className="font-semibold text-sm tracking-tight">{title}</span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {lastRefresh && (
            <span className="whitespace-nowrap flex items-center gap-1.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
              {lastRefresh}
            </span>
          )}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-1 hover:text-foreground transition-colors disabled:opacity-50"
            >
              <RefreshCw className={cn("w-3 h-3", isRefreshing && "animate-spin")} />
              刷新
            </button>
          )}
          {navItems && navItems.length > 0 && (
            <nav className="flex items-center gap-0.5">
              {navItems.map(item => (
                <a
                  key={item.href}
                  href={item.href}
                  className="px-2.5 py-1 rounded text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  {item.label}
                </a>
              ))}
            </nav>
          )}
          {rightExtra}
          {statusBar}
        </div>
      </div>
    </header>
  )
}
