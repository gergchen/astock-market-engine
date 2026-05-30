'use client'

import { useRouter } from 'next/navigation'
import { ArrowLeft, RefreshCw, Flame } from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem { href: string; label: string }

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
  title, icon, showBack = true, backHref = '/', navItems,
  lastRefresh, isRefreshing = false, onRefresh, rightExtra,
  variant = 'sticky', scrolled = false, statusBar,
}: AppHeaderProps) {
  const router = useRouter()

  return (
    <header className={cn(
      'sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-2xl',
      variant === 'fixed' && 'fixed top-0 left-0 right-0',
      scrolled ? 'bg-[hsl(var(--bg-surface))]' : 'bg-[hsl(var(--bg-root))]/85',
    )}>
      <div className="max-w-6xl mx-auto px-6 h-12 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {showBack ? (
            <button onClick={() => router.push(backHref)}
              className="text-white/20 hover:text-white/60 transition-colors p-1 -ml-1"
              aria-label="返回">
              <ArrowLeft className="w-4 h-4" />
            </button>
          ) : (
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center">
              <Flame className="w-3.5 h-3.5 text-white" />
            </div>
          )}
          <div className="flex items-center gap-2">
            {icon}
            <span className="text-[13px] font-semibold tracking-tight text-white/90">{title}</span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          {lastRefresh && (
            <span className="whitespace-nowrap flex items-center gap-1.5 text-white/20">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 animate-glow-pulse" />
              {lastRefresh}
            </span>
          )}
          {onRefresh && (
            <button onClick={onRefresh} disabled={isRefreshing}
              className="flex items-center gap-1 text-white/20 hover:text-white/50 transition-colors disabled:opacity-50">
              <RefreshCw className={cn("w-3 h-3", isRefreshing && "animate-spin")} />
              <span className="text-[11px]">刷新</span>
            </button>
          )}
          {navItems && navItems.length > 0 && (
            <nav className="flex items-center gap-0.5">
              {navItems.map(item => (
                <a key={item.href} href={item.href}
                  className="px-2.5 py-1 rounded-md text-[11px] text-white/25 hover:text-white/60 hover:bg-white/[0.04] transition-all">
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
