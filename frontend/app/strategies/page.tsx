'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Trophy, TrendingUp, BarChart3, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import AppHeader from '@/components/AppHeader'
import { API_BASE } from '@/lib/api'

interface Ranking {
  symbol: string; name: string; strategy: string; strategy_key: string
  total_return: number; sharpe_ratio: number; win_rate: number
  max_drawdown: number; total_trades: number
}

const SORT_OPTIONS = [
  { key: 'sharpe', label: '夏普比' },
  { key: 'return', label: '收益率' },
  { key: 'win_rate', label: '胜率' },
]

export default function StrategyMarketPage() {
  const router = useRouter()
  const [rankings, setRankings] = useState<Ranking[]>([])
  const [loading, setLoading] = useState(true)
  const [sortBy, setSortBy] = useState('sharpe')

  const fetchRankings = async (sort: string) => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/analysis/strategy-market?sort_by=${sort}`)
      if (res.ok) {
        const data = await res.json()
        setRankings(data.rankings ?? [])
      }
    } catch {}
    setLoading(false)
  }

  useEffect(() => { fetchRankings(sortBy) }, [sortBy])

  const top3 = rankings.slice(0, 3)

  return (
    <div className="min-h-screen">
      <AppHeader title="策略市场" icon={<TrendingUp className="w-4 h-4 text-muted-foreground" />} />

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        {loading ? (
          <div className="flex justify-center py-24">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            {top3.length > 0 && (
              <div className="grid grid-cols-3 gap-3">
                {top3.map((r, i) => {
                  const medals = ['#D4943A', '#8B8B8B', '#A0724E']
                  return (
                    <Card key={`${r.symbol}-${r.strategy_key}`}>
                      <CardContent className="p-4 text-center">
                        <div className="w-7 h-7 rounded mx-auto mb-2 flex items-center justify-center"
                          style={{ background: medals[i] + '18' }}>
                          <Trophy className="w-3.5 h-3.5" style={{ color: medals[i] }} />
                        </div>
                        <div className="text-sm font-semibold">{r.name}</div>
                        <div className="text-[11px] text-muted-foreground">{r.symbol} · {r.strategy}</div>
                        <div className="mt-2 flex items-center justify-center gap-3 text-xs">
                          <span className="text-up font-mono font-semibold">
                            {(r.total_return >= 0 ? '+' : '')}{(r.total_return * 100).toFixed(1)}%
                          </span>
                          <span className="text-muted-foreground">夏普 {r.sharpe_ratio.toFixed(2)}</span>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            )}

            <div className="flex items-center gap-1.5">
              <span className="text-[11px] text-muted-foreground mr-1">排序</span>
              {SORT_OPTIONS.map(opt => (
                <button key={opt.key} onClick={() => setSortBy(opt.key)}
                  className={`px-2.5 py-1 rounded text-xs transition-colors ${
                    sortBy === opt.key ? 'bg-primary/15 text-primary' : 'bg-muted text-muted-foreground'
                  }`}>
                  {opt.label}
                </button>
              ))}
            </div>

            <Card>
              <CardContent className="p-0">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th className="w-10">#</th><th>股票</th><th>策略</th>
                      <th className="text-right">收益率</th><th className="text-right">夏普比</th>
                      <th className="text-right">胜率</th><th className="text-right">最大回撤</th>
                      <th className="text-right">交易</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankings.map((r, i) => (
                      <tr key={`${r.symbol}-${r.strategy_key}`}
                        className="cursor-pointer"
                        onClick={() => router.push(`/backtest?symbol=${r.symbol}&strategy=${r.strategy_key}`)}>
                        <td className="font-mono">
                          {i + 1 <= 3 ? (
                            <span style={{ color: ['#D4943A', '#8B8B8B', '#A0724E'][i] }}>{i + 1}</span>
                          ) : i + 1}
                        </td>
                        <td>
                          <div className="font-medium">{r.name}</div>
                          <div className="text-[11px] text-muted-foreground">{r.symbol}</div>
                        </td>
                        <td>
                          <Badge variant="outline" className="text-[10px]">{r.strategy}</Badge>
                        </td>
                        <td className={`text-right font-mono font-semibold ${r.total_return >= 0 ? 'text-up' : 'text-down'}`}>
                          {(r.total_return >= 0 ? '+' : '')}{(r.total_return * 100).toFixed(1)}%
                        </td>
                        <td className={`text-right font-mono ${r.sharpe_ratio >= 1 ? 'text-up' : r.sharpe_ratio >= 0.5 ? 'text-amber-400' : 'text-muted-foreground'}`}>
                          {r.sharpe_ratio.toFixed(2)}
                        </td>
                        <td className="text-right font-mono text-muted-foreground">
                          {(r.win_rate * 100).toFixed(0)}%
                        </td>
                        <td className="text-right font-mono text-down">
                          {(r.max_drawdown * 100).toFixed(1)}%
                        </td>
                        <td className="text-right font-mono text-muted-foreground">{r.total_trades}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <div className="text-center text-[11px] text-muted-foreground pb-8">
              基于历史K线的纯规则回测，不构成未来收益保证
            </div>
          </>
        )}
      </main>
    </div>
  )
}
