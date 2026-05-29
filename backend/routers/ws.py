"""WebSocket 实时数据推送

客户端连接后可订阅:
  - market: 大盘指数 + 涨跌停数 + 炸板率 (5s 推送)
  - stock/{symbol}: 个股实时行情 (3s 推送)
"""
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["WebSocket"])

# 频道订阅管理
_subscribers: dict[str, set[WebSocket]] = {
    "market": set(),
}


def _subscribe(channel: str, ws: WebSocket):
    if channel not in _subscribers:
        _subscribers[channel] = set()
    _subscribers[channel].add(ws)


def _unsubscribe(channel: str, ws: WebSocket):
    if channel in _subscribers:
        _subscribers[channel].discard(ws)


async def _broadcast(channel: str, data: dict):
    """向频道的所有订阅者广播数据"""
    dead: list[WebSocket] = []
    for ws in _subscribers.get(channel, set()):
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _subscribers.get(channel, set()).discard(ws)


async def _market_pusher():
    """每 5s 推送大盘数据"""
    from backend.services import (
        get_all_limit_up_today,
        get_market_overview,
        get_top_boards,
        get_zhaban_rate,
    )
    while True:
        try:
            overview = get_market_overview()
            up_count = get_all_limit_up_today()
            zhaban = get_zhaban_rate()
            top = get_top_boards(3)

            await _broadcast("market", {
                "type": "market_snapshot",
                "index": {
                    "name": overview.get("指数", "上证") if overview else "上证",
                    "price": overview.get("最新价", 0) if overview else 0,
                    "change_pct": overview.get("涨跌幅", 0) if overview else 0,
                },
                "limit_up": up_count,
                "zhaban_rate": round(zhaban, 3),
                "top_boards": [
                    {"name": t.get("name", ""), "board": t.get("boards", 0)}
                    for t in (top or [])
                ],
            })
        except Exception:
            pass
        await asyncio.sleep(5)


@router.websocket("/market")
async def market_ws(ws: WebSocket):
    """大盘实时推送"""
    await ws.accept()
    _subscribe("market", ws)
    try:
        while True:
            # 保活：等待客户端消息（客户端可发 ping）
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=30)
                if data == "ping":
                    await ws.send_text("pong")
            except asyncio.TimeoutError:
                await ws.send_text("pong")
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        _unsubscribe("market", ws)


@router.websocket("/stock/{symbol}")
async def stock_ws(ws: WebSocket, symbol: str):
    """个股实时行情推送 (3s)"""
    await ws.accept()
    try:
        while True:
            try:
                from backend.services import get_realtime_quote, get_stock_name
                quote = get_realtime_quote(symbol)
                if quote:
                    await ws.send_json({
                        "type": "stock_quote",
                        "symbol": symbol,
                        "name": get_stock_name(symbol),
                        "price": quote.get("最新价", 0),
                        "change_pct": quote.get("涨跌幅", 0),
                        "volume": quote.get("成交量", 0),
                        "high": quote.get("最高", 0),
                        "low": quote.get("最低", 0),
                    })
                await asyncio.sleep(3)
            except asyncio.TimeoutError:
                pass
            except Exception:
                await asyncio.sleep(5)
    except (WebSocketDisconnect, Exception):
        pass


# 启动后台推送任务
_market_task_started = False


def start_market_pusher():
    """在应用启动时调用"""
    global _market_task_started
    if not _market_task_started:
        _market_task_started = True
        asyncio.get_event_loop().create_task(_market_pusher())
