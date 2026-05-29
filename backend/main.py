"""AStock 市场认知引擎 — FastAPI 后端入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.config import CORS_ORIGINS

# ── 结构化日志 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("astock")

# ── 速率限制 ──
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭生命周期管理"""
    logger.info("启动市场认知引擎...")
    try:
        from backend.database.db import init_db
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.warning("数据库初始化: %s", e)
    try:
        from vector_db.client import get_client
        get_client()
        logger.info("Qdrant 向量库就绪")
    except Exception as e:
        logger.warning("Qdrant 初始化: %s", e)
    try:
        from backend.routers.ws import start_market_pusher
        start_market_pusher()
        logger.info("WebSocket 推送已启动")
    except Exception as e:
        logger.warning("WebSocket 推送: %s", e)
    try:
        from backend.services.feishu_bot import start_bot
        start_bot()
        logger.info("飞书机器人已启动")
    except Exception as e:
        logger.warning("飞书机器人: %s", e)

    yield

    try:
        from backend.services.feishu_bot import stop_bot
        stop_bot()
    except Exception as e:
        logger.warning("飞书机器人停止: %s", e)
    logger.info("市场认知引擎已关闭")


app = FastAPI(
    title="AStock 市场认知引擎",
    description="A股市场行为逻辑分析系统",
    version="2.0.0",
    lifespan=lifespan,
)

# ── 速率限制中间件 ──
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "请求过于频繁，请稍后再试", "retry_after": str(exc)},
    )

# ── 全局错误处理 ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误"},
    )

# ── 请求日志中间件 ──
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/health"):
        logger.info("%s %s → %d", request.method, request.url.path, response.status_code)
    return response

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──
from backend.routers import analysis, stock
from backend.routers import auth as auth_router
from backend.routers import ws as ws_router

app.include_router(stock.router)
app.include_router(analysis.router)
app.include_router(ws_router.router)
app.include_router(auth_router.router)


@app.get("/")
def root():
    return {
        "service": "AStock 市场认知引擎",
        "status": "running",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    from backend.config import HOST, PORT
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
