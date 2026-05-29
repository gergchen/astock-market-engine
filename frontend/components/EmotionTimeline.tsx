'use client'

import { useState, useEffect } from 'react'
import { Clock, ChevronLeft, ChevronRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Spinner, ErrorState, EmptyState } from '@/components/ui/states'
import { API_BASE } from '@/lib/api'
import { emotionColor } from '@/lib/types'

interface HistoryRecord {
  date: string
  emotion_stage: string
  ai_review_text: string
}

interface Props {
  limit?: number
}

const STAGE_LABELS: Record<string, string> = {
  '冰点期': '冰点', '修复期': '修复', '主升期': '主升',
  '高潮期': '高潮', '分歧期': '分歧', '退潮期': '退潮',
}

const STAGE_INTENSITY: Record<string, number> = {
  '冰点期': 15, '修复期': 40, '主升期': 85,
  '高潮期': 95, '分歧期': 55, '退潮期': 25,
}

export default function EmotionTimeline({ limit = 30 }: Props) {
  const [records, setRecords] = useState<HistoryRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [hovered, setHovered] = useState<number | null>(null)
  const [scroll, setScroll] = useState(0)

  const fetchData = () => {
    setLoading(true)
    setError('')
    fetch(`${API_BASE}/api/analysis/rag/history?limit=${limit}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        if (data?.records?.length) {
          setRecords(data.records.reverse())
        } else {
          setRecords([])
        }
      })
      .catch(err => {
        setError(err.message || '加载失败')
        setRecords([])
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [limit])

  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 flex items-center justify-center">
          <Spinner size="sm" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return <ErrorState message={`情绪数据加载失败: ${error}`} onRetry={fetchData} />
  }

  if (records.length === 0) {
    return <EmptyState type="no_data" message="暂无历史情绪数据" />
  }

  const maxScroll = Math.max(0, records.length - 14)

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-muted-foreground" />
            <CardTitle className="text-sm">情绪周期时间轴</CardTitle>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setScroll(Math.max(0, scroll - 3))}
              disabled={scroll === 0}
              className="p-1 rounded hover:bg-muted disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setScroll(Math.min(maxScroll, scroll + 3))}
              disabled={scroll >= maxScroll}
              className="p-1 rounded hover:bg-muted disabled:opacity-30 transition-colors"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pb-4">
        <div className="relative" style={{ height: 140 }}>
          <div className="absolute top-20 left-0 right-0 h-px bg-border" />

          <div className="absolute top-0 left-0 right-0 flex" style={{
            transform: `translateX(${-scroll * 52}px)`,
            transition: 'transform 0.3s ease',
          }}>
            {records.map((r, i) => {
              const color = emotionColor(r.emotion_stage)
              const label = STAGE_LABELS[r.emotion_stage] || r.emotion_stage
              const isHovered = hovered === i
              const intensity = STAGE_INTENSITY[r.emotion_stage] || 40
              const barHeight = 20 + (intensity / 100) * 50

              return (
                <div
                  key={r.date}
                  className="relative flex flex-col items-center"
                  style={{ width: 52, flexShrink: 0 }}
                  onMouseEnter={() => setHovered(i)}
                  onMouseLeave={() => setHovered(null)}
                >
                  <div
                    className="w-2 rounded-full cursor-pointer transition-all duration-150"
                    style={{
                      height: isHovered ? barHeight + 12 : barHeight,
                      background: color,
                      marginTop: isHovered ? 8 : 20,
                    }}
                  />
                  <div className="absolute top-[72px] w-2 h-2 rounded-full border-2 z-10"
                    style={{ background: 'hsl(var(--bg-elevated))', borderColor: color }} />
                  <div className="absolute top-[88px] text-[10px] text-muted-foreground whitespace-nowrap"
                    style={{ color: isHovered ? 'hsl(var(--foreground))' : undefined }}>
                    {r.date.slice(5)}
                  </div>

                  {isHovered && (
                    <div
                      className="absolute -top-2 left-1/2 -translate-x-1/2 z-20 px-3 py-2 rounded text-xs whitespace-nowrap border"
                      style={{ background: 'hsl(var(--bg-overlay))', borderColor: color + '44' }}
                    >
                      <div className="flex items-center gap-1.5 mb-1">
                        <div className="w-2 h-2 rounded-full" style={{ background: color }} />
                        <span className="font-semibold" style={{ color }}>{r.emotion_stage}</span>
                      </div>
                      <div className="text-muted-foreground mb-1 text-[11px]">{r.date}</div>
                      {r.ai_review_text && (
                        <div className="text-muted-foreground max-w-[160px] whitespace-normal text-[10px] leading-relaxed">
                          {r.ai_review_text.slice(0, 60)}{r.ai_review_text.length > 60 ? '…' : ''}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {records.length > 0 && (
            <div
              className="absolute top-0 bottom-0 w-px bg-primary/30 z-20"
              style={{
                left: `${(records.length - 1 - scroll) * 52 + 26}px`,
                display: records.length - 1 - scroll >= 0 && records.length - 1 - scroll < 14 ? 'block' : 'none',
              }}
            />
          )}
        </div>

        <div className="flex flex-wrap gap-3 justify-center mt-2 pt-3 border-t border-border">
          {Object.entries(STAGE_LABELS).map(([stage, label]) => (
            <div key={stage} className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full" style={{ background: emotionColor(stage) }} />
              <span className="text-[10px] text-muted-foreground">{label}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
