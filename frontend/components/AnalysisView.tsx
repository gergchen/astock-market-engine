'use client'

import {
  TrendingUp, TrendingDown, AlertTriangle, Lightbulb,
  BarChart3, Target, Activity, FileText,
} from 'lucide-react'

interface AnalysisViewProps { text: string }

function parseSections(text: string) {
  const lines = text.split('\n')
  const sections: { title: string; body: string[] }[] = []
  let cur: { title: string; body: string[] } | null = null
  for (const line of lines) {
    const m = line.match(/^##\s+(.+)/)
    if (m) { if (cur) sections.push(cur); cur = { title: m[1].trim(), body: [] } }
    else if (cur) cur.body.push(line)
  }
  if (cur) sections.push(cur)
  return sections
}

function renderLine(line: string) {
  return line
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-foreground font-semibold">$1</strong>')
    .replace(/(\d+\.?\d*%?)/g, '<span class="font-semibold text-foreground font-mono">$1</span>')
}

function strip(s: string) { return s.replace(/\*\*(.+?)\*\*/g, '$1').replace(/[#*\-]/g, '').trim() }

function sentimentTag(text: string): 'up' | 'down' | 'neutral' | null {
  const t = strip(text).toLowerCase()
  if (/风险|警惕|压力|下跌|卖出|危险|回避/.test(t)) return 'down'
  if (/机会|突破|利好|上涨|买入|关注|布局|看好|积极|强势|放量|主升/.test(t)) return 'up'
  if (/谨慎|中性|观望|震荡|分歧/.test(t)) return 'neutral'
  return null
}

function extractTags(body: string[]) {
  const tags: { label: string; color: string }[] = []
  const text = body.join(' ')
  const emotionMap: [RegExp, string, string][] = [
    [/冷清|低迷|冰点/, '冷清', 'hsl(var(--muted-foreground))'],
    [/温和|修复|回暖/, '温和', 'hsl(var(--down))'],
    [/活跃|亢奋|热烈/, '活跃', 'hsl(var(--up))'],
    [/狂热|疯狂|高潮/, '狂热', 'hsl(var(--up))'],
  ]
  for (const [re, label, color] of emotionMap) { if (re.test(text)) { tags.push({ label, color }); break } }
  const positionMap: [RegExp, string, string][] = [
    [/低位|底部|低估/, '低位', 'hsl(var(--down))'],
    [/中位|中途/, '中位', 'hsl(var(--primary))'],
    [/高位|顶部|高估/, '高位', 'hsl(var(--up))'],
  ]
  for (const [re, label, color] of positionMap) { if (re.test(text)) { tags.push({ label, color }); break } }
  const capitalMap: [RegExp, string, string][] = [
    [/吸筹/, '吸筹', '#A78BFA'], [/洗盘/, '洗盘', '#7B9BAF'],
    [/主升/, '主升', '#38A868'], [/出货/, '出货', '#D94040'],
  ]
  for (const [re, label, color] of capitalMap) { if (re.test(text)) { tags.push({ label, color }); break } }
  return tags
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

const SECTIONS: Record<string, { icon: any; accent: string }> = {
  '一、当前状态': { icon: Target, accent: 'var(--primary)' },
  '一、当前状态（一句话总结）': { icon: Target, accent: 'var(--primary)' },
  '二、主力行为分析': { icon: BarChart3, accent: '#A78BFA' },
  '三、市场情绪与位置': { icon: Activity, accent: '#7B9BAF' },
  '四、风险与机会': { icon: AlertTriangle, accent: '#C5A03A' },
  '五、预期差分析': { icon: Lightbulb, accent: '#D4943A' },
}

export default function AnalysisView({ text }: AnalysisViewProps) {
  const sections = parseSections(text)
  if (sections.length === 0) {
    return <div className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">{text}</div>
  }

  return (
    <div className="space-y-2">
      {sections.map((section, si) => {
        const meta = Object.entries(SECTIONS).find(([k]) => section.title.startsWith(k))?.[1]
        const accent = meta?.accent ?? 'var(--primary)'
        const Icon = meta?.icon ?? FileText
        const tags = extractTags(section.body)
        const isSummary = si === 0

        return (
          <div key={si} className="bg-card border border-border" style={{ borderLeft: `3px solid ${accent}60` }}>
            <div className="flex items-center justify-between px-4 pt-3 pb-2">
              <div className="flex items-center gap-2">
                <Icon className="w-3.5 h-3.5 shrink-0" style={{ color: accent }} />
                <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  {section.title.replace(/[#一二三四五六七八九十、（）]/g, '').trim() || section.title}
                </span>
              </div>
              {tags.length > 0 && (
                <div className="flex gap-1">
                  {tags.map((t, i) => (
                    <span key={i}
                      className="inline-block px-1.5 py-[1px] text-[9px] font-medium tracking-wide rounded"
                      style={{ background: t.color + '12', color: t.color }}>
                      {t.label}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="px-4 pb-4">
              {chunkBody(section.body).map((chunk, ci) => {
                const joined = chunk.join('\n')
                const tag = sentimentTag(joined)

                if (chunk.every(l => l.trim().startsWith('-'))) {
                  return (
                    <ul key={ci} className="space-y-1 mt-2">
                      {chunk.map((li, liIdx) => {
                        const t = li.replace(/^-\s*/, '')
                        return (
                          <li key={liIdx} className="flex items-start gap-2 text-xs text-muted-foreground leading-relaxed">
                            <span className="block w-1 h-1 mt-[7px] shrink-0 rounded-full" style={{ background: accent + '40' }} />
                            <span dangerouslySetInnerHTML={{ __html: renderLine(t) }} />
                          </li>
                        )
                      })}
                    </ul>
                  )
                }

                if (isSummary && ci === 0) {
                  return (
                    <div key={ci} className="mt-1">
                      <p className="text-sm font-semibold leading-snug tracking-tight text-foreground"
                        dangerouslySetInnerHTML={{ __html: renderLine(joined) }} />
                    </div>
                  )
                }

                const conclusionMatch = joined.match(/\*\*(结论|核心判断|判断|关键)：?\*\*/)
                if (conclusionMatch) {
                  return (
                    <div key={ci} className="mt-2 p-3 bg-[hsl(var(--bg-surface))] border-l-[3px]"
                      style={{ borderLeftColor: accent + '60' }}>
                      <p className="text-xs font-medium text-foreground leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: renderLine(joined) }} />
                    </div>
                  )
                }

                if (tag === 'down' || tag === 'up') {
                  const isRisk = tag === 'down'
                  return (
                    <div key={ci} className="mt-2 flex items-start gap-3 p-3 rounded"
                      style={{
                        background: (isRisk ? 'hsl(var(--down))' : 'hsl(var(--up))') + '06',
                        borderLeft: '3px solid ' + (isRisk ? 'hsl(var(--down))' : 'hsl(var(--up))'),
                      }}>
                      <div className="w-5 h-5 flex items-center justify-center shrink-0 mt-[1px]"
                        style={{ background: (isRisk ? 'hsl(var(--down))' : 'hsl(var(--up))') + '12' }}>
                        {isRisk
                          ? <TrendingDown className="w-3 h-3" style={{ color: 'hsl(var(--down))' }} />
                          : <TrendingUp className="w-3 h-3" style={{ color: 'hsl(var(--up))' }} />
                        }
                      </div>
                      <p className="text-xs leading-relaxed"
                        style={{ color: isRisk ? 'hsl(var(--down))' : 'hsl(var(--up))' }}
                        dangerouslySetInnerHTML={{ __html: renderLine(joined) }} />
                    </div>
                  )
                }

                return (
                  <p key={ci} className="mt-2 text-xs text-muted-foreground leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: renderLine(joined) }} />
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
