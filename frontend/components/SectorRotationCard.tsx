'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { TrendingUp, TrendingDown, RefreshCw, Activity, BarChart3 } from 'lucide-react'
import { EmptyState } from '@/components/ui/states'

interface SectorRecord {
  name: string
  change: number
  flow: number
  flow_yi?: number
}

interface RotationData {
  industry?: {
    加强: SectorRecord[]
    持续: SectorRecord[]
    退潮: SectorRecord[]
    反弹: SectorRecord[]
  }
  concept?: {
    加强: SectorRecord[]
    持续: SectorRecord[]
    退潮: SectorRecord[]
    反弹: SectorRecord[]
  }
  board_distribution?: {
    name: string
    涨停数: number
    flow: number
    change: number
  }[]
  最强板块?: string
  最强板块涨停数?: number
}

interface Props {
  data: RotationData | null
}

function SectorSection({ records, title, icon, color }: {
  records: SectorRecord[]
  title: string
  icon: React.ReactNode
  color: string
}) {
  if (!records?.length) return null
  return (
    <div className="mb-3">
      <div className={`flex items-center gap-1 mb-1.5 text-xs font-medium ${color}`}>
        {icon}
        <span>{title} ({records.length})</span>
      </div>
      <div className="space-y-0.5">
        {records.slice(0, 5).map((r, i) => (
          <div
            key={i}
            className="flex items-center justify-between text-xs px-2 py-1.5 rounded hover:bg-muted transition-colors"
          >
            <span className="font-medium truncate max-w-[120px]">{r.name}</span>
            <div className="flex items-center gap-2 shrink-0">
              <span className={r.change >= 0 ? 'text-up' : 'text-down'}>
                {r.change >= 0 ? '+' : ''}{r.change.toFixed(2)}%
              </span>
              <span className={r.flow >= 0 ? 'text-up' : 'text-down'}>
                {r.flow >= 0 ? '+' : ''}{r.flow_yi?.toFixed(2) ?? (r.flow / 1e8).toFixed(2)}亿
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function CategoryPanel({ current }: { current: RotationData['industry'] }) {
  if (!current) return <EmptyState type="no_data" message="暂无数据" />

  const hasData = (current.加强?.length || 0) > 0 ||
    (current.持续?.length || 0) > 0 ||
    (current.退潮?.length || 0) > 0 ||
    (current.反弹?.length || 0) > 0

  if (!hasData) {
    return (
      <div className="text-center text-xs text-muted-foreground py-6">
        今日市场分化不明显，板块轮动信号较弱
      </div>
    )
  }

  return (
    <>
      <SectorSection
        records={current.加强}
        title="加强 (涨幅+资金双正)"
        icon={<TrendingUp className="w-3 h-3" />}
        color="text-up"
      />
      <SectorSection
        records={current.持续}
        title="持续 (有涨幅但资金未跟进)"
        icon={<Activity className="w-3 h-3" />}
        color="text-amber-400"
      />
      <SectorSection
        records={current.反弹}
        title="反弹 (企稳信号)"
        icon={<RefreshCw className="w-3 h-3" />}
        color="text-muted-foreground"
      />
      <SectorSection
        records={current.退潮}
        title="退潮 (跌幅+资金流出)"
        icon={<TrendingDown className="w-3 h-3" />}
        color="text-down"
      />
    </>
  )
}

export default function SectorRotationCard({ data }: Props) {
  const [tab, setTab] = useState('industry')

  if (!data) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-muted-foreground" />
            <CardTitle className="text-sm">板块轮动分析</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <EmptyState type="no_data" message="板块轮动数据暂未加载" />
        </CardContent>
      </Card>
    )
  }

  const hasAnyData = (data.industry?.加强?.length || 0) > 0 ||
    (data.industry?.退潮?.length || 0) > 0 ||
    (data.concept?.加强?.length || 0) > 0 ||
    (data.concept?.退潮?.length || 0) > 0

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-muted-foreground" />
          <CardTitle className="text-sm">板块轮动分析</CardTitle>
          {data.最强板块 && data.最强板块 !== '无明显最强板块' && (
            <span className="text-[11px] text-muted-foreground ml-auto">
              最强: <span className="text-up font-medium">{data.最强板块}</span>
              {(data.最强板块涨停数 ?? 0) > 0 && (
                <span className="text-muted-foreground"> · {data.最强板块涨停数}只涨停</span>
              )}
            </span>
          )}
          {!hasAnyData && (
            <span className="text-[11px] text-muted-foreground ml-auto">非交易日</span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {!hasAnyData ? (
          <div className="text-center text-xs text-muted-foreground py-6">
            非交易日或板块数据获取中
          </div>
        ) : (
          <Tabs value={tab} onValueChange={setTab} className="w-full">
            <TabsList className="mb-3">
              <TabsTrigger value="industry">行业板块</TabsTrigger>
              <TabsTrigger value="concept">概念板块</TabsTrigger>
            </TabsList>
            <TabsContent value="industry">
              <CategoryPanel current={data.industry} />
            </TabsContent>
            <TabsContent value="concept">
              <CategoryPanel current={data.concept} />
            </TabsContent>
          </Tabs>
        )}

        {data.board_distribution && data.board_distribution.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border">
            <div className="flex items-center gap-1.5 mb-2 text-[11px] text-muted-foreground">
              <BarChart3 className="w-3 h-3" />
              行业涨停分布
            </div>
            <div className="flex flex-wrap gap-1.5">
              {data.board_distribution.slice(0, 5).map((b, i) => (
                <span key={i} className="px-2 py-0.5 rounded text-[10px] bg-muted text-muted-foreground">
                  {b.name} <span className="text-up font-medium">{b.涨停数}只</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

