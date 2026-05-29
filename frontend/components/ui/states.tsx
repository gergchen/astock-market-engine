'use client'

import {
  AlertTriangle, Calendar, Inbox, Loader2, RefreshCw,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  fullPage?: boolean
}

export function Spinner({ size = 'md', text, fullPage = false }: SpinnerProps) {
  const sizeMap = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' }

  const spinner = (
    <div className="flex flex-col items-center gap-3">
      <Loader2 className={`${sizeMap[size]} animate-spin text-muted-foreground`} />
      {text && <span className="text-xs text-muted-foreground">{text}</span>}
    </div>
  )

  if (fullPage) {
    return (
      <div className="flex items-center justify-center py-32">
        {spinner}
      </div>
    )
  }

  return spinner
}

interface SkeletonProps {
  lines?: number
  className?: string
}

const SKELETON_WIDTHS = ['85%', '70%', '92%', '60%', '78%', '65%', '88%', '55%']

export function SkeletonCard({ lines = 4, className = '' }: SkeletonProps) {
  return (
    <Card className={className}>
      <CardContent className="p-5 space-y-3">
        <div className="h-4 w-1/3 bg-muted rounded animate-pulse" />
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className="h-3 bg-muted rounded animate-pulse"
            style={{
              width: SKELETON_WIDTHS[i % SKELETON_WIDTHS.length],
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </CardContent>
    </Card>
  )
}

interface EmptyStateProps {
  type?: 'no_data' | 'nontrading' | 'generic'
  message?: string
}

export function EmptyState({ type = 'no_data', message }: EmptyStateProps) {
  const config = {
    no_data: { icon: Inbox, defaultMsg: '暂无数据' },
    nontrading: { icon: Calendar, defaultMsg: '非交易日，数据暂不可用' },
    generic: { icon: Inbox, defaultMsg: '暂无内容' },
  }
  const { icon: Icon, defaultMsg } = config[type]

  return (
    <Card>
      <CardContent className="p-8">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Icon className="w-6 h-6 opacity-30" />
          <span className="text-xs">{message || defaultMsg}</span>
        </div>
      </CardContent>
    </Card>
  )
}

interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

export function ErrorState({ message = '数据加载失败', onRetry }: ErrorStateProps) {
  return (
    <Card className="border-destructive/30">
      <CardContent className="p-8">
        <div className="flex flex-col items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-amber-500 opacity-60" />
          <span className="text-xs text-muted-foreground">{message}</span>
          {onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RefreshCw className="w-3 h-3 mr-1.5" />
              重试
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function PageLoading() {
  return (
    <div className="flex items-center justify-center py-24">
      <Spinner size="lg" text="加载中…" />
    </div>
  )
}

interface AsyncBoundaryProps {
  loading: boolean
  error: string | null
  isEmpty: boolean
  emptyType?: 'no_data' | 'nontrading' | 'generic'
  emptyMessage?: string
  errorMessage?: string
  onRetry?: () => void
  children: React.ReactNode
}

export function AsyncBoundary({
  loading,
  error,
  isEmpty,
  emptyType,
  emptyMessage,
  errorMessage,
  onRetry,
  children,
}: AsyncBoundaryProps) {
  if (loading) return <Spinner fullPage text="加载中…" />
  if (error) return <ErrorState message={errorMessage || error} onRetry={onRetry} />
  if (isEmpty) return <EmptyState type={emptyType} message={emptyMessage} />
  return <>{children}</>
}
