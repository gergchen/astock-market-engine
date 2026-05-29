"""用户认证 — 注册 / 登录 / Token 验证

使用 bcrypt-like sha256 + salt 密码哈希，HMAC-SHA256 JWT。
纯标准库实现，零外部依赖。
"""
import hashlib
import hmac
import json
import os
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from backend.database.db import SessionLocal
from backend.database.models import User

router = APIRouter(prefix="/api/auth", tags=["认证"])

# JWT secret — 生产环境应从环境变量读取
from backend.config import JWT_SECRET as _jwt_secret_env

_JWT_SECRET = _jwt_secret_env.encode() if _jwt_secret_env else os.urandom(32)
_TOKEN_EXPIRE_HOURS = 72

# ─── Request/Response models ───────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class UserInfo(BaseModel):
    username: str
    email: str | None = None
    is_active: bool = True

# ─── Password hashing ──────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return urlsafe_b64encode(salt + dk).decode()


def _verify_password(password: str, stored: str) -> bool:
    try:
        raw = urlsafe_b64decode(stored.encode())
        salt, dk = raw[:16], raw[16:]
        new_dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return hmac.compare_digest(dk, new_dk)
    except Exception:
        return False


# ─── JWT ───────────────────────────────────────────────────────────────────────

def _create_token(username: str) -> str:
    header = urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    exp = int(time.time()) + _TOKEN_EXPIRE_HOURS * 3600
    payload = urlsafe_b64encode(json.dumps({"sub": username, "exp": exp}).encode()).decode().rstrip("=")
    sig_raw = hmac.new(_JWT_SECRET, f"{header}.{payload}".encode(), "sha256").digest()
    sig = urlsafe_b64encode(sig_raw).decode().rstrip("=")
    return f"{header}.{payload}.{sig}"


def _verify_token(token: str) -> str | None:
    """验证 token 并返回 username，失败返回 None"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        # Verify signature
        expected_sig = urlsafe_b64encode(
            hmac.new(_JWT_SECRET, f"{header}.{payload}".encode(), "sha256").digest()
        ).decode().rstrip("=")
        if not hmac.compare_digest(sig.encode(), expected_sig.encode()):
            return None
        # Decode payload (add padding)
        payload += "=" * (4 - len(payload) % 4) if len(payload) % 4 else ""
        data = json.loads(urlsafe_b64decode(payload.encode()))
        if data.get("exp", 0) < time.time():
            return None
        return data.get("sub")
    except Exception:
        return None


# ─── Dependency ────────────────────────────────────────────────────────────────

def get_current_user(authorization: str = Header("")) -> str | None:
    """FastAPI 依赖：从 Bearer token 提取当前用户名"""
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return _verify_token(token)


def require_user(username: str | None = Depends(get_current_user)) -> str:
    """FastAPI 依赖：要求登录，否则 401"""
    if username is None:
        raise HTTPException(401, "请先登录")
    return username


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    """用户注册"""
    if len(req.username) < 2 or len(req.username) > 50:
        raise HTTPException(400, "用户名长度 2-50 个字符")
    if len(req.password) < 6:
        raise HTTPException(400, "密码长度至少 6 位")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == req.username).first()
        if existing:
            raise HTTPException(409, "用户名已存在")

        user = User(
            username=req.username,
            email=req.email,
            hashed_password=_hash_password(req.password),
        )
        db.add(user)
        db.commit()

        token = _create_token(req.username)
        return TokenResponse(access_token=token, username=req.username)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """用户登录"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == req.username).first()
        if not user or not _verify_password(req.password, user.hashed_password):
            raise HTTPException(401, "用户名或密码错误")
        if not user.is_active:
            raise HTTPException(403, "账户已禁用")

        token = _create_token(req.username)
        return TokenResponse(access_token=token, username=req.username)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/me", response_model=UserInfo)
def get_me(username: str = Depends(require_user)):
    """获取当前用户信息"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(404, "用户不存在")
        return UserInfo(username=user.username, email=user.email, is_active=bool(user.is_active))
    finally:
        db.close()



