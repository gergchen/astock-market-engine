"""全局配置"""
import os

from dotenv import load_dotenv

load_dotenv()

# ── AI API ──
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_API_BASE = os.getenv("CLAUDE_API_BASE", "https://api.anthropic.com")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")

# ── 服务器 ──
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8005"))

# ── CORS: 默认仅允许本地前端，生产环境显式配置 ──
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

# ── 认证 ──
JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET or JWT_SECRET == "change-me-to-a-random-string-in-production":
    # 开发环境允许默认值，生产环境应设置强密钥
    pass

# ── 飞书 ──
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")

# ── 数据库 ──
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/market_memory.db")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# ── RAG ──
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"
RAG_SIMILAR_DAYS_COUNT = int(os.getenv("RAG_SIMILAR_DAYS_COUNT", "5"))
RAG_QDRANT_PATH = os.getenv("RAG_QDRANT_PATH", "./data/qdrant_storage")
