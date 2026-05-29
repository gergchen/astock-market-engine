"""事件提取 — 关键词识别 + 事件分类 + 摘要"""

import hashlib
import re

from .event_types import Event, NewsItem

# ── 政策关键词 ──
_POLICY_KEYWORDS = [
    "国务院", "发改委", "央行", "证监会", "银保监", "财政部", "工信部",
    "政策", "法规", "监管", "审批", "核准", "试点", "规划", "方案",
    "减税", "补贴", "降准", "降息", "加息", "LPR", "MLF", "逆回购",
    "注册制", "科创板", "北交所", "新三板",
]

# ── 财报关键词 ──
_EARNINGS_KEYWORDS = [
    "业绩", "营收", "净利润", "利润", "亏损", "盈利", "预告", "快报",
    "年报", "季报", "中报", "分红", "回购", "增持", "减持", "质押",
]

# ── 行业/概念关键词 → 板块映射 ──
_CONCEPT_SECTOR_MAP = {
    "AI": ["人工智能", "AI", "大模型", "ChatGPT", "智能"],
    "芯片": ["芯片", "半导体", "光刻", "EDA", "封装"],
    "新能源": ["光伏", "风电", "储能", "新能源", "锂电", "钠电"],
    "汽车": ["汽车", "新能源车", "自动驾驶", "智能驾驶", "整车"],
    "医药": ["医药", "创新药", "CXO", "医疗器械", "疫苗"],
    "消费": ["白酒", "食品", "饮料", "家电", "消费"],
    "金融": ["银行", "券商", "保险", "信托"],
    "地产": ["房地产", "地产", "物业", "基建"],
    "军工": ["军工", "国防", "航天", "卫星"],
    "数字经济": ["数据", "算力", "数字", "信创", "东数西算"],
    "机器人": ["机器人", "人形", "自动化"],
    "低空经济": ["低空", "无人机", "飞行汽车", "eVTOL"],
}

# ── 情绪词 ──
_POSITIVE_WORDS = ["利好", "超预期", "增长", "突破", "获批", "中标", "签约", "翻倍"]
_NEGATIVE_WORDS = ["利空", "下降", "亏损", "处罚", "调查", "暴雷", "减持", "跌停"]


def _segment_chinese(text: str) -> list[str]:
    """简单中文分词（无 jieba 依赖）

    使用标点符号切分 + 常见2-4字词提取。
    安装 jieba 后自动升级为 jieba 分词。
    """
    # 按标点切分
    segments = re.split(r'[，。、；：！？\s,.;:!?\[\]()（）""'r'【】《》\-\|/]+', text)
    words = []
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        # 提取 2-4 字词组
        for i in range(len(seg) - 1):
            for wlen in (2, 3, 4):
                if i + wlen <= len(seg):
                    w = seg[i:i + wlen]
                    # 过滤纯数字/符号
                    if not re.match(r'^[\d\.\-\+%]+$', w):
                        words.append(w)
    return words


def extract_keywords(text: str, max_kw: int = 8) -> list[str]:
    """从文本中提取关键词"""
    found: set[str] = set()
    text_lower = text.lower()

    # 1. 匹配政策关键词
    for kw in _POLICY_KEYWORDS:
        if kw in text:
            found.add(kw)

    # 2. 匹配财报关键词
    for kw in _EARNINGS_KEYWORDS:
        if kw in text:
            found.add(kw)

    # 3. 匹配概念关键词
    for concept_name, aliases in _CONCEPT_SECTOR_MAP.items():
        for alias in aliases:
            if alias in text:
                found.add(concept_name)
                break

    # 4. 分词补充
    words = _segment_chinese(text)
    for w in words[:20]:
        if len(w) >= 2 and w not in found:
            found.add(w)

    # 返回前 max_kw 个
    return list(found)[:max_kw]


def classify_event(text: str) -> str:
    """事件分类"""
    for kw in _POLICY_KEYWORDS[:8]:  # only core policy words
        if kw in text:
            return "政策"
    for kw in _EARNINGS_KEYWORDS[:4]:
        if kw in text:
            return "财报"
    for concept_name, aliases in _CONCEPT_SECTOR_MAP.items():
        for alias in aliases:
            if alias in text:
                return "行业"
    return "市场"


def get_affected_sectors(text: str) -> list[str]:
    """识别受影响的板块"""
    sectors = []
    for concept_name, aliases in _CONCEPT_SECTOR_MAP.items():
        for alias in aliases:
            if alias in text:
                sectors.append(concept_name)
                break
    return list(set(sectors))[:5]


def compute_sentiment(text: str) -> str:
    """简单情绪判断"""
    pos = sum(1 for w in _POSITIVE_WORDS if w in text)
    neg = sum(1 for w in _NEGATIVE_WORDS if w in text)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


def extract_event(news: NewsItem) -> Event:
    """从单条新闻提取结构化事件"""
    full_text = news.title + " " + news.content
    keywords = extract_keywords(full_text)
    event_type = classify_event(full_text)
    sectors = get_affected_sectors(full_text)
    sentiment = compute_sentiment(full_text)

    # 影响评分：政策类型最高，关联板块越多越高
    base = {"政策": 0.7, "财报": 0.5, "行业": 0.6, "市场": 0.3}
    impact = base.get(event_type, 0.3)
    impact += min(len(sectors) * 0.05, 0.2)
    if sentiment == "positive":
        impact += 0.05
    impact = min(1.0, impact)

    return Event(
        id=hashlib.md5(news.title.encode()).hexdigest()[:12],
        title=news.title,
        summary=news.content[:200] if news.content else news.title,
        event_type=event_type,
        keywords=keywords,
        affected_sectors=sectors,
        affected_stocks=[],  # 由 stock_linker 填充
        sentiment=sentiment,
        impact_score=round(impact, 2),
        publish_time=news.publish_time,
    )
