"""SQLAlchemy 数据模型 — SQLite / PostgreSQL 兼容"""
from sqlalchemy import JSON, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class MarketSnapshot(Base):
    """每日市场快照"""
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    limit_up_count = Column(Integer, default=0)
    limit_down_count = Column(Integer, default=0)
    zhaban_rate = Column(Float, default=0.0)
    board_height = Column(Integer, default=0)
    index_change = Column(Float, default=0.0)
    up_down_ratio = Column(Float, default=0.0)
    emotion_stage = Column(String(20), default="")
    metadata_json = Column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_snapshot_date", "date"),
        Index("idx_snapshot_emotion", "emotion_stage"),
    )


class ReviewRecord(Base):
    """AI 复盘记录"""
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ai_review_text = Column(Text, default="")
    emotion_stage = Column(String(20), default="")

    __table_args__ = (
        Index("idx_review_date", "date"),
        Index("idx_review_emotion", "emotion_stage"),
    )


class User(Base):
    """用户账户"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(128), nullable=False)
    is_active = Column(Integer, default=1)  # SQlite doesn't have Boolean
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_user_username", "username"),
    )
