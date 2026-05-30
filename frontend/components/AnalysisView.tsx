'use client'

import {
  TrendingUp, TrendingDown, AlertTriangle, Lightbulb,
  BarChart3, Target, Activity, FileText,
  Shield, Eye, ArrowDown, ArrowUp, Minus,
  ChevronRight, Zap, XCircle, CheckCircle,
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
  // 第一个 section 的第一行非空文本
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

function extractKeyMetrics(sections: Section[]): { label: string; value: string; sentiment: 'up' | 'down' | 'neutral' }[] {
  const metrics: { label: string; value: string; sentiment: 'up' | 'down' | 'neutral' }[] = []
  const all = sections.map(s => s.body.join('\n')).join('\n')

  // 主力行为
  if (/出货/.test(all)) metrics.push({ label: '主力行为', value: '出货', sentiment: 'down' })
  else if (/吸筹/.test(all)) metrics.push({ label: '主力行为', value: '吸筹', sentiment: 'up' })
  else if (/洗盘/.test(all)) metrics.push({ label: '主力行为', value: '洗盘', sentiment: 'neutral' })
  else if (/主升/.test(all)) metrics.push({ label: '主力行为', value: '主升', sentiment: 'up' })

  // 位置
  if (/高位/.test(all)) metrics.push({ label: '股价位置', value: '高位', sentiment: 'down' })
  else if (/中位|半山腰/.test(all)) metrics.push({ label: '股价位置', value: '中位', sentiment: 'neutral' })
  else if (/低位|底部/.test(all)) metrics.push({ label: '股价位置', value: '低位', sentiment: 'up' })

  // 情绪
  if (/狂热|亢奋/.test(all)) metrics.push({ label: '市场情绪', value: '狂热', sentiment: 'up' })
  else if (/冷清|低迷/.test(all)) metrics.push({ label: '市场情绪', value: '冷清', sentiment: 'down' })
  else if (/活跃/.test(all)) metrics.push({ label: '市场情绪', value: '活跃', sentiment: 'up' })
  else if (/温和|修复/.test(all)) metrics.push({ label: '市场情绪', value: '温和', sentiment: 'neutral' })

  // 量能
  if (/放量/.test(all)) metrics.push({ label: '量能', value: '放量', sentiment: 'up' })
  else if (/缩量/.test(all)) metrics.push({ label: '量能', value: '缩量', sentiment: 'down' })

  return metrics
}

function renderLine(line: string) {
  return line
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-foreground font-semibold">$1</strong>')
    .replace(/(\d+\.?\d*%?)/g, '<span class="font-semibold text-foreground font-mono">$1</span>')
}

function strip(s: string) { return s.replace(/\*\*(.+?)\*\*/g, '$1').replace(/[#*\-]/g, '').trim() }

// ── 配置 ──

const SECTION_META: Record<string, { icon: any; accent: string; label: string }> = {
  '一、当前状态': { icon: Target, accent: '#3B82F6', label: '一句话总结' },
  '一、当前状态（一句话总结）': { icon: Target, accent: '#3B82F6', label: '一句话总结' },
  '二、主力行为分析': { icon: BarChart3, accent: '#A78BFA', label: '主力行为' },
  '三、市场情绪与位置': { icon: Activity, accent: '#7B9BAF', label: '情绪与位置' },
  '四、风险与机会': { icon: AlertTriangle, accent: '#C5A03A', label: '风险与机会' },
  '五、预期差分析': { icon: Lightbulb, accent: '#D4943A', label: '预期差' },
}

const SENTIMENT_CONFIG = {
  up: { color: '#22C55E', bg: '#22C55E0A', icon: ArrowUp, label: '积极' },
  down: { color: '#EF4444', bg: '#EF44440A', icon: ArrowDown, label: '风险' },
  neutral: { color: '#94A3B8', bg: '#94A3B80A', icon: Minus, label: '中性' },
}

// ── 组件 ──

export default function AnalysisView({ text: rawText }: AnalysisViewProps) {
  const text = typeof rawText === 'string' ? rawText : String(rawText ?? '')
  const sections = parseSections(text)

  if (sections.length === 0) {
    return <div className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">{text}</div>
  }

  const oneLiner = extractOneLiner(sections)
  const verdict = extractVerdict(sections)
  const riskLevel = extractRiskLevel(sections)
  const advice = extractAdvice(sections)
  const metrics = extractKeyMetrics(sections)

  const riskConfig = {
    high: { color: '#EF4444', label: '高风险', icon: XCircle },
    medium: { color: '#F59E0B', label: '中等风险', icon: AlertTriangle },
    low: { color: '#22C55E', label: '低风险', icon: CheckCircle },
  }
  const risk = riskConfig[riskLevel]
  const RiskIcon = risk.icon

  return (
    <div className="space-y-3">

      {/* ═══ Hero: 一句话总结 + 风险徽章 ═══ */}
      {oneLiner && (
        <div className="relative overflow-hidden rounded-lg border border-border bg-gradient-to-br from-card to-card/80 p-4">
          <div className="absolute top-0 right-0 w-32 h-32 opacity-[0.03]"
            style={{ background: `radial-gradient(circle, ${risk.color}, transparent)` }} />
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: risk.color + '12' }}>
              <RiskIcon className="w-4 h-4" style={{ color: risk.color }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium leading-snug text-foreground">{oneLiner}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
                  style={{ background: risk.color + '15', color: risk.color }}>
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: risk.color }} />
                  {risk.label}
                </span>
                {verdict?.confidence && (
                  <span className="text-[10px] text-muted-foreground">置信度: {verdict.confidence}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ 核心指标卡片 ═══ */}
      {metrics.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {metrics.map((m, i) => {
            const cfg = SENTIMENT_CONFIG[m.sentiment]
            const Icon = cfg.icon
            return (
              <div key={i} className="rounded-lg border border-border p-3 flex flex-col items-center gap-1.5"
                style={{ background: cfg.bg }}>
                <Icon className="w-3.5 h-3.5" style={{ color: cfg.color }} />
                <span className="text-[10px] text-muted-foreground">{m.label}</span>
                <span className="text-sm font-bold font-mono" style={{ color: cfg.color }}>{m.value}</span>
              </div>
            )
          })}
        </div>
      )}

      {/* ═══ 核心结论 ═══ */}
      {verdict && (
        <div className="rounded-lg border-l-[3px] p-3.5"
          style={{ borderLeftColor: risk.color, background: risk.color + '06' }}>
          <div className="flex items-center gap-2 mb-1.5">
            <Zap className="w-3.5 h-3.5" style={{ color: risk.color }} />
            <span className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: risk.color }}>
              核心结论
            </span>
          </div>
          <p className="text-xs font-medium text-foreground leading-relaxed">{verdict.text}</p>
        </div>
      )}

      {/* ═══ 操作建议 ═══ */}
      {advice.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-3.5">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-500">操作建议</span>
          </div>
          <div className="space-y-1.5">
            {advice.map((a, i) => (
              <div key={i} className="flex items-start gap-2">
                <ChevronRight className="w-3 h-3 mt-0.5 shrink-0 text-amber-500/60" />
                <span className="text-xs text-foreground/80 leading-relaxed">{a}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ 详细分析 sections ═══ */}
      <div className="space-y-2">
        {sections.map((section, si) => {
          const meta = Object.entries(SECTION_META).find(([k]) => section.title.startsWith(k))?.[1]
          const accent = meta?.accent ?? '#64748B'
          const Icon = meta?.icon ?? FileText
          const label = meta?.label ?? section.title.replace(/[#一二三四五六七八九十、（）]/g, '').trim()

          return (
            <details key={si} className="group" open={si <= 1}>
              <summary className="flex items-center gap-2 px-3 py-2.5 cursor-pointer rounded-t-lg
                list-none [&::-webkit-details-marker]:hidden bg-card border border-border
                hover:bg-accent/30 transition-colors">
                <div className="w-5 h-5 rounded flex items-center justify-center"
                  style={{ background: accent + '15' }}>
                  <Icon className="w-3 h-3" style={{ color: accent }} />
                </div>
                <span className="text-[11px] font-semibold tracking-wide text-foreground/80 flex-1">{label}</span>
                <ChevronRight className="w-3.5 h-3.5 text-muted-foreground transition-transform group-open:rotate-90" />
              </summary>
              <div className="border border-t-0 border-border rounded-b-lg bg-card/50 px-4 py-3">
                <SectionBody body={section.body} accent={accent} isSummary={si === 0} />
              </div>
            </details>
          )
        })}
      </div>
    </div>
  )
}

// ── Section 内容渲染 ──

function SectionBody({ body, accent, isSummary }: { body: string[]; accent: string; isSummary: boolean }) {
  const chunks = chunkBody(body)
  return (
    <div className="space-y-2">
      {chunks.map((chunk, ci) => {
        // 纯列表
        if (chunk.every(l => l.trim().startsWith('-'))) {
          return (
            <ul key={ci} className="space-y-1">
              {chunk.map((li, liIdx) => {
                const t = li.replace(/^-\s*/, '')
                return (
                  <li key={liIdx} className="flex items-start gap-2 text-xs text-muted-foreground leading-relaxed">
                    <span className="block w-1 h-1 mt-[7px] shrink-0 rounded-full" style={{ background: accent + '50' }} />
                    <span dangerouslySetInnerHTML={{ __html: renderLine(t) }} />
                  </li>
                )
              })}
            </ul>
          )
        }

        // 结论块
        const joined = chunk.join('\n')
        if (/\*\*(结论|核心判断|判断依据|总结)：?\*\*/.test(joined)) {
          return (
            <div key={ci} className="p-2.5 rounded bg-[hsl(var(--bg-surface))] border-l-[3px]"
              style={{ borderLeftColor: accent + '60' }}>
              <p className="text-xs font-medium text-foreground leading-relaxed"
                dangerouslySetInnerHTML={{ __html: renderLine(joined) }} />
            </div>
          )
        }

        // 普通段落
        return (
          <p key={ci} className="text-xs text-muted-foreground leading-relaxed"
            dangerouslySetInnerHTML={{ __html: renderLine(joined) }} />
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
