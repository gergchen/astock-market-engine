"""数据服务层 — 使用 akshare 获取 A 股数据

所有数据获取逻辑集中在此，上层不直接调用 akshare。
为减少对 akshare 的重复请求，对盘面级数据（涨停池/全市场行情快照/板块资金流向）
增加内存 TTL 缓存。个股级数据不缓存。

模块结构:
    _cache.py       — TTL 缓存 + mock 状态追踪
    _helpers.py     — akshare 安全调用封装 + mock 数据生成
    market_data.py  — 个股日K 行情 + 股票名称
    quote_data.py   — 实时行情快照 + 大盘概况
    limit_data.py   — 涨停池 / 跌停池 / 龙虎榜
    flow_data.py    — 个股资金流向 + 板块资金流向
    financial_data.py — 财报数据
    market_compute.py — 盘面计算指标（炸板率/连板高度）
"""

# 基础设施（被其它模块内部使用，同时也对外暴露）
from ._cache import _cache_get, _cache_set, mark_mock_used, pop_mock_used
from ._helpers import _generate_mock_data, _try_akshare

# 数据质量层
from .data_quality import (
    DataQuality,
    DataSource,
    classify_system_status,
    get_system_quality,
    pop_system_quality,
    quality_dict,
    set_system_quality,
    tag_kline_df,
)

# 财报
from .financial_data import get_stock_financial

# 资金流向
from .flow_data import (
    get_sector_fund_flow,
    get_sector_fund_flow_by_type,
    get_stock_fund_flow,
)

# 涨跌停 + 龙虎榜
from .limit_data import get_lhb_detail, get_limit_down_pool, get_limit_up_pool

# 盘面计算
from .market_compute import get_all_limit_up_today, get_top_boards, get_zhaban_rate

# 个股数据
from .market_data import _fetch_stock_daily_curl, get_stock_daily, get_stock_name

# 实时行情
from .quote_data import (
    _get_spot_em_df,
    _row_to_quote,
    get_market_overview,
    get_realtime_quote,
    get_realtime_quote_map,
)
