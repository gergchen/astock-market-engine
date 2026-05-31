'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search, TrendingUp, BarChart3, Activity,
  ArrowRight, BookOpen, LineChart, Layers, Flame,
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

const QUICK = ['600519', '000858', '300750', '002594', '601012', '000333']

export default function HomePage() {
  const [symbol, setSymbol] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbol.trim()) return
    setLoading(true)
    router.push(`/stock?code=${symbol.trim()}`)
  }

  return (
    <div className="min-h-screen">
      {/* 顶部导航 */}
      <header className="border-b border-white/[0.06] backdrop-blur-2xl bg-[hsl(var(--bg-root))]/85 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 h-12 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center">
              <Flame className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-[13px] font-semibold tracking-tight text-white/90">AStock</span>
            <span className="text-[10px] text-white/20 tracking-wider ml-1 hidden sm:inline">市场认知引擎 v4</span>
          </div>
          <nav className="flex items-center gap-0.5">
            {NAV.map(link => (
              <a key={link.href} href={link.href}
                className="px-3 py-1.5 rounded-md text-[11px] text-white/25 hover:text-white/60 hover:bg-white/[0.04] transition-all">
                {link.label}
              </a>
            ))}
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-2xl mx-auto px-6 pt-24 pb-14">
        <div className="text-center mb-10">
          <p className="text-[10px] text-violet-400/40 tracking-[0.3em] uppercase mb-5">A股市场分析</p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4 leading-tight text-white/90"
            style={{ fontFamily: "'Space Grotesk', 'DM Sans', sans-serif" }}>
            看懂市场行为逻辑
          </h1>
          <p className="text-white/25 text-sm leading-relaxed max-w-md mx-auto">
            输入股票代码，获取主力行为分析、情绪周期判断和量化评分。
          </p>
        </div>

        {/* 搜索框 */}
        <form onSubmit={handleSubmit} className="max-w-lg mx-auto">
          <div className="flex items-center rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden
            focus-within:border-violet-500/20 focus-within:shadow-[0_0_20px_rgba(139,92,246,0.08)] transition-all duration-300">
            <Search className="ml-4 w-4 h-4 text-white/15 shrink-0" />
            <Input
              value={symbol}
              onChange={e => setSymbol(e.target.value)}
              placeholder="输入股票代码，例如 600519"
              className="flex-1 h-11 border-0 bg-transparent focus-visible:ring-0 shadow-none text-sm text-white/70 placeholder:text-white/15"
            />
            <Button type="submit" size="sm" disabled={loading}
              className="mr-1.5 h-8 px-5 text-xs rounded-lg bg-violet-500/15 text-violet-300 border border-violet-500/20
                hover:bg-violet-500/25 hover:border-violet-500/30 transition-all">
              分析
            </Button>
          </div>
        </form>

        {/* 快捷入口 */}
        <div className="mt-5 flex items-center justify-center gap-1.5 flex-wrap">
          <span className="text-[10px] text-white/15 mr-1">热门</span>
          {QUICK.map(code => (
            <button key={code} onClick={() => router.push(`/stock?code=${code}`)}
              className="px-2.5 py-1 rounded-lg bg-white/[0.03] border border-white/[0.04] text-[11px] text-white/30
                hover:text-white/60 hover:border-white/[0.08] transition-all font-mono">
              {code}
            </button>
          ))}
        </div>
      </section>

      {/* 功能导航 */}
      <section className="max-w-5xl mx-auto px-6 pb-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {NAV.map(link => (
            <a key={link.href} href={link.href}
              className="group flex items-center gap-3 p-4 rounded-xl border border-white/[0.04] bg-white/[0.015]
                hover:border-white/[0.08] hover:bg-white/[0.03] transition-all duration-200">
              <link.icon className="w-4 h-4 text-white/20 group-hover:text-violet-400/60 transition-colors" />
              <div>
                <div className="text-sm font-medium text-white/60 group-hover:text-white/80 transition-colors">{link.label}</div>
                <div className="text-[10px] text-white/15 mt-0.5">{link.desc}</div>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-white/[0.06] ml-auto group-hover:text-white/20 transition-colors" />
            </a>
          ))}
        </div>
      </section>

      {/* 能力说明 */}
      <section className="max-w-5xl mx-auto px-6 pb-24">
        <div className="mb-5">
          <p className="text-[10px] text-white/15 tracking-[0.2em] uppercase">核心功能</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {FEATURES.map(f => (
            <div key={f.title} className="p-4 rounded-xl border border-white/[0.04] bg-white/[0.015]
              hover:border-white/[0.06] transition-colors">
              <f.icon className="w-4 h-4 text-violet-400/30 mb-3" />
              <h3 className="text-[13px] font-medium text-white/50 mb-1">{f.title}</h3>
              <p className="text-[11px] text-white/20 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
