# AStock AI Copilot V2 — 完整项目上下文

> 本文件包含项目的完整代码结构、架构决策、核心算法源码和配置。
> AI 工具可通过此文件理解项目全貌，无需 GitHub 搜索。
>
> 原始 URL: `https://raw.githubusercontent.com/gergchen/astock-market-engine/main/AI-CONTEXT.md`

---

## 一、项目概览

**名称**: AStock AI Copilot V2 — 市场认知引擎
**描述**: 真正理解 A 股市场行为逻辑的 AI 认知系统。不是自动交易机器人，而是帮你读懂市场的 AI 分析助手。
**版本**: 2.0.0
**许可证**: MIT

### 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Next.js 14 (App Router) + TypeScript + Tailwind CSS + Framer Motion |
| UI | shadcn/ui + lucide-react + lightweight-charts (K线) |
| 数据获取 | SWR (stale-while-revalidate) |
| 后端 | FastAPI + uvicorn (Python 3.10+) |
| 数据源 | akshare, Tencent/Sina HTTP API, EastMoney (curl_cffi) |
| AI | Claude API / OpenAI API (DeepSeek 兼容) — **可选，不配也能运行** |
| 向量存储 | Qdrant (local mode, 无外部服务依赖) |
| 数据库 | SQLAlchemy + SQLite (默认) / PostgreSQL (可选) |
| 容器 | Docker + docker-compose (dev/prod) |
| CI | GitHub Actions (ruff + pytest + next lint + next build) |

### 核心能力

- AI 个股分析（主力行为 + 技术面 + 资金面）
- 主力行为识别（吸筹/洗盘/主升/出货，规则评分）
- 情绪周期判断（冰点/修复/主升/高潮/分歧/退潮，多维加权）
- 龙头识别（连板高度/封板强度/板块影响力/封板时间/资金力度/换手率 6维评分）
- 板块轮动（行业+概念双维度，状态分类：加强/持续/退潮/反弹）
- 涨停/跌停原因分析（5种/6种类型多条件打分）
- 预期差分析（6种反常现象识别）
- 事件驱动引擎（新闻→概念映射→关联个股→热点追踪）
- 策略回测（MA交叉/放量突破/龙头跟随）
- RAG 增强复盘（检索相似历史交易日注入 LLM 提示）
- WebSocket 实时推送（行情/快照/热力图）
- **无需 API Key** — 降级到本地规则引擎 + mock 数据

---

## 二、完整目录结构

```
市场认知引擎/
├── CLAUDE.md                       # Claude Code 上下文
├── AI-CONTEXT.md                   # 本文件 — 给任何 AI 读取的完整上下文
├── README.md                       # 项目主页
├── .env.example                    # 环境变量模板
├── ruff.toml                       # Python linter 配置
├── start.bat / start.sh / start-all.ps1  # 启动脚本
│
├── backend/                        # FastAPI 后端
│   ├── main.py                     #   入口 (路由注册/CORS/限流/生命周期)
│   ├── config.py                   #   环境变量配置
│   ├── routers/
│   │   ├── stock.py                #   /api/stock/* — K线/行情/资金流/板块/龙虎榜
│   │   ├── analysis.py            #   /api/analysis/* — AI分析/本地规则/事件/RAG/回测
│   │   ├── auth.py                #   /api/auth/* — JWT注册/登录
│   │   └── ws.py                  #   /ws/* — WebSocket实时推送
│   ├── services/                   # 数据服务层 (多源回退+TTL缓存+数据质量标记)
│   │   ├── analysis/              #   AI分析管线
│   │   │   ├── llm_client.py      #   统一LLM客户端 (Claude/OpenAI/DeepSeek)
│   │   │   ├── prompt_builder.py  #   结构化提示构建
│   │   │   ├── stock_analysis.py  #   个股分析编排 (LLM→降级→本地规则)
│   │   │   ├── degraded.py        #   降级安全模板
│   │   │   └── local_rules.py     #   本地规则引擎 (纯Python无API)
│   │   ├── market_data.py         #   日K线/股票名称 (Sina→Tencent→EastMoney→akshare→mock)
│   │   ├── quote_data.py          #   实时行情/大盘指数
│   │   ├── limit_data.py          #   涨停跌停池/龙虎榜 (60s TTL)
│   │   ├── flow_data.py           #   个股/板块资金流
│   │   ├── financial_data.py      #   财报数据
│   │   ├── market_compute.py      #   衍生指标 (涨停数/炸板率/连板高度/封板强度)
│   │   ├── data_quality.py        #   数据质量标记 + 置信度评分
│   │   ├── db_service.py          #   SQLite/PostgreSQL 持久化
│   │   ├── feishu.py              #   飞书 Webhook
│   │   └── feishu_bot.py          #   飞书机器人
│   ├── agents/
│   │   ├── stock_analysis_agent.py   # 综合分析编排 (组合MainCapital+EmotionCycle)
│   │   ├── main_capital_agent.py     # 主力行为识别 (4阶段规则评分)
│   │   └── emotion_cycle_agent.py    # 情绪周期判断 (6阶段多维加权)
│   ├── feature_engine/            # V8 共享特征计算
│   │   ├── market_features.py     #   市场级快照 (一次性计算, 消除N+1)
│   │   └── stock_features.py      #   个股结构化特征
│   ├── score_engine/              # V8 结构化评分
│   │   ├── market_scores.py       #   情绪评分/龙头强度/风险评分 (0-100)
│   │   ├── stock_scores.py        #   主力评分/技术评分/综合评分 (0-100)
│   │   └── score_utils.py         #   评分工具函数
│   ├── event_engine/              # 事件驱动引擎
│   │   ├── event_types.py         #   数据类型定义
│   │   ├── news_fetcher.py        #   新闻获取
│   │   ├── event_extractor.py     #   事件提取/分类/情感判定
│   │   ├── concept_mapper.py      #   概念→板块→个股映射
│   │   ├── stock_linker.py        #   新闻→关联个股评分
│   │   ├── hot_tracker.py         #   热点追踪
│   │   └── timeline.py            #   事件时间线
│   ├── backtest/                  # 策略回测引擎
│   │   ├── engine.py              #   信号→模拟交易→绩效 (夏普/最大回撤/胜率)
│   │   └── strategies.py          #   内置策略 (MA交叉/放量突破/龙头跟随)
│   ├── database/                  # 数据持久化
│   │   ├── db.py                  #   SQLAlchemy引擎
│   │   └── models.py              #   ORM: MarketSnapshot/ReviewRecord/User
│   └── schemas/                   # Pydantic 模型
│
├── frontend/                      # Next.js 14 前端
│   ├── app/                       # App Router
│   │   ├── page.tsx               #   首页 (搜索/快速入口/功能卡片)
│   │   ├── stock/page.tsx         #   个股分析 (K线/AI分析/评分)
│   │   ├── market/page.tsx        #   大盘概况 (评分/龙头/板块轮动)
│   │   ├── review/page.tsx        #   AI复盘 (每日回顾/情绪周期/历史对比)
│   │   ├── workbench/page.tsx     #   实时工作台 (炸板热力图/板块统计)
│   │   └── backtest/page.tsx      #   策略回测
│   ├── components/                # UI组件
│   │   ├── ui/                    #   shadcn/ui 基础
│   │   ├── AppHeader.tsx
│   │   ├── KLineChart.tsx         #   K线图 (lightweight-charts)
│   │   ├── AnalysisView.tsx       #   AI分析渲染
│   │   ├── EmotionTimeline.tsx    #   情绪周期可视化
│   │   ├── DragonLeaderCard.tsx
│   │   ├── SectorRotationCard.tsx
│   │   ├── ZhabanHeatmap.tsx      #   炸板率热力图
│   │   ├── SystemStatusProvider.tsx
│   │   └── ErrorBoundary.tsx
│   └── lib/                       # 工具
│       ├── api.ts                 #   类型安全API客户端
│       ├── hooks.ts               #   SWR数据获取Hooks
│       └── types.ts               #   共享类型
│
├── emotion_cycle_engine/          # 情绪周期引擎 (init only, 逻辑在backend/agents/)
├── market_reasoning_engine/       # 市场推理引擎 — 预期差分析
│   └── agent.py                   #   ExpectationGapAgent (6种反常现象)
├── sector_rotation_engine/        # 板块轮动引擎
│   └── agent.py                   #   SectorRotationAgent (双维度+状态分类)
├── dragon_leader_engine/          # 龙头识别引擎
│   └── agent.py                   #   DragonLeaderAgent (6维评分)
├── review_engine/                 # 复盘引擎
│   ├── agent.py                   #   MarketReviewAgent (AI复盘+RAG增强)
│   └── sector_rotation.py         #   板块轮动工具
├── limit_up_analysis/             # 涨停分析引擎
│   └── agent.py                   #   LimitUpAgent (5种类型)
├── limit_down_analysis/           # 跌停分析引擎
│   └── agent.py                   #   LimitDownAgent (6种类型)
├── rag/                           # RAG 检索增强
│   └── retriever.py               #   ReviewEnhancer (相似行情检索+注入)
├── vector_db/                     # Qdrant 向量数据库
│   └── client.py                  #   Qdrant本地客户端 (2个集合)
├── tests/                         # 测试
│   ├── conftest.py                #   共享fixtures
│   ├── test_auth.py               #   认证测试 (密码哈希/JWT/端点)
│   ├── test_data_quality.py       #   数据质量测试
│   ├── test_degraded_and_local_rules.py  # 降级/本地规则测试
│   └── test_input_validation.py   #   输入验证测试
├── docker/                        # Docker部署
│   ├── docker-compose.yml         #   开发环境 (热重载)
│   ├── docker-compose.prod.yml    #   生产环境 (Nginx)
│   ├── Dockerfile.backend         #   多阶段构建 (python:3.11-slim)
│   ├── Dockerfile.frontend        #   多阶段构建 (node:20-alpine)
│   └── nginx.conf                 #   反向代理配置
└── .github/workflows/
    └── ci.yml                     #   CI: ruff + pytest + lint + build
```

---

## 三、核心算法源码

### 3.1 情绪周期判断 (EmotionCycleAgent)

**文件**: `backend/agents/emotion_cycle_agent.py`
**原理**: 6阶段 × 4维度 加权评分，取最高分阶段

```python
STAGES = [
    {"name": "冰点期", "ideal_up": (0, 10), "ideal_zhaban": (0.6, 1.0), "ideal_board": (0, 2), "ideal_ratio": (0, 0.5)},
    {"name": "修复期", "ideal_up": (10, 20), "ideal_zhaban": (0.4, 0.6), "ideal_board": (3, 4), "ideal_ratio": (0.5, 1.5)},
    {"name": "主升期", "ideal_up": (20, 50), "ideal_zhaban": (0.2, 0.35), "ideal_board": (5, 8), "ideal_ratio": (1.5, 5)},
    {"name": "高潮期", "ideal_up": (50, 999), "ideal_zhaban": (0, 0.2), "ideal_board": (8, 99), "ideal_ratio": (5, 999)},
    {"name": "分歧期", "ideal_up": (30, 50), "ideal_zhaban": (0.35, 0.5), "ideal_board": (5, 7), "ideal_ratio": (1, 3)},
    {"name": "退潮期", "ideal_up": (0, 20), "ideal_zhaban": (0.5, 1.0), "ideal_board": (0, 3), "ideal_ratio": (0, 1)},
]

# 权重: 涨停数45% + 炸板率25% + 连板高度20% + 涨跌停比10%
weights = {"up": 0.45, "zhaban": 0.25, "board": 0.2, "ratio": 0.1}

# 评分函数: 落入区间得1分，距离越远分越低（线性衰减）
def _range_score(value, ideal_range, min_denom=1.0):
    lo, hi = ideal_range
    if lo <= value <= hi:
        return 1.0
    if value < lo:
        return max(0.0, 1.0 - (lo - value) / max(lo, min_denom))
    return max(0.0, 1.0 - (value - hi) / max(hi, min_denom))

# 缺失值处理: 对应维度均分，不会被默认0拉偏到冰点期
```

**输出**: `{stage, description, score, signals, suggestion, all_scores}`

### 3.2 主力行为识别 (MainCapitalAgent)

**文件**: `backend/agents/main_capital_agent.py`
**原理**: 4阶段 × 5维度 规则评分

```python
# 吸筹 (满分5): 股价<MA60的90%(+1) + 量比<1.2(+1) + 换手率1%-3%(+1) + 收盘近最高(+1) + 下影线(+1)
# 洗盘 (满分5): 股价在MA60的80%-95%(+1) + 量比<0.6(+1) + 振幅<2%(+1) + 换手率<1.5%(+1)
# 主升 (满分5): 股价>MA60的105%(+1) + 量比≥1.5(+1) + 今日涨(+1) + 换手率>3%(+1) + 振幅<6%(+1)
# 出货 (满分5): 累计涨幅>30%且股价>MA60的130%(+1) + 放量滞涨(+1) + 换手率>5%(+1) + 跌幅<-3%(+1)

# 取最高分阶段
best_stage = max(scores, key=lambda k: scores[k]["score"])
confidence: ≥0.8→高, ≥0.5→中, else→低
```

### 3.3 概念龙头识别 (DragonLeaderAgent)

**文件**: `dragon_leader_engine/agent.py`
**原理**: 6维评分 (满分100)

```python
# 1. 连板高度 (30分): min(boards/10, 1.0) × 30
# 2. 封板强度 (15分): min(fengdan/成交额/5, 1.0) × 15
# 3. 板块影响力 (20分): min(所属行业涨停数/10, 1.0) × 20
# 4. 封板时间 (15分): 越早越高, 9:25=1.0, 10:00=0.8, 11:30=0.5, 15:00=0.0
# 5. 资金力度 (10分): min(主力净流入/10000, 1.0) × 10
# 6. 换手率健康度 (10分): ≤5%=10, ≤10%=7, ≤20%=4, >20%=1
```

**关键优化**: 批量查询实时行情以避免 N+1 问题。

### 3.4 板块轮动 (SectorRotationAgent)

**文件**: `sector_rotation_engine/agent.py`
**原理**: 行业+概念双维度，4状态分类

```python
状态分类规则:
  if change > 0 and flow > 0:   → "加强" (量价齐升)
  if change > 0 and flow <= 0:  → "持续" (惯性上涨)
  if change < 0 and flow < 0:   → "退潮" (量价齐跌)
  if change < 0 and flow >= 0:  → "反弹" (资金试盘)

最强板块 = max(涨停数×2 + 涨跌幅) 且涨停数≥3且资金流入>0
```

### 3.5 涨停原因分析 (LimitUpAgent)

**文件**: `limit_up_analysis/agent.py`
**原理**: 5类型 × 4维度 规则评分

```python
类型: 政策催化 | 资金驱动 | 情绪炒作 | 龙头带动 | 基本面驱动
每类满分4分，归一化0-1，取最高分
自信度: ≥0.75→高, ≥0.5→中, else→低
```

### 3.6 跌停原因分析 (LimitDownAgent)

**文件**: `limit_down_analysis/agent.py`
**原理**: 6类型 × 3-4维度 规则评分

```python
类型: 公司暴雷 | 主力出货 | 板块退潮 | 情绪崩塌 | 高位补跌 | 流动性危机
评分方法同上（归一化取最高分）
```

### 3.7 预期差分析 (ExpectationGapAgent)

**文件**: `market_reasoning_engine/agent.py`
**原理**: 6种反常现象 × 4维度 规则评分

```python
6种现象:
1. 利好不涨 — 有利好消息但股价不涨甚至跌
2. 业绩增长反而跌 — 净利润增长但股价下跌
3. 利空落地反而涨 — 利空消息但股价不跌反涨
4. 放量涨次日跌 — 前日放量拉高今日出货
5. 缩量上涨 — 主力锁仓/买盘不足
6. 高位放量滞涨 — 高位出货特征
```

### 3.8 结构化评分引擎 (V8 Score Engine)

**文件**: `backend/score_engine/market_scores.py`, `backend/score_engine/stock_scores.py`

市场评分（0-100）:
- **情绪评分**: 阶段匹配 → 基础分 ± 微调: 冰点=10, 修复=40, 主升=85, 高潮=70, 分歧=50, 退潮=20
- **龙头强度**: 最高板(40分) + 连板股数(30分) + 板块集中度(30分)
- **风险评分**: 基础30分, 高潮+40, 退潮+30, 分歧+20, 冰点-10, 炸板率>50%+15, 跌停>涨停+20

个股评分（0-100）:
- **主力评分**: 主升=90, 吸筹=70, 洗盘=50, 出货=15, 按匹配度微调
- **技术评分**: 趋势(40) + 量能(30) + 位置(30) + 资金流向修正(-8~+8)
- **综合评分**: 主力×60% + 技术×40%

---

## 四、API 接口文档

**基础URL**: `http://localhost:8005`

### 数据接口 (stock.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stock/daily?symbol=600519` | 日K线数据 |
| GET | `/api/stock/quote?symbol=600519` | 实时行情 |
| GET | `/api/stock/fundflow?symbol=600519` | 个股资金流 |
| GET | `/api/stock/market-overview` | 大盘概况 |
| GET | `/api/stock/limit-up-pool` | 涨停池 |
| GET | `/api/stock/limit-down-pool` | 跌停池 |
| GET | `/api/stock/sector-flow` | 板块资金流 |
| GET | `/api/stock/lhb-detail?date=20260101` | 龙虎榜详情 |
| GET | `/api/stock/health` | 系统健康状态 |

### 分析接口 (analysis.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/analysis/stock?symbol=600519` | AI综合分析 |
| GET | `/api/analysis/local-rules?symbol=600519` | 本地规则分析 |
| GET | `/api/analysis/limit-up-reason?symbol=600519` | 涨停原因 |
| GET | `/api/analysis/limit-down-reason?symbol=600519` | 跌停原因 |
| GET | `/api/analysis/expectation-gap?symbol=600519` | 预期差分析 |
| GET | `/api/analysis/dragon-leaders` | 龙头识别 |
| GET | `/api/analysis/sector-rotation` | 板块轮动 |
| GET | `/api/analysis/market-review` | 市场复盘 |
| GET | `/api/analysis/emotion-cycle` | 情绪周期 |
| GET | `/api/analysis/market-scores` | 市场评分 |
| GET | `/api/analysis/stock-scores?symbol=600519` | 个股评分 |

### 认证接口 (auth.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |

### WebSocket (ws.py)

| 路径 | 说明 |
|------|------|
| `/ws/market` | 市场快照推送 (每5秒) |
| `/ws/stock?symbol=600519` | 个股行情推送 (每3秒) |

---

## 五、数据流架构

```
外部数据源
  Tencent HTTP → Sina HTTP → curl_cffi(EastMoney) → akshare → Mock
       ↓              ↓              ↓                  ↓         ↓
  ┌──────────────────────────────────────────────────────────────┐
  │              Services 层 (多源回退 + TTL缓存)                │
  │  market_data / quote_data / limit_data / flow_data / ...     │
  │  每次请求标记 DataQuality 置信度 (SINA/TENCENT/AKSHARE/MOCK)  │
  └──────────────┬───────────────────────────────────────────────┘
                 ↓ 置信度 ≥ 0.6?
           ┌─────┴─────┐
           ↓ YES        ↓ NO (降级)
  ┌──────────────────┐  ┌──────────────────┐
  │ Feature Engine   │  │  Degraded Path   │
  │ MarketFeatures   │  │  安全模板消息     │
  │ StockFeatures    │  └──────────────────┘
  └──────┬───────────┘
         ↓ 共享特征
  ┌──────────────────┐
  │ Score Engine     │  ← 纯规则 0-100 评分
  │ market_scores    │
  │ stock_scores     │
  └──────┬───────────┘
         ↓ 结构化评分注入
  ┌──────────────────┐
  │ Agents           │  ← 业务逻辑编排
  │ EmotionCycle     │
  │ MainCapital      │
  │ DragonLeader     │
  │ ReviewEngine     │
  └──────┬───────────┘
         ↓
  ┌──────────────────┐
  │ RAG (Qdrant)     │  ← 向量检索增强
  │ SQLite / Pg      │  ← 结构化持久化
  └──────────────────┘
```

### 三层分析管线

```
① 真实数据 + LLM (配置了API Key)     → 完整AI综合分析
② 真实数据 + 本地规则 (无API Key)    → 纯规则引擎分析
③ Mock数据 + 降级模板 (数据源全挂)   → 安全降级提示
```

---

## 六、配置与环境变量

```ini
# AI提供商 (openai/claude)
AI_PROVIDER=openai

# Claude API
CLAUDE_API_KEY=
CLAUDE_API_BASE=https://api.anthropic.com
CLAUDE_MODEL=claude-sonnet-4-20250514

# OpenAI/DeepSeek 兼容接口
OPENAI_API_KEY=
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# 服务
HOST=0.0.0.0
PORT=8005
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# 前端
NEXT_PUBLIC_API_BASE_URL=http://localhost:8005

# 认证 (生产环境必须改)
JWT_SECRET=change-me-to-a-random-string-in-production

# 数据库
DATABASE_URL=sqlite:///./data/market_memory.db

# RAG
RAG_ENABLED=true
RAG_SIMILAR_DAYS_COUNT=5
RAG_QDRANT_PATH=./data/qdrant_storage
```

---

## 七、Docker 部署

### 开发环境 (热重载)
```yaml
docker-compose.yml:
  - backend:  构建→COPY所有引擎包→uvicorn --reload :8005
  - frontend: node:20-alpine→npm run dev :3000
  - volumes: 源码目录挂载实现热重载
```

### 生产环境
```yaml
docker-compose.prod.yml:
  - backend:  多阶段构建→uvicorn--workers 2 :8005
  - frontend: next build→npm start :3000
  - nginx:    alpine反向代理 80→frontend:3000, /api/→backend:8005
```

**注意**: Dockerfile.frontend 依赖 `next.config.js` 存在（生产构建需要），如果项目没有此文件或文件名不匹配会构建失败。

---

## 八、架构决策

### 1. V8 架构 (Feature Engine + Score Engine)
旧架构中每个 Agent 独立调用 services 层，导致 N+1 问题。V8 架构引入 Feature Engine 一次性计算所有 Shared Feature，Score Engine 输出结构化 0-100 评分，Agent 直接消费已计算好的数据。

### 2. 多源回退 + 数据质量追踪
每层数据源标记 DataQuality 置信度。置信度 < 0.6 时系统自动降级到安全模式，避免 LLM 基于不可信数据生成误导性分析。

### 3. Agent + Score Engine 分离
Agent 负责业务逻辑编排和最终输出（含 LLM 调用），Score Engine 负责纯规则数值计算（0-100 分，不依赖 LLM）。评分注入 LLM prompt 提高分析一致性。

### 4. RAG 增强复盘
每日市场状态转换为 6 维向量存入 Qdrant，复盘时检索 Top-K 相似历史交易日，将历史行情数据注入 LLM prompt，帮助 AI 做对比分析。

### 5. 零外部依赖运行
不配置任何 API Key 的情况下：数据源回退到 mock → 分析降级到本地规则引擎 → 复盘使用内置模板。系统完整可用，只是缺少 AI 深度分析能力。

---

## 九、需要注意的点

1. **前端构建**: `Dockerfile.frontend` 需要 `next.config.js` 存在。如果项目使用 `next.config.mjs` 或 `next.config.ts`，Dockerfile 中的 `COPY next.config.js` 会失败。
2. **情绪周期 Score Engine**: `compute_emotion_scores()` 中用 `zhaban <= 0 and mf.limit_up_count == 0` 判断炸板率缺失，这个逻辑在真实市场数据中可能误判（炸板率可能为0但市场有成交，如极端一致行情）。
3. **RAG 依赖 OpenAI**: 向量化使用 `text-embedding-3-small`，如果不可用会用 hash fallback。确保 `OPENAI_API_KEY` 配置了有效的 embedding 权限。
4. **数据源风险**: akshare 是免费接口，交易时段可能被限流或返回空数据。系统有多层回退但极端行情下所有源都可能超时。
5. **WebSocket 端口**: 后端默认 8005 端口，前端 API 客户端自动解析 `NEXT_PUBLIC_API_BASE_URL`，未设置时 fallback 到 `localhost:8005`。

---

*本文件由 AI 根据项目源码自动生成，内容与 `main` 分支 HEAD 一致。
如有任何 AI 工具需要理解此项目，直接提供本文件内容即可。*
