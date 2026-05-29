'use client'

import { useState, useRef, useCallback, type ReactNode } from 'react'
import { Loader2, FileText } from 'lucide-react'
import { API_BASE } from '@/lib/api'

interface Props {
  children: ReactNode
  symbol: string
  query?: string
  side?: 'top' | 'bottom' | 'left' | 'right'
}

const _cache = new Map<string, string>()

export default function AITooltip({ children, symbol, query, side = 'top' }: Props) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()

  const cacheKey = `${symbol}::${query ?? 'comprehensive'}`

  const fetchExplanation = useCallback(async () => {
    if (_cache.has(cacheKey)) {
      setText(_cache.get(cacheKey)!)
      return
    }
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/analysis/stock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          analysis_type: query ?? 'comprehensive',
        }),
      })
      if (res.ok) {
        const data = await res.json()
        const raw = typeof data.analysis === 'string'
          ? data.analysis
          : data.analysis?.raw ?? data.analysis?.text ?? ''
        const lines = raw.split('\n').filter((l: string) =>
          l.trim() && !l.startsWith('#') && l.length > 10
        )
        const snippet = lines.slice(0, 3).join('\n').slice(0, 300)
        _cache.set(cacheKey, snippet)
        setText(snippet)
      }
    } catch {
      setText('分析暂时不可用')
    } finally {
      setLoading(false)
    }
  }, [symbol, query, cacheKey])

  const handleEnter = () => {
    timerRef.current = setTimeout(() => {
      setOpen(true)
      fetchExplanation()
    }, 400)
  }

  const handleLeave = () => {
    clearTimeout(timerRef.current)
    setOpen(false)
  }

  const sideStyles: Record<string, React.CSSProperties> = {
    top:    { bottom: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)' },
    bottom: { top: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)' },
    left:   { right: 'calc(100% + 8px)', top: '50%', transform: 'translateY(-50%)' },
    right:  { left: 'calc(100% + 8px)', top: '50%', transform: 'translateY(-50%)' },
  }

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      {children}

      {open && (
        <div
          className="absolute z-50 w-72 transition-opacity duration-150"
          style={sideStyles[side]}
        >
          <div className="p-4 rounded border border-border bg-[hsl(var(--bg-overlay))] shadow-lg">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-medium text-foreground">快速解读</span>
            </div>

            {loading ? (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="w-3 h-3 animate-spin" />
                分析中...
              </div>
            ) : (
              <p className="text-xs leading-relaxed text-muted-foreground">{text}</p>
            )}

            <div className="mt-2 text-[10px] text-muted-foreground/60">
              {symbol} · 不构成投资建议
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
