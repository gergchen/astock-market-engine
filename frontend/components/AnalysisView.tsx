'use client'

import { useState, useEffect } from 'react'
import {
  TrendingUp, TrendingDown, AlertTriangle, Lightbulb,
  BarChart3, Target, Activity, FileText,
  Shield, Zap, ChevronRight, Radio, Crosshair,
  ArrowUp, ArrowDown, Minus, Sparkles,
} from 'lucide-react'

interface AnalysisViewProps { text: string }

// ── 解析 ──

interface Section { title: string; body: string[] }

function parseSections(text: string): Section[] {
  const lines = text.split('\n')
  const sections: Section[] = []
  let cur: Section | null = null
  for (const line of lines) {
    const m = line.match(/^##\s+(.+)/)
    if (m) { if (cur) sections.push(cur); cur = { title: m[1].trim(), body: [] } }
    else if (cur) cur.body.push(line)
  }
  if (cur) sections.push(cur)
  return sections
}

function extractOneLiner(sections: Section[]): string {
  for (const s of sections) {
    for (const line of s.body) {
      const t = line.replace(/[*#\-]/g, '').trim()
      if (t.length > 5) return t
    }
  }
  return ''
}

function extractVerdict(sections: Section[]): { text: string; confidence: string } | null {
  for (const s of sections) {
    const joined = s.body.join('\n')
    const m = joined.match(/\*\*(结论|核心判断|判断)：?\*\*\s*(.+)/)
    if (m) {
      const conf = joined.match(/置信度[：:]\s*(\S+)/)
      return { text: m[2].replace(/\*/g, '').trim(), confidence: conf?.[1] || '' }
    }
  }
  return null
}

function extractRiskLevel(sections: Section[]): 'high' | 'medium' | 'low' {
  const all = sections.map(s => s.body.join(' ')).join(' ')
  if (/高风险|极高|赶紧跑|千万别买|最大.*风险|出货.*明显/.test(all)) return 'high'
  if (/中等|谨慎|观望|注意/.test(all)) return 'medium'
  return 'low'
}

function extractAdvice(sections: Section[]): string[] {
  const advices: string[] = []
  for (const s of sections) {
    for (const line of s.body) {
      if (/手里有.*赶紧|卖出|别犹豫|管住手|千万别买|关注|可以考虑/.test(line)) {
        advices.push(line.replace(/^[-*]\s*/, '').replace(/\*\*/g, '').trim())
      }
    }
  }
  return advices.slice(0, 3)
}

function extractKeyMetrics(sections: Section[]): { label: string; value: string; signal: 'up' | 'down' | 'neutral' }[] {
  const metrics: { label: string; value: string; signal: 'up' | 'down' | 'neutral' }[] = []
  const all = sections.map(s => s.body.join('\n')).join('\n')
  if (/出货/.test(all)) metrics.push({ label: '主力行为', value: '出货', signal: 'down' })
  else if (/吸筹/.test(all)) metrics.push({ label: '主力行为', value: '吸筹', signal: 'up' })
  else if (/洗盘/.test(all)) metrics.push({ label: '主力行为', value: '洗盘', signal: 'neutral' })
  if (/高位/.test(all)) metrics.push({ label: '股价位置', value: '高位', signal: 'down' })
  else if (/中位|半山腰/.test(all)) metrics.push({ label: '股价位置', value: '中位', signal: 'neutral' })
  else if (/低位|底部/.test(all)) metrics.push({ label: '股价位置', value: '低位', signal: 'up' })
  if (/狂热|亢奋/.test(all)) metrics.push({ label: '市场情绪', value: '狂热', signal: 'up' })
  else if (/冷清|低迷/.test(all)) metrics.push({ label: '市场情绪', value: '冷清', signal: 'down' })
  else if (/活跃/.test(all)) metrics.push({ label: '市场情绪', value: '活跃', signal: 'up' })
  if (/放量/.test(all)) metrics.push({ label: '量能', value: '放量', signal: 'up' })
  else if (/缩量/.test(all)) metrics.push({ label: '量能', value: '缩量', signal: 'down' })
  return metrics
}

function extractEvidence(sections: Section[]): { text: string; tag: string }[] {
  const evidence: { text: string; tag: string }[] = []
  for (const s of sections) {
    if (!s.title.includes('主力') && !s.title.includes('情绪') && !s.title.includes('预期')) continue
    for (const line of s.body) {
      const t = line.replace(/^[-*]\s*/, '').replace(/\*\*/g, '').trim()
      if (t.length > 8 && /\d/.test(t)) {
        let tag = '数据'
        if (/出货|流出|抛售/.test(t)) tag = '出货'
        else if (/拉高|拉升|冲/.test(t)) tag = '拉高'
        else if (/散户|接盘/.test(t)) tag = '散户接盘'
        else if (/下跌|跌/.test(t)) tag = '下跌'
        else if (/放量|成交量/.test(t)) tag = '量能'
        evidence.push({ text: t, tag })
      }
    }
  }
  return evidence.slice(0, 3)
}

function renderLine(line: string) {
  return line
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white/90 font-semibold">$1</strong>')
    .replace(/(\d+\.?\d*%?)/g, '<span class="font-semibold text-white/80 font-mono">$1</span>')
}

// ── 配置 ──

const SECTION_META: Record<string, { icon: any; accent: string; label: string }> = {
  '一、当前状态': { icon: Target, accent: '#8B5CF6', label: '一句话总结' },
  '一、当前状态（一句话总结）': { icon: Target, accent: '#8B5CF6', label: '一句话总结' },
  '二、主力行为分析': { icon: BarChart3, accent: '#8B5CF6', label: '主力行为' },
  '三、市场情绪与位置': { icon: Activity, accent: '#06B6D4', label: '情绪与位置' },
  '四、风险与机会': { icon: AlertTriangle, accent: '#F59E0B', label: '风险与机会' },
  '五、预期差分析': { icon: Sparkles, accent: '#F59E0B', label: '预期差' },
}

const SIGNAL = {
  up:      { color: '#F43F5E', bg: 'rgba(244,63,94,0.06)' },
  down:    { color: '#10B981', bg: 'rgba(16,185,129,0.06)' },
  neutral: { color: '#64748B', bg: 'rgba(100,116,139,0.06)' },
}

const RISK_CONFIG = {
  high:   { color: '#F43F5E', glow: 'rgba(244,63,94,0.12)', label: '高风险', ring: 'rgba(244,63,94,0.2)' },
  medium: { color: '#F59E0B', glow: 'rgba(245,158,11,0.12)', label: '中风险', ring: 'rgba(245,158,11,0.2)' },
  low:    { color: '#10B981', glow: 'rgba(16,185,129,0.12)', label: '低风险', ring: 'rgba(16,185,129,0.2)' },
}

// ── 入场动画 ──

function useStagger(count: number, delay = 50) {
  const [visible, setVisible] = useState(false)
  useEffect(() => { requestAnimationFrame(() => setVisible(true)) }, [])
  return (i: number) => ({
    opacity: visible ? 1 : 0,
    transform: visible ? 'translateY(0)' : 'translateY(14px)',
    transition: `all 0.5s cubic-bezier(0.16,1,0.3,1) ${i * delay}ms`,
  })
}

// ── 主组件 ──

export default function AnalysisView({ text: rawText }: AnalysisViewProps) {
  const text = typeof rawText === 'string' ? rawText : String(rawText ?? '')
  const sections = parseSections(text)
  const stagger = useStagger(12, 60)

  if (sections.length === 0) {
    return <div className="text-xs text-white/30 leading-relaxed whitespace-pre-wrap">{text}</div>
  }

  const oneLiner = extractOneLiner(sections)
  const verdict = extractVerdict(sections)
  const riskLevel = extractRiskLevel(sections)
  const advice = extractAdvice(sections)
  const metrics = extractKeyMetrics(sections)
  const evidence = extractEvidence(sections)
  const risk = RISK_CONFIG[riskLevel]

  return (
    <div className="space-y-4">

      {/* ═══ 信号矩阵 ═══ */}
      {metrics.length > 0 && (
        <div {...stagger(0)} className="grid grid-cols-2 sm:grid-cols-4 gap-px rounded-xl overflow-hidden border border-white/[0.04]"
          style={{ background: 'rgba(255,255,255,0.02)' }}>
          {metrics.map((m, i) => {
            const cfg = SIGNAL[m.signal]
            return (
              <div key={i} className="p-4 text-center transition-colors duration-200 hover:bg-white/[0.02]"
                style={{ background: 'rgba(9,9,11,0.95)' }}>
                <div className="text-[10px] text-white/15 uppercase tracking-[0.15em] mb-2">{m.label}</div>
                <div className="text-[15px] font-bold tracking-tight" style={{ color: cfg.color }}>{m.value}</div>
              </div>
            )
          })}
        </div>
      )}

      {/* ═══ Hero: 一句话总结 ═══ */}
      {oneLiner && (
        <div {...stagger(1)} className="relative rounded-xl border border-white/[0.06] overflow-hidden"
          style={{ background: `linear-gradient(135deg, ${risk.glow} 0%, rgba(9,9,11,1) 50%)` }}>
          <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-full" style={{ background: risk.color }} />
          <div className="p-5 pl-6">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                style={{ background: risk.glow, border: `1px solid ${risk.ring}` }}>
                {riskLevel === 'high' ? <TrendingDown className="w-4 h-4" style={{ color: risk.color }} /> :
                 riskLevel === 'low' ? <TrendingUp className="w-4 h-4" style={{ color: risk.color }} /> :
                 <Minus className="w-4 h-4" style={{ color: risk.color }} />}
              </div>
              <div className="flex-1">
                <p className="text-[13px] font-medium text-white/80 leading-relaxed">{oneLiner}</p>
                <div className="flex items-center gap-3 mt-2.5">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold"
                    style={{ background: risk.glow, color: risk.color, border: `1px solid ${risk.ring}` }}>
                    <span className="w-1.5 h-1.5 rounded-full animate-glow-pulse" style={{ background: risk.color }} />
                    {risk.label}
                  </span>
                  {verdict?.confidence && (
                    <span className="text-[10px] text-white/15">置信度 {verdict.confidence}</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ 核心结论 ═══ */}
      {verdict && (
        <div {...stagger(2)} className="relative rounded-xl border border-white/[0.06] overflow-hidden"
          style={{ background: `linear-gradient(90deg, ${risk.glow} 0%, transparent 60%)` }}>
          <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-full" style={{ background: risk.color }} />
          <div className="p-5 pl-6">
            <div className="flex items-center gap-2 mb-2">
              <Crosshair className="w-3.5 h-3.5" style={{ color: risk.color }} />
              <span className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: risk.color }}>
                核心判断
              </span>
            </div>
            <p className="text-[12px] text-white/60 leading-[1.8]">{verdict.text}</p>
          </div>
        </div>
      )}

      {/* ═══ 证据链 ═══ */}
      {evidence.length > 0 && (
        <div {...stagger(3)} className="rounded-xl border border-white/[0.06] p-5"
          style={{ background: 'rgba(12,12,20,0.6)' }}>
          <div className="flex items-center gap-2 mb-4">
            <Radio className="w-3.5 h-3.5 text-violet-400/40" />
            <span className="text-[10px] font-bold text-violet-400/40 uppercase tracking-[0.2em]">证据链</span>
          </div>
          <div className="space-y-3">
            {evidence.map((ev, i) => (
              <div key={i} className="flex items-start gap-4 group">
                <div className="flex flex-col items-center">
                  <div className="w-6 h-6 rounded-full border border-white/[0.06] flex items-center justify-center
                    text-[10px] font-mono text-white/20 group-hover:border-violet-500/20 transition-colors">
                    {i + 1}
                  </div>
                  {i < evidence.length - 1 && <div className="w-px h-3 bg-white/[0.04] mt-1" />}
                </div>
                <div className="flex-1 flex items-start gap-3 pt-0.5">
                  <span className="text-[11px] text-white/40 leading-relaxed flex-1">{ev.text}</span>
                  <span className="shrink-0 px-2 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wider
                    border border-violet-500/10 text-violet-300/30 bg-violet-500/[0.04]">
                    {ev.tag}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ 操作建议 ═══ */}
      {advice.length > 0 && (
        <div {...stagger(4)} className="rounded-xl border border-amber-500/10 p-5"
          style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.02) 0%, transparent 60%)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-3.5 h-3.5 text-amber-400/50" />
            <span className="text-[10px] font-bold text-amber-400/50 uppercase tracking-[0.2em]">操作建议</span>
          </div>
          <div className="space-y-2">
            {advice.map((a, i) => (
              <div key={i} className="flex items-start gap-3 py-2 px-3 rounded-lg hover:bg-white/[0.02] transition-colors">
                <span className="text-[10px] text-amber-400/30 font-mono mt-0.5">{String(i + 1).padStart(2, '0')}</span>
                <span className="text-[11px] text-white/40 leading-relaxed">{a}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ 详细分析 sections ═══ */}
      <div {...stagger(5)} className="space-y-2">
        {sections.map((section, si) => {
          const meta = Object.entries(SECTION_META).find(([k]) => section.title.startsWith(k))?.[1]
          const accent = meta?.accent ?? '#64748B'
          const Icon = meta?.icon ?? FileText
          const label = meta?.label ?? section.title.replace(/[#一二三四五六七八九十、（）]/g, '').trim()

          return (
            <details key={si} className="group" open={si <= 1}>
              <summary className="flex items-center gap-3 px-4 py-3 cursor-pointer rounded-xl
                list-none [&::-webkit-details-marker]:hidden border border-white/[0.04]
                hover:border-white/[0.08] hover:bg-white/[0.02] transition-all duration-200"
                style={{ background: 'rgba(12,12,20,0.5)' }}>
                <div className="w-6 h-6 rounded-lg flex items-center justify-center"
                  style={{ background: accent + '10' }}>
                  <Icon className="w-3 h-3" style={{ color: accent }} />
                </div>
                <span className="text-[11px] font-semibold text-white/50 flex-1 tracking-wide">{label}</span>
                <ChevronRight className="w-3.5 h-3.5 text-white/10 transition-transform duration-200 group-open:rotate-90" />
              </summary>
              <div className="mt-1 ml-3 pl-6 border-l border-white/[0.04] space-y-2 py-3">
                <SectionBody body={section.body} accent={accent} />
              </div>
            </details>
          )
        })}
      </div>
    </div>
  )
}

// ── Section 内容渲染 ──

function SectionBody({ body, accent }: { body: string[]; accent: string }) {
  const chunks = chunkBody(body)
  return (
    <div className="space-y-2">
      {chunks.map((chunk, ci) => {
        if (chunk.every(l => l.trim().startsWith('-'))) {
          return (
            <ul key={ci} className="space-y-1.5">
              {chunk.map((li, liIdx) => {
                const t = li.replace(/^-\s*/, '')
                return (
                  <li key={liIdx} className="flex items-start gap-2 text-[11px] text-white/35 leading-relaxed">
                    <span className="block w-1 h-1 mt-[6px] shrink-0 rounded-full" style={{ background: accent + '30' }} />
                    <span dangerouslySetInnerHTML={{ __html: renderLine(t) }} />
                  </li>
                )
              })}
            </ul>
          )
        }
        const joined = chunk.join('\n')
        if (/\*\*(结论|核心判断|判断依据|总结)：?\*\*/.test(joined)) {
          return (
            <div key={ci} className="p-3 rounded-lg border-l-[3px]" style={{ borderLeftColor: accent + '40', background: 'rgba(255,255,255,0.015)' }}>
              <p className="text-[11px] font-medium text-white/50 leading-relaxed" dangerouslySetInnerHTML={{ __html: renderLine(joined) }} />
            </div>
          )
        }
        return (
          <p key={ci} className="text-[11px] text-white/30 leading-relaxed" dangerouslySetInnerHTML={{ __html: renderLine(joined) }} />
        )
      })}
    </div>
  )
}

function chunkBody(body: string[]): string[][] {
  const chunks: string[][] = []
  let cur: string[] = []
  for (const line of body) {
    if (line.trim() === '' && cur.length > 0) { chunks.push(cur); cur = [] }
    else if (line.trim() !== '') cur.push(line)
  }
  if (cur.length > 0) chunks.push(cur)
  return chunks
}
