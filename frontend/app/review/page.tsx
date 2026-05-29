'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { BarChart3, Loader2, FileText, TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import AppHeader from '@/components/AppHeader'
import DragonLeaderCard from '@/components/DragonLeaderCard'
import SectorRotationCard from '@/components/SectorRotationCard'
import HistoricalComparison from '@/components/HistoricalComparison'
import AIReviewCard from '@/components/AIReviewCard'
import SystemStatusBar from '@/components/SystemStatusBar'
import MockWarningBanner from '@/components/MockWarningBanner'
import { ErrorState, EmptyState } from '@/components/ui/states'
import {
  useMarketReview, useMarketOverview, useDragonLeaders,
  useSectorRotation, useSimilarToday, useMarketScores,
} from '@/lib/hooks'
import { useSystemStatus } from '@/components/SystemStatusProvider'
import { emotionColor, riskColor } from '@/lib/types'

export default function ReviewPage() {
  const router = useRouter()
  const [scrolled, setScrolled] = useState(false)
  const { isMock } = useSystemStatus()

  const { data: marketReview, error: mrErr } = useMarketReview()
  const { data: overview } = useMarketOverview()
  const { data: dragonLeaders } = useDragonLeaders()
  const { data: sectorRotation } = useSectorRotation()
  const { data: similarData } = useSimilarToday()
  const { data: marketScores } = useMarketScores()

  const similarDays = similarData?.similar_days ?? null
  const loading = !marketReview && !mrErr

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const getEmotionStyle = (stage: string) => {
    const map: Record<string, { color: string; bg: string }> = {
      '冰点期': { color: 'text-blue-400', bg: 'bg-muted' },
      '修复期': { color: 'text-emerald-500', bg: 'bg-muted' },
      '主升期': { color: 'text-orange-400', bg: 'bg-muted' },
      '高潮期': { color: 'text-red-400', bg: 'bg-muted' },
      '分歧期': { color: 'text-yellow-400', bg: 'bg-muted' },
      '退潮期': { color: 'text-purple-400', bg: 'bg-muted' },
    }
    return map[stage] || { color: 'text-muted-foreground', bg: 'bg-muted' }
  }

  const renderMarkdown = (text: string) => {
    const html = text
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/\n\n/g, '</p><p>')
    return { __html: `<p>${html}</p>` }
  }

  const emotion = marketReview?.emotion
  const limitUpCount = marketReview?.limit_up_count ?? 0
  const limitDownCount = marketReview?.limit_down_count ?? 0
  const zhabanRate = marketReview?.zhaban_rate

  return (
    <div className="min-h-screen">
      <AppHeader
        title="市场复盘"
        variant="fixed"
        scrolled={scrolled}
        statusBar={<SystemStatusBar />}
        navItems={[
          { href: '/', label: '首页' },
          { href: '/market', label: '大盘' },
          { href: '/workbench', label: '工作台' },
        ]}
      />

      <main className="max-w-4xl mx-auto px-4 pt-16 pb-8">
        {loading ? (
          <div className="flex justify-center py-24">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        ) : mrErr && !marketReview ? (
          <ErrorState message={`复盘数据加载失败: ${mrErr?.message}`} />
        ) : !marketReview ? (
          <EmptyState type="no_data" message="暂无复盘数据（非交易日或数据获取中）" />
        ) : (
          <div className="space-y-4">
            {isMock && <MockWarningBanner />}

            {/* 市场概况指标 */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Card className="border-border rounded">
                <CardContent className="p-4">
                  <div className="text-[11px] text-muted-foreground mb-1">涨停</div>
                  <div className="text-2xl font-bold font-mono text-up">{limitUpCount}</div>
                </CardContent>
              </Card>
              <Card className="border-border rounded">
                <CardContent className="p-4">
                  <div className="text-[11px] text-muted-foreground mb-1">跌停</div>
                  <div className="text-2xl font-bold font-mono text-down">{limitDownCount}</div>
                </CardContent>
              </Card>
              <Card className="border-border rounded">
                <CardContent className="p-4">
                  <div className="text-[11px] text-muted-foreground mb-1">炸板率</div>
                  <div className="text-2xl font-bold font-mono">{zhabanRate != null ? (zhabanRate * 100).toFixed(1) + '%' : '--'}</div>
                </CardContent>
              </Card>
              <Card className="border-border rounded">
                <CardContent className="p-4">
                  <div className="text-[11px] text-muted-foreground mb-1">情绪阶段</div>
                  <div className="text-lg font-bold" style={{ color: emotionColor(emotion?.stage || '') }}>
                    {emotion?.stage || '--'}
                  </div>
                  {emotion?.confidence && (
                    <div className="text-[10px] text-muted-foreground">置信度: {emotion.confidence}</div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* 情绪详情 */}
            {emotion && (
              <Card className="border-border rounded">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-muted-foreground" />
                    <CardTitle className="text-sm">情绪周期判断</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 mb-3">
                    <div className="text-2xl font-bold" style={{ color: emotionColor(emotion.stage) }}>
                      {emotion.stage}
                    </div>
                    <Badge className="text-[10px]" style={{
                      background: emotionColor(emotion.stage) + '18',
                      color: emotionColor(emotion.stage),
                      border: 'none',
                    }}>置信度 {emotion.confidence}</Badge>
                  </div>
                  {emotion.signals?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {emotion.signals.map((s: string, i: number) => (
                        <Badge key={i} variant="outline" className="text-[10px]">{s}</Badge>
                      ))}
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground leading-relaxed">
                    {emotion.suggestion}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 市场评分 */}
            {marketScores && (
              <Card className="border-border rounded">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-muted-foreground" />
                    <CardTitle className="text-sm">市场分析</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded bg-muted">
                      <div className="text-xs text-muted-foreground mb-1">情绪</div>
                      <div className="text-xl font-bold font-mono" style={{ color: emotionColor(marketScores.emotion.stage) }}>
                        {marketScores.emotion.score}
                      </div>
                      <Badge style={{
                        background: emotionColor(marketScores.emotion.stage) + '22',
                        color: emotionColor(marketScores.emotion.stage),
                        border: 'none'
                      }} className="text-[10px]">{marketScores.emotion.stage}</Badge>
                    </div>
                    <div className="p-3 rounded bg-muted">
                      <div className="text-xs text-muted-foreground mb-1">龙头</div>
                      <div className="text-xl font-bold font-mono">
                        {marketScores.dragon_intensity.score}
                      </div>
                      <div className="text-[10px] text-muted-foreground">{marketScores.dragon_intensity.high_board_count} 只高标</div>
                    </div>
                    <div className="p-3 rounded bg-muted">
                      <div className="text-xs text-muted-foreground mb-1">活跃度</div>
                      <div className="text-xl font-bold font-mono">
                        {marketScores.dragon_intensity.score}
                      </div>
                      <Badge variant="outline" className="text-[10px]">活跃度</Badge>
                    </div>
                    <div className="p-3 rounded bg-muted">
                      <div className="text-xs text-muted-foreground mb-1">风险</div>
                      <div className="text-xl font-bold font-mono" style={{ color: riskColor(marketScores.risk.level) }}>
                        {marketScores.risk.score}
                      </div>
                      <Badge style={{
                        background: riskColor(marketScores.risk.level) + '22',
                        color: riskColor(marketScores.risk.level),
                        border: 'none'
                      }} className="text-[10px]">{marketScores.risk.level}风险</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* AI 复盘分析 */}
            {marketReview.ai_review && (
              <AIReviewCard
                text={marketReview.ai_review}
                extraMetrics={[
                  { label: '涨停', value: limitUpCount },
                  { label: '跌停', value: limitDownCount },
                  { label: '炸板率', value: zhabanRate != null ? (zhabanRate * 100).toFixed(1) + '%' : '--' },
                ]}
              />
            )}

            {/* 龙头股 */}
            {dragonLeaders && <DragonLeaderCard data={dragonLeaders} />}

            {/* 板块轮动 */}
            <SectorRotationCard data={sectorRotation} />

            {/* 历史相似日 */}
            {similarDays && similarDays.length > 0 && (
              <HistoricalComparison similarDays={similarDays} loading={false} />
            )}

            {/* 底部提示 */}
            <div className="text-center text-[11px] text-muted-foreground pb-4 pt-2">
              {isMock
                ? '* 当前为模拟数据模式，分析仅供参考'
                : '* 数据基于 akshare 实时数据，仅供参考，不构成投资建议'}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

