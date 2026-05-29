'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { API_BASE } from '@/lib/api'
import type { SystemStatusResponse, SystemStatusType } from '@/lib/types'

interface SystemStatusContextValue {
  status: SystemStatusResponse | null
  isMock: boolean
  systemStatus: SystemStatusType
}

const SystemStatusContext = createContext<SystemStatusContextValue>({
  status: null,
  isMock: false,
  systemStatus: 'unknown',
})

export function SystemStatusProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/stock/system/status`)
        if (res.ok) setStatus(await res.json())
      } catch { /* silent */ }
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const value: SystemStatusContextValue = {
    status,
    isMock: status?.status === 'mock',
    systemStatus: status?.status ?? 'unknown',
  }

  return (
    <SystemStatusContext.Provider value={value}>
      {children}
    </SystemStatusContext.Provider>
  )
}

export const useSystemStatus = () => useContext(SystemStatusContext)
