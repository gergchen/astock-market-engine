'use client'

import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  compact?: boolean
  className?: string
}

export default function MockWarningBanner({ compact = false, className }: Props) {
  if (compact) {
    return (
      <div className={cn('flex items-center gap-1.5 text-xs text-amber-500', className)}>
        <AlertTriangle className="w-3 h-3 shrink-0" />
        <span>当前为模拟数据模式</span>
      </div>
    )
  }

  return (
    <div className={cn('rounded-lg border border-amber-500/30 bg-amber-500/10 p-4', className)}>
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-amber-600 dark:text-amber-400">
            当前为模拟数据模式
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            当前无法获取真实行情，系统已降级。所有分析已自动切换为安全模式，不进行任何主力分析、资金行为或历史走势推理。
          </p>
        </div>
      </div>
    </div>
  )
}
