"""热词追踪 — 统计词频趋势 + 热门话题发现"""
from collections import Counter, defaultdict
from datetime import datetime

from .concept_mapper import concept_to_stocks
from .event_extractor import extract_keywords, get_affected_sectors
from .event_types import HotTopic, NewsItem
from .news_fetcher import fetch_finance_news

# 窗口内热词计数
_HISTORY: dict[str, Counter] = defaultdict(Counter)  # date → Counter[word]
_MAX_HISTORY = 7  # 保留 7 天


def _cleanup_history():
    """删除过期历史"""
    dates = sorted(_HISTORY.keys())
    while len(dates) > _MAX_HISTORY:
        del _HISTORY[dates[0]]
        dates = dates[1:]


def _record_keywords(news_list: list[NewsItem]):
    """记录当日词频"""
    today = datetime.now().strftime("%Y-%m-%d")
    counter = _HISTORY[today]
    for news in news_list:
        full_text = news.title + " " + news.content
        kws = extract_keywords(full_text)
        for kw in kws:
            counter[kw] += 1
    _cleanup_history()


def get_trending_topics(top_k: int = 15) -> list[HotTopic]:
    """获取当前热门话题（今日词频 Top + 趋势判断）"""
    news_list = fetch_finance_news(limit=80)
    _record_keywords(news_list)

    today = datetime.now().strftime("%Y-%m-%d")
    today_counter = _HISTORY[today]
    if not today_counter:
        return []

    # 计算昨日词频（用于趋势判断）
    dates = sorted(_HISTORY.keys())
    yesterday_counter: Counter = Counter()
    if len(dates) >= 2:
        yesterday_counter = _HISTORY[dates[-2]]

    topics = []
    for word, count in today_counter.most_common(top_k * 2):
        if len(word) < 2:
            continue
        # 趋势判断
        yesterday_count = yesterday_counter.get(word, 0)
        if count > yesterday_count * 1.3:
            trend = "rising"
        elif count < yesterday_count * 0.7 and yesterday_count > 0:
            trend = "falling"
        else:
            trend = "stable"

        sectors = get_affected_sectors(word)
        stocks = concept_to_stocks(word) if word in sectors else []

        topics.append(HotTopic(
            keyword=word,
            count=count,
            trend=trend,
            related_sectors=sectors,
            related_stocks=stocks,
            first_seen=dates[0] if dates else today,
            last_seen=today,
        ))

        if len(topics) >= top_k:
            break

    return topics


def get_word_trend(word: str) -> dict:
    """获取单个词的趋势数据"""
    trend_data = {}
    for date in sorted(_HISTORY.keys()):
        trend_data[date] = _HISTORY[date].get(word, 0)
    return {
        "word": word,
        "trend": trend_data,
        "total": sum(trend_data.values()),
    }
