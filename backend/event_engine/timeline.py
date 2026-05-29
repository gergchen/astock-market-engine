"""事件时间线 — 按时间排列的事件流 + 查询"""
from .event_extractor import classify_event
from .event_types import TimelineEntry
from .news_fetcher import fetch_today_events
from .stock_linker import link_news_to_stocks


def build_today_timeline() -> list[TimelineEntry]:
    """构建今日事件时间线"""
    news_list = fetch_today_events()
    if not news_list:
        return []

    entries = []
    for news in news_list:
        event_type = classify_event(news.title)
        affected = link_news_to_stocks(news)

        # 重要性：政策 > 行业 > 财报 > 市场
        importance_map = {"政策": "high", "行业": "medium", "财报": "medium", "市场": "low"}

        entries.append(TimelineEntry(
            time=news.publish_time or "",
            title=news.title,
            event_type=event_type,
            affected_markets=affected[:5],
            importance=importance_map.get(event_type, "low"),
        ))

    # 按时间排序（有时间的在前，无时间的在后）
    entries.sort(key=lambda e: (e.time == "", e.time))
    return entries


def query_timeline(
    keyword: str | None = None,
    event_type: str | None = None,
    min_importance: str = "low",
) -> list[TimelineEntry]:
    """查询时间线（可过滤）"""
    entries = build_today_timeline()
    importance_order = {"high": 3, "medium": 2, "low": 1}

    result = []
    for e in entries:
        if min_importance and importance_order.get(e.importance, 1) < importance_order.get(min_importance, 1):
            continue
        if event_type and e.event_type != event_type:
            continue
        if keyword and keyword not in e.title:
            continue
        result.append(e)

    return result


def get_events_by_sector(sector: str) -> list[TimelineEntry]:
    """获取与特定板块相关的事件"""
    entries = build_today_timeline()
    return [e for e in entries if sector in e.title or any(sector in m for m in e.affected_markets)]


def get_market_drivers() -> list[dict]:
    """返回今日市场驱动因素（解释"为什么今天爆"）

    聚合政策+行业事件，按重要性排序。
    """
    entries = build_today_timeline()
    drivers: list[dict] = []

    for e in entries:
        if e.importance in ("high", "medium"):
            drivers.append({
                "time": e.time,
                "event": e.title,
                "type": e.event_type,
                "importance": e.importance,
                "affected": e.affected_markets[:3],
            })

    return sorted(drivers, key=lambda d: {"high": 0, "medium": 1, "low": 2}[d["importance"]])
