'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { TrendingUp, BarChart3, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import AppHeader from '@/components/AppHeader'
import { API_BASE } from '@/lib/api'

const STRATEGIES = [
  { key: 'ma_cross', name: '均线交叉 V2', desc: '趋势过滤 + RSI确认 + ATR止损' },
  { key: 'volume_breakout', name: '放量突破 V2', desc: '站上MA20 + 量比确认 + ATR止损' },
  { key: 'dragon_follow', name: '龙头跟随 V2', desc: '双周期动量 + ATR移动止盈' },
  { key: 'trend_momentum', name: '趋势动量', desc: 'EMA多头排列 + RSI健康区' },
  { key: 'mean_reversion', name: '均值回归', desc: '布林带超卖 + RSI反弹' },
]

interface BacktestResult {
  symbol: string
  strategy: string
  period: string
  metrics: {
    total_trades: number; win_count: number; lose_count: number
    win_rate: number; total_return: number; annual_return: number
    max_drawdown: number; sharpe_ratio: number; avg_pnl: number; avg_hold_days: number
  }
  trades: Array<{ buy_date: string; sell_date: string; buy_price: number; sell_price: number; pnl_pct: number; hold_days: number; reason: string }>
  equity_curve: Array<{ date: string; value: number }>
}

export default function BacktestPage() {
  const router = useRouter()
  const [symbol, setSymbol] = useState('600519')
  const [strategy, setStrategy] = useState('ma_cross')
  const [capital, setCapital] = useState('500000')
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const run = async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({ symbol, strategy, initial_capital: capital })
      const res = await fetch(`${API_BASE}/api/analysis/backtest?${params}`, { method: 'POST' })
      if (!res.ok) throw new Error((await res.json()).detail || '回测失败')
      setResult(await res.json())
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const fmtPct = (v: number) => `${(v >= 0 ? '+' : '')}${(v * 100).toFixed(2)}%`
  const m = result?.metrics
  const equity = result?.equity_curve ?? []

  return (
    <div className="min-h-screen">
      <AppHeader title="策略回测" icon={<BarChart3 className="w-4 h-4 text-muted-foreground" />} />

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        <Card>
          <CardContent className="p-5">
            <div className="flex flex-wrap gap-4 items-end">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">股票代码</label>
                <Input value={symbol} onChange={e => setSymbol(e.target.value)} className="w-28 h-9 font-mono" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">策略</label>
                <div className="flex gap-1">
                  {STRATEGIES.map(s => (
                    <button key={s.key} onClick={() => setStrategy(s.key)}
                      className={`px-3 py-1.5 rounded text-xs transition-colors ${
                        strategy === s.key
                          ? 'bg-primary/15 text-primary border border-primary/30'
                          : 'bg-muted text-muted-foreground border border-transparent'
                      }`}>
                      {s.name}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">初始资金</label>
                <Input value={capital} onChange={e => setCapital(e.target.value)} className="w-28 h-9 font-mono" />
              </div>
              <Button onClick={run} disabled={loading} size="sm">
                {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <BarChart3 className="w-3.5 h-3.5 mr-1" />}
                运行回测
              </Button>
            </div>
          </CardContent>
        </Card>

        {error && (
          <div className="p-3 rounded border border-destructive/30 bg-destructive/5 text-destructive text-xs">{error}</div>
        )}

        {m && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {[
                { label: '总收益', value: fmtPct(m.total_return), color: m.total_return >= 0 ? 'text-up' : 'text-down' },
                { label: '年化', value: fmtPct(m.annual_return), color: m.annual_return >= 0 ? 'text-up' : 'text-down' },
                { label: '胜率', value: (m.win_rate * 100).toFixed(0) + '%', color: 'text-foreground' },
                { label: '夏普比', value: m.sharpe_ratio.toFixed(2), color: m.sharpe_ratio >= 1 ? 'text-up' : 'text-muted-foreground' },
                { label: '最大回撤', value: (m.max_drawdown * 100).toFixed(1) + '%', color: 'text-down' },
              ].map(item => (
                <div key={item.label} className="p-3 rounded border border-border bg-card">
                  <div className="text-[10px] text-muted-foreground mb-1">{item.label}</div>
                  <div className={`text-lg font-bold font-mono ${item.color}`}>{item.value}</div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { label: '交易次数', value: m.total_trades },
                { label: '盈利 / 亏损', value: `${m.win_count} / ${m.lose_count}` },
                { label: '平均收益', value: fmtPct(m.avg_pnl) },
                { label: '平均持仓', value: m.avg_hold_days.toFixed(1) + '天' },
              ].map(item => (
                <div key={item.label} className="p-3 rounded border border-border bg-card">
                  <div className="text-[10px] text-muted-foreground mb-1">{item.label}</div>
                  <div className="text-sm font-mono">{item.value}</div>
                </div>
              ))}
            </div>

            {equity.length > 1 && (
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">收益曲线</CardTitle></CardHeader>
                <CardContent>
                  <div className="relative h-32">
                    <svg width="100%" height="100%" viewBox={`0 0 ${equity.length} 100`} preserveAspectRatio="none">
                      <defs>
                        <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="hsl(152 48% 42%)" stopOpacity="0.15" />
                          <stop offset="100%" stopColor="hsl(152 48% 42%)" stopOpacity="0" />
                        </linearGradient>
                      </defs>
                      <path
                        d={(() => {
                          const minV = Math.min(...equity.map(d => d.value))
                          const maxV = Math.max(...equity.map(d => d.value))
                          const range = maxV - minV || 1
                          return equity.map((d, i) =>
                            `${i === 0 ? 'M' : 'L'} ${i / (equity.length - 1) * equity.length} ${100 - ((d.value - minV) / range) * 90 - 5}`
                          ).join(' ')
                        })()}
                        fill="none" stroke="hsl(152 48% 42%)" strokeWidth="1.5"
                      />
                      <path
                        d={(() => {
                          const minV = Math.min(...equity.map(d => d.value))
                          const maxV = Math.max(...equity.map(d => d.value))
                          const range = maxV - minV || 1
                          const linePath = equity.map((d, i) =>
                            `${i === 0 ? 'M' : 'L'} ${i / (equity.length - 1) * equity.length} ${100 - ((d.value - minV) / range) * 90 - 5}`
                          ).join(' ')
                          return `${linePath} L ${equity.length} 100 L 0 100 Z`
                        })()}
                        fill="url(#equityFill)"
                      />
                    </svg>
                  </div>
                </CardContent>
              </Card>
            )}

            {result.trades.length > 0 && (
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">交易记录</CardTitle></CardHeader>
                <CardContent className="p-0">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>买入</th><th>卖出</th><th className="text-right">买价</th>
                        <th className="text-right">卖价</th><th className="text-right">收益</th>
                        <th className="text-right">持仓</th><th>原因</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades.slice(-20).map((t, i) => (
                        <tr key={i}>
                          <td className="font-mono">{t.buy_date}</td>
                          <td className="font-mono">{t.sell_date}</td>
                          <td className="text-right font-mono">{t.buy_price.toFixed(2)}</td>
                          <td className="text-right font-mono">{t.sell_price.toFixed(2)}</td>
                          <td className={`text-right font-mono font-semibold ${t.pnl_pct >= 0 ? 'text-up' : 'text-down'}`}>
                            {fmtPct(t.pnl_pct)}
                          </td>
                          <td className="text-right text-muted-foreground">{t.hold_days}天</td>
                          <td className="text-muted-foreground max-w-[200px] truncate">{t.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {!loading && !result && !error && (
          <div className="text-center py-20 text-muted-foreground text-xs">
            选择股票和策略，点击「运行回测」
          </div>
        )}
      </main>
    </div>
  )
}
