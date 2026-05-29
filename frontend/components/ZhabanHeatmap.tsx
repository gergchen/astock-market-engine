'use client'

import { useState, useEffect } from 'react'
import { Grid3X3, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { API_BASE } from '@/lib/api'

interface SectorStat {
  sector: string
  limit_up: number
  zhaban: number
  total: number
  zhaban_rate: number
  avg_boards: number
}

function heatColor(rate: number): string {
  if (rate >= 0.5) return '#D94040'
  if (rate >= 0.35) return '#D4943A'
  if (rate >= 0.2) return '#C5A03A'
  if (rate > 0) return '#38A868'
  return '#6B8B9E'
}

function heatBg(rate: number): string {
  if (rate >= 0.5) return 'hsl(0 25% 13%)'
  if (rate >= 0.35) return 'hsl(30 25% 12%)'
  if (rate >= 0.2) return 'hsl(50 20% 11%)'
  if (rate > 0) return 'hsl(150 20% 11%)'
  return 'hsl(200 15% 11%)'
}

export default function ZhabanHeatmap() {
  const [sectors, setSectors] = useState<SectorStat[]>([])
  const [loading, setLoading] = useState(true)
  const [hovered, setHovered] = useState<number | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/analysis/sector-stats`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.sectors) setSectors(data.sectors)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 flex items-center justify-center">
          <div className="w-5 h-5 rounded-full border-2 border-border border-t-primary animate-spin" />
        </CardContent>
      </Card>
    )
  }

  if (sectors.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-xs text-muted-foreground">
          暂无板块数据（非交易日或数据获取中）
        </CardContent>
      </Card>
    )
  }

  const maxTotal = Math.max(...sectors.map(s => s.total), 1)

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Grid3X3 className="w-3.5 h-3.5 text-muted-foreground" />
          <CardTitle className="text-sm">炸板热力图</CardTitle>
          <span className="text-[11px] text-muted-foreground ml-auto">
            {sectors.length} 个板块
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 mb-2 px-2">
          <div className="w-20 shrink-0" />
          <div className="flex-1 grid grid-cols-4 gap-1.5">
            {['涨停数', '炸板率', '炸板数', '均板'].map(h => (
              <div key={h} className="text-[10px] text-muted-foreground text-center">{h}</div>
            ))}
          </div>
        </div>

        <div className="space-y-0.5">
          {sectors.map((s, i) => {
            const color = heatColor(s.zhaban_rate)
            const bg = heatBg(s.zhaban_rate)
            const isHovered = hovered === i
            return (
              <div
                key={s.sector}
                className="flex items-center gap-2 px-2 py-1.5 rounded transition-colors cursor-default"
                style={{
                  background: isHovered ? bg : 'transparent',
                  border: isHovered ? `1px solid ${color}22` : '1px solid transparent',
                }}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
              >
                <div className="w-20 shrink-0 text-xs truncate" style={{ color: isHovered ? 'hsl(var(--foreground))' : 'hsl(var(--muted-foreground))' }}>
                  {s.sector}
                </div>

                <div className="flex-1 grid grid-cols-4 gap-1.5 text-center text-xs">
                  <div className="flex items-center justify-center">
                    <div className="flex items-center gap-1">
                      <div className="h-2.5 rounded-sm bg-down opacity-50"
                        style={{ width: `${Math.max(4, (s.limit_up / maxTotal) * 36)}px` }} />
                      <span className="font-mono text-down">{s.limit_up}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-center gap-1">
                    <div className="w-7 h-2.5 rounded-sm" style={{ background: color, opacity: 0.6 }} />
                    <span className="font-mono text-[11px]" style={{ color }}>
                      {(s.zhaban_rate * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div className="flex items-center justify-center">
                    <span className={`font-mono ${s.zhaban > 0 ? 'text-up' : 'text-muted-foreground'}`}>
                      {s.zhaban > 0 ? s.zhaban : '--'}
                    </span>
                  </div>

                  <div className="flex items-center justify-center">
                    <div className="flex items-center gap-1">
                      <TrendingUp className="w-2.5 h-2.5 text-muted-foreground" />
                      <span className="font-mono" style={{ color: s.avg_boards >= 3 ? '#D4943A' : 'hsl(var(--muted-foreground))' }}>
                        {s.avg_boards}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <div className="flex items-center gap-3 mt-3 pt-3 border-t border-border justify-center">
          {[
            { label: '0%', color: '#6B8B9E' },
            { label: '<20%', color: '#38A868' },
            { label: '20-35%', color: '#C5A03A' },
            { label: '35-50%', color: '#D4943A' },
            { label: '>50%', color: '#D94040' },
          ].map(item => (
            <div key={item.label} className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-sm" style={{ background: item.color }} />
              <span className="text-[10px] text-muted-foreground">{item.label}</span>
            </div>
          ))}
          <span className="text-[10px] text-muted-foreground ml-1">炸板率</span>
        </div>
      </CardContent>
    </Card>
  )
}
