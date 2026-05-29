"""概念映射 — 概念/政策 → 板块 → 个股

提供双向查询：概念找个股，个股找概念。
数据基于 akshare 概念板块 + 行业分类 + 常见映射。
"""
from backend.services.flow_data import get_sector_fund_flow_by_type

# ── 核心概念 → 典型关联个股 ──
_CONCEPT_STOCKS: dict[str, list[str]] = {
    "AI": ["300033", "300418", "002230", "603019", "688111", "300624"],
    "芯片": ["688981", "002049", "603986", "688396", "600703"],
    "新能源": ["300750", "002594", "601012", "300274", "688599"],
    "汽车": ["002594", "000625", "601238", "600104", "300750"],
    "医药": ["600276", "300760", "300122", "000661", "688180"],
    "消费": ["600519", "000858", "000333", "002714", "600887"],
    "金融": ["600036", "601318", "300059", "600030", "000001"],
    "地产": ["000002", "001979", "600048", "600383", "002146"],
    "军工": ["600760", "000768", "002013", "600893", "300775"],
    "数字经济": ["300059", "002415", "688111", "600536", "300033"],
    "机器人": ["300024", "002747", "688017", "300124", "603728"],
    "低空经济": ["002085", "300632", "688326", "002253", "300900"],
}

# ── 概念 → 板块名称映射 ──
_CONCEPT_SECTORS: dict[str, list[str]] = {
    "AI": ["人工智能", "ChatGPT概念", "AIGC概念", "算力概念"],
    "芯片": ["半导体", "国产芯片", "光刻机(胶)", "Chiplet概念"],
    "新能源": ["光伏设备", "风电设备", "储能", "锂电池", "钠离子电池"],
    "汽车": ["汽车整车", "汽车零部件", "新能源车", "无人驾驶"],
    "医药": ["化学制药", "生物制品", "医疗器械", "中药"],
    "消费": ["酿酒行业", "食品饮料", "家电行业", "商业百货"],
    "金融": ["银行", "证券", "保险", "多元金融"],
    "地产": ["房地产开发", "房地产服务", "装修建材"],
    "军工": ["航天航空", "船舶制造", "军工"],
    "数字经济": ["数据要素", "信创", "东数西算", "云计算"],
    "机器人": ["机器人概念", "工业母机", "机器视觉"],
    "低空经济": ["低空经济", "飞行汽车", "通用航空"],
}


def concept_to_sectors(concept: str) -> list[str]:
    """概念 → 关联板块名称列表"""
    return _CONCEPT_SECTORS.get(concept, [concept])


def concept_to_stocks(concept: str) -> list[str]:
    """概念 → 核心关联股票代码列表"""
    return _CONCEPT_STOCKS.get(concept, [])


def sector_to_concepts(sector_name: str) -> list[str]:
    """板块名 → 反查关联概念"""
    found = []
    for concept, sectors in _CONCEPT_SECTORS.items():
        for s in sectors:
            if sector_name in s or s in sector_name:
                found.append(concept)
                break
    return list(set(found))


def keyword_to_stocks(keyword: str) -> list[str]:
    """任意关键词 → 可能影响的个股"""
    stocks: set[str] = set()

    # 1. 直接概念匹配
    for concept, stock_list in _CONCEPT_STOCKS.items():
        if concept in keyword or any(k in keyword for k in _CONCEPT_SECTORS.get(concept, [])):
            stocks.update(stock_list[:3])

    # 2. 板块名匹配
    for concept, sectors in _CONCEPT_SECTORS.items():
        for sector in sectors:
            if sector in keyword or keyword in sector:
                stocks.update(_CONCEPT_STOCKS.get(concept, [])[:3])
                break

    return list(stocks)[:10]


def get_hot_sectors_from_flow() -> list[dict]:
    """从实时板块资金流向获取当前热门板块"""
    try:
        df = get_sector_fund_flow_by_type("概念资金流向")
        if df is None or df.empty:
            return []
        results = []
        for _, row in df.head(5).iterrows():
            name = str(row.get("名称", ""))
            change = float(row.get("今日涨跌幅", 0)) if row.get("今日涨跌幅") else 0
            flow = float(row.get("主力净流入-净额", 0)) if row.get("主力净流入-净额") else 0
            concepts = sector_to_concepts(name)
            results.append({
                "sector": name,
                "change_pct": round(change, 2),
                "flow_yi": round(flow / 1e8, 2),
                "concepts": concepts,
            })
        return results
    except Exception:
        return []
