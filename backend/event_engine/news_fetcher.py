"""新闻获取 — akshare 财经新闻 + TTL 缓存"""
import hashlib
import logging
from datetime import datetime

import pandas as pd

from backend.services._cache import _cache_get, _cache_set
from backend.services._helpers import _try_akshare

from .event_types import NewsItem

logger = logging.getLogger("market_engine.event")

_NEWS_TTL = 120  # 新闻缓存 2 分钟


def _hash_title(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()[:12]


def _parse_news_df(df: pd.DataFrame) -> list[NewsItem]:
    """DataFrame → NewsItem 列表"""
    items = []
    for _, row in df.iterrows():
        try:
            title = str(row.iloc[0]) if len(row) > 0 else ""
            if not title or title == "nan":
                continue
            content = str(row.iloc[1]) if len(row) > 1 else ""
            source = str(row.iloc[2]) if len(row) > 2 else ""
            pub_time = str(row.iloc[3]) if len(row) > 3 else ""
            url = str(row.iloc[4]) if len(row) > 4 else ""
            items.append(NewsItem(
                title=title.strip(),
                content=content.strip() if content != "nan" else "",
                source=source.strip() if source != "nan" else "",
                publish_time=pub_time.strip() if pub_time != "nan" else "",
                url=url.strip() if url != "nan" else "",
            ))
        except Exception:
            continue
    return items


def fetch_finance_news(limit: int = 50) -> list[NewsItem]:
    """获取财联社等来源的 A 股快讯"""
    cache_key = "finance_news"
    cached = _cache_get(cache_key)
    if cached is not None:
        # 只返回前 limit 条
        return cached[:limit] if isinstance(cached, list) else cached

    items: list[NewsItem] = []

    # 来源1: 财联社电报
    try:
        import akshare as ak
        df = _try_akshare(ak.stock_info_global_em, None)
        if df is not None and not df.empty:
            items = _parse_news_df(df)
    except Exception as e:
        logger.warning("stock_info_global_em failed: %s", e)

    # 来源2: 个股新闻聚合（空参数获取全市场）
    if not items:
        try:
            import akshare as ak
            df = _try_akshare(ak.stock_news_em, None)
            if df is not None and not df.empty:
                items = _parse_news_df(df)
        except Exception as e:
            logger.warning("stock_news_em failed: %s", e)

    _cache_set(cache_key, items, ttl=_NEWS_TTL)
    return items[:limit]


def fetch_sector_news(sector_name: str, limit: int = 20) -> list[NewsItem]:
    """获取特定板块相关新闻（基于全量新闻关键词过滤）"""
    all_news = fetch_finance_news(limit=100)
    matched = []
    for n in all_news:
        text = n.title + n.content
        if sector_name in text:
            matched.append(n)
        if len(matched) >= limit:
            break
    return matched


def fetch_today_events() -> list[NewsItem]:
    """获取今日事件（用于时间线构建）"""
    today = datetime.now().strftime("%Y-%m-%d")
    all_news = fetch_finance_news(limit=100)
    today_news = [n for n in all_news if today in n.publish_time or not n.publish_time]
    return today_news
