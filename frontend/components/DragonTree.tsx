'use client'

import { useRouter } from 'next/navigation'
import { Crown, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface Leader {
  symbol: string
  name: string
  boards: number
  fengdan: number
  industry: string
  score: number
}

interface DragonData {
  leaders: Leader[]
  top_leader: Leader | null
  sector_leaders: Leader[]
  日内龙头: Leader | null
  连板高标: Leader[]
  market_summary: { 涨停数: number; 连板股数: number; 最高板: number }
}

interface Props {
  data: DragonData
}

function boardColor(boards: number): string {
  if (boards >= 8) return '#D94040'
  if (boards >= 5) return '#D4943A'
  if (boards >= 3) return '#C5A03A'
  return '#6B8B9E'
}

function boardBg(boards: number): string {
  if (boards >= 8) return 'hsl(0 30% 14%)'
  if (boards >= 5) return 'hsl(30 30% 12%)'
  if (boards >= 3) return 'hsl(50 25% 11%)'
  return 'hsl(210 15% 12%)'
}

export default function DragonTree({ data }: Props) {
  const router = useRouter()

  if (!data?.leaders?.length) return null

  const { top_leader, 日内龙头, 连板高标, sector_leaders, market_summary } = data

  const byBoards: Record<number, Leader[]> = {}
  data.leaders.forEach(l => {
    if (!byBoards[l.boards]) byBoards[l.boards] = []
    byBoards[l.boards].push(l)
  })
  const boardLevels = Object.keys(byBoards).map(Number).sort((a, b) => b - a)

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Crown className="w-3.5 h-3.5 text-muted-foreground" />
          <CardTitle className="text-sm">龙头晋级树</CardTitle>
          <span className="text-[11px] text-muted-foreground ml-auto font-mono">
            {market_summary.涨停数}涨停 · 最高{market_summary.最高板}板
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {boardLevels.map((boards, levelIdx) => {
            const leaders = byBoards[boards]
            const isTop = levelIdx === 0
            return (
              <div key={boards}>
                <div className="flex items-center gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium"
                    style={{ background: boardBg(boards), color: boardColor(boards) }}>
                    <TrendingUp className="w-3 h-3" />
                    {boards}板
                  </div>
                  <div className="flex-1 h-px bg-border" />
                  <span className="text-[10px] text-muted-foreground">{leaders.length}只</span>
                </div>

                <div className="grid gap-1.5 mb-2" style={{
                  gridTemplateColumns: `repeat(${Math.min(leaders.length, 6)}, minmax(0, 1fr))`
                }}>
                  {leaders.slice(0, 8).map((l, i) => (
                    <button
                      key={l.symbol}
                      onClick={() => router.push(`/stock?symbol=${l.symbol}`)}
                      className="text-left p-2 rounded border transition-colors hover:brightness-110"
                      style={{
                        background: boardBg(boards),
                        borderColor: isTop && i === 0 ? boardColor(boards) + '55' : 'hsl(var(--border))',
                      }}
                    >
                      <div className="flex items-center gap-1">
                        <span className="text-xs font-medium truncate text-foreground">
                          {l.name}
                        </span>
                        {isTop && i === 0 && (
                          <Crown className="w-3 h-3 text-amber-500 shrink-0" />
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-muted-foreground font-mono">{l.symbol}</span>
                        {l.fengdan > 0 && (
                          <span className="text-[10px] font-mono" style={{ color: boardColor(boards) }}>
                            封{l.fengdan.toFixed(1)}亿
                          </span>
                        )}
                      </div>
                      {l.industry && (
                        <div className="text-[10px] text-muted-foreground mt-0.5">{l.industry}</div>
                      )}
                    </button>
                  ))}
                </div>

                {levelIdx < boardLevels.length - 1 && (
                  <div className="flex justify-center py-0.5">
                    <svg width="20" height="10" className="text-border">
                      <line x1="10" y1="0" x2="10" y2="6" stroke="currentColor" strokeWidth="1" />
                      <line x1="3" y1="6" x2="17" y2="6" stroke="currentColor" strokeWidth="1" />
                    </svg>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
