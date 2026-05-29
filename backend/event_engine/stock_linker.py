"""个股联动 — 事件 → 受影响个股评分"""
import hashlib

from .concept_mapper import concept_to_stocks, keyword_to_stocks
from .event_extractor import extract_keywords, get_affected_sectors
from .event_types import Event, NewsItem

_LINK_CACHE: dict[str, list[str]] = {}


def link_news_to_stocks(news: NewsItem) -> list[str]:
    """单条新闻 → 可能受影响的股票列表"""
    cache_key = hashlib.md5(news.title.encode()).hexdigest()[:12]
    if cache_key in _LINK_CACHE:
        return _LINK_CACHE[cache_key]

    full_text = news.title + " " + news.content
    keywords = extract_keywords(full_text)
    sectors = get_affected_sectors(full_text)

    stocks: set = set()

    # 1. 概念关键字 → 个股
    for kw in keywords:
        linked = keyword_to_stocks(kw)
        stocks.update(linked)

    # 2. 板块 → 个股
    for sector in sectors:
        linked = concept_to_stocks(sector)
        stocks.update(linked)

    result = list(stocks)[:15]
    _LINK_CACHE[cache_key] = result
    return result


def enrich_event(event: Event, news: NewsItem) -> Event:
    """补全事件中的 affected_stocks"""
    stocks = link_news_to_stocks(news)
    event.affected_stocks = stocks
    return event


def batch_link(news_list: list[NewsItem]) -> list[Event]:
    """批量新闻 → 事件（含个股联动）"""
    from .event_extractor import extract_event

    events = []
    for news in news_list:
        event = extract_event(news)
        event = enrich_event(event, news)
        events.append(event)
    return events


def get_today_linked_stocks() -> dict[str, list[str]]:
    """获取今日事件关联的个股映射（个股 → 关联事件标题）"""
    from .news_fetcher import fetch_today_events
    news_list = fetch_today_events()
    stock_events: dict[str, list[str]] = {}

    for news in news_list:
        stocks = link_news_to_stocks(news)
        for s in stocks:
            if s not in stock_events:
                stock_events[s] = []
            stock_events[s].append(news.title[:60])

    return stock_events
