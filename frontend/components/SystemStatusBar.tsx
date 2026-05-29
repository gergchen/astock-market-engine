'use client'

import { Wifi, WifiOff, Clock, AlertTriangle } from 'lucide-react'
import { useSystemStatus } from './SystemStatusProvider'
import { cn } from '@/lib/utils'
import type { SystemStatusType } from '@/lib/types'

const CONFIG: Record<SystemStatusType, {
  icon: typeof Wifi
  color: string
  label: string
}> = {
  realtime: { icon: Wifi, color: 'text-emerald-400', label: '实时' },
  cache:    { icon: Clock, color: 'text-blue-400', label: '缓存' },
  stale:    { icon: AlertTriangle, color: 'text-amber-400', label: '过期' },
  mock:     { icon: WifiOff, color: 'text-red-400', label: '模拟' },
  unknown:  { icon: AlertTriangle, color: 'text-gray-500', label: '未知' },
}

export default function SystemStatusBar() {
  const { status } = useSystemStatus()
  if (!status) return null

  const cfg = CONFIG[status.status] ?? CONFIG.unknown
  const Icon = cfg.icon

  return (
    <div className="flex items-center gap-1.5 text-[11px]">
      <Icon className={cn("w-3 h-3", cfg.color)} />
      <span className={cfg.color}>{cfg.label}</span>
    </div>
  )
}
