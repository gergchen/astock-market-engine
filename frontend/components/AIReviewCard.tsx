'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, AlertTriangle, Activity, FileText } from 'lucide-react'

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="text-foreground font-semibold">{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="px-1 py-0.5 rounded text-[11px] bg-muted text-muted-foreground font-mono">{part.slice(1, -1)}</code>
    }
    return part
  })
}

function renderMarkdown(text: string): React.ReactNode {
  if (!text) return null
  const lines = text.split('\n')
  const elements: React.ReactNode[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]
    if (!line.trim()) { i++; continue }

    if (line.match(/^#{1,3}\s/)) {
      const level = line.match(/^(#{1,3})/)![1].length
      const title = line.replace(/^#{1,3}\s+/, '').replace(/\*\*/g, '')
      const sizeCls = level === 1 ? 'text-sm' : level === 2 ? 'text-xs' : 'text-[11px]'
      elements.push(
        <h3 key={i} className={sizeCls + ' font-semibold text-foreground mt-5 mb-2 first:mt-0 tracking-tight'}>
          {title}
        </h3>
      )
      i++; continue
    }

    if (line.match(/^[\-\*]\s/)) {
      const items: string[] = []
      while (i < lines.length && lines[i].match(/^[\-\*]\s/)) {
        items.push(lines[i].replace(/^[\-\*]\s+/, ''))
        i++
      }
      elements.push(
        <ul key={i} className="list-disc list-inside space-y-0.5 text-xs text-muted-foreground mb-2 ml-1">
          {items.map((item, j) => <li key={j}>{renderInline(item)}</li>)}
        </ul>
      )
      continue
    }

    elements.push(
      <p key={i} className="text-xs text-muted-foreground leading-relaxed mb-2">
        {renderInline(line)}
      </p>
    )
    i++
  }
  return elements
}

interface MetricItem {
  label: string
  value: string
  icon: React.ReactNode
}

function extractMetrics(text: string): MetricItem[] {
  const metrics: MetricItem[] = []
  const patterns: { regex: RegExp; label: string; icon: React.ReactNode; format?: (m: RegExpMatchArray) => string }[] = [
    { regex: /涨停[：:]?\s*(\d+)\s*只?/i, label: '涨停', icon: <TrendingUp className="w-3 h-3 text-up" /> },
    { regex: /跌停[：:]?\s*(\d+)\s*只?/i, label: '跌停', icon: <TrendingUp className="w-3 h-3 text-down rotate-180" /> },
    { regex: /炸板率[：:]?\s*([\d.]+)\s*%/i, label: '炸板率', icon: <AlertTriangle className="w-3 h-3 text-amber-400" />, format: m => m[1] + '%' },
    { regex: /连板高度[：:]?\s*(\d+)\s*板?/i, label: '连板高度', icon: <Activity className="w-3 h-3 text-orange-400" />, format: m => m[1] + '板' },
  ]
  for (const p of patterns) {
    const match = text.match(p.regex)
    if (match) {
      metrics.push({
        label: p.label,
        value: p.format ? p.format(match) : match[1] + '只',
        icon: p.icon,
      })
    }
  }
  return metrics
}

interface AIReviewCardProps {
  text: string
  extraMetrics?: { label: string; value: string | number }[]
}

export default function AIReviewCard({ text, extraMetrics }: AIReviewCardProps) {
  if (!text) return null

  const autoMetrics = extractMetrics(text)
  const hasMetrics = autoMetrics.length > 0 || (extraMetrics && extraMetrics.length > 0)

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-3.5 h-3.5 text-muted-foreground" />
          <CardTitle className="text-sm">市场复盘</CardTitle>
          <span className="text-[10px] text-muted-foreground ml-auto">收盘总结</span>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {hasMetrics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-5">
            {autoMetrics.map((m, i) => (
              <div key={i} className="p-3 rounded border border-border bg-[hsl(var(--bg-surface))]">
                <div className="flex items-center gap-1.5 mb-1">
                  {m.icon}
                  <span className="text-[10px] text-muted-foreground">{m.label}</span>
                </div>
                <div className="text-base font-semibold font-mono">{m.value}</div>
              </div>
            ))}
            {extraMetrics?.map((m, i) => (
              <div key={'ext-' + i} className="p-3 rounded border border-border bg-[hsl(var(--bg-surface))]">
                <span className="text-[10px] text-muted-foreground">{m.label}</span>
                <div className="text-base font-semibold font-mono">{m.value}</div>
              </div>
            ))}
          </div>
        )}

        <div className="analysis-content">
          {renderMarkdown(text)}
        </div>
      </CardContent>
    </Card>
  )
}
