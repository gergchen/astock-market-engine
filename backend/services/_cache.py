"""TTL 内存缓存 + mock 状态追踪

所有服务模块共享的底层设施，零内部依赖。
"""
import threading
import time

_DEFAULT_TTL = 60  # 秒

_CACHE: dict[str, tuple] = {}
_CACHE_LOCK = threading.Lock()

_MOCK_USED_SYMBOLS: set = set()
_MOCK_LOCK = threading.Lock()


def _cache_get(key: str):
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if item is None:
            return None
        value, expire_at = item
        if time.time() > expire_at:
            _CACHE.pop(key, None)
            return None
        return value


def _cache_set(key: str, value, ttl: int = _DEFAULT_TTL):
    with _CACHE_LOCK:
        _CACHE[key] = (value, time.time() + ttl)


def mark_mock_used(symbol: str):
    with _MOCK_LOCK:
        _MOCK_USED_SYMBOLS.add(symbol)


def pop_mock_used() -> bool:
    with _MOCK_LOCK:
        if _MOCK_USED_SYMBOLS:
            _MOCK_USED_SYMBOLS.clear()
            return True
        return False
