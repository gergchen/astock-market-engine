'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search, TrendingUp, BarChart3, Activity,
  ArrowRight, BookOpen, LineChart, Layers,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const FEATURES = [
  { icon: TrendingUp, title: '主力行为识别', desc: '吸筹、洗盘、主升、出货 — 追踪资金动向' },
  { icon: Activity, title: '情绪周期判断', desc: '冰点→修复→主升→高潮，定位当前阶段' },
  { icon: BarChart3, title: '量化评分', desc: '趋势、量能、位置三维评分体系' },
  { icon: Layers, title: '策略回测', desc: '均线突破、量价配合、龙头跟踪回测验证' },
]

const NAV = [
  { href: '/market', label: '大盘', icon: LineChart, desc: '市场全景' },
  { href: '/review', label: '复盘', icon: BookOpen, desc: '收盘解读' },
  { href: '/workbench', label: '工作台', icon: Activity, desc: '实时监控' },
  { href: '/backtest', label: '回测', icon: BarChart3, desc: '策略验证' },
]

export default function HomePage() {
  const [symbol, setSymbol] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbol.trim()) return
    setLoading(true)
    router.push(`/stock?symbol=${symbol.trim()}`)
  }

  const QUICK = ['600519', '000858', '300750', '002594', '601012', '000333']

  return (
    <div className="min-h-screen">
      {/* ── 顶部导航 ── */}
      <header className="border-b border-border bg-[hsl(var(--bg-surface))]">
        <div className="max-w-5xl mx-auto px-5 h-12 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-primary/15 flex items-center justify-center">
              <span className="text-[10px] font-bold text-primary">A</span>
            </div>
            <span className="font-semibold text-sm tracking-tight">AStock</span>
            <span className="text-[10px] text-muted-foreground tracking-wider ml-1 hidden sm:inline">市场认知引擎</span>
          </div>
          <nav className="flex items-center gap-1">
            {NAV.map(link => (
              <a key={link.href} href={link.href}
                className="px-3 py-1.5 rounded text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
                {link.label}
              </a>
            ))}
          </nav>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="max-w-2xl mx-auto px-5 pt-20 pb-12">
        <div className="text-center mb-8">
          <p className="text-xs text-muted-foreground tracking-widest uppercase mb-4">A股市场分析</p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4 leading-tight">
            看懂市场行为逻辑
          </h1>
          <p className="text-muted-foreground text-sm leading-relaxed max-w-md mx-auto">
            输入股票代码，获取主力行为分析、情绪周期判断和量化评分。
          </p>
        </div>

        {/* 搜索框 */}
        <form onSubmit={handleSubmit} className="max-w-lg mx-auto">
          <div className="flex items-center border border-border rounded-md bg-[hsl(var(--bg-surface))] overflow-hidden focus-within:border-primary/40 transition-colors">
            <Search className="ml-3 w-4 h-4 text-muted-foreground shrink-0" />
            <Input
              value={symbol}
              onChange={e => setSymbol(e.target.value)}
              placeholder="输入股票代码，例如 600519"
              className="flex-1 h-10 border-0 bg-transparent focus-visible:ring-0 shadow-none text-sm"
            />
            <Button type="submit" size="sm" disabled={loading}
              className="mr-1 h-7 px-4 text-xs rounded">
              分析
            </Button>
          </div>
        </form>

        {/* 快捷入口 */}
        <div className="mt-4 flex items-center justify-center gap-1.5 flex-wrap">
          <span className="text-[11px] text-muted-foreground mr-1">热门：</span>
          {QUICK.map(code => (
            <button
              key={code}
              onClick={() => router.push(`/stock?symbol=${code}`)}
              className="px-2.5 py-1 rounded bg-muted text-xs text-muted-foreground hover:text-foreground transition-colors font-mono"
            >
              {code}
            </button>
          ))}
        </div>
      </section>

      {/* ── 功能导航 ── */}
      <section className="max-w-5xl mx-auto px-5 pb-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {NAV.map(link => (
            <a
              key={link.href}
              href={link.href}
              className="group flex items-center gap-3 p-4 rounded border border-border bg-[hsl(var(--bg-surface))] hover:border-border/80 transition-colors"
            >
              <link.icon className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
              <div>
                <div className="text-sm font-medium">{link.label}</div>
                <div className="text-[11px] text-muted-foreground">{link.desc}</div>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-muted-foreground/40 ml-auto group-hover:text-muted-foreground transition-colors" />
            </a>
          ))}
        </div>
      </section>

      {/* ── 能力说明 ── */}
      <section className="max-w-5xl mx-auto px-5 pb-24">
        <div className="mb-6">
          <p className="text-[11px] text-muted-foreground tracking-widest uppercase mb-1">核心功能</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {FEATURES.map(f => (
            <div key={f.title} className="p-4 rounded border border-border bg-[hsl(var(--bg-surface))]">
              <f.icon className="w-4 h-4 text-muted-foreground mb-3" />
              <h3 className="text-sm font-medium mb-1">{f.title}</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
