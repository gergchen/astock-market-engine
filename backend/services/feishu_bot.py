"""飞书机器人 — 通过 lark-oapi SDK 长连接接收消息，对接 LLM 回复."""

import json
import logging
import re
import threading
from urllib.request import Request, urlopen

from openai import OpenAI

from ..config import (
    AI_PROVIDER,
    CLAUDE_API_BASE,
    CLAUDE_API_KEY,
    CLAUDE_MODEL,
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)

FEISHU_DOMAIN = "https://open.feishu.cn"
MSG_MAX = 8000

# ── App 凭据（从魔兽项目迁移） ──
FEISHU_APP_ID = "cli_a973d0ec4d389bc8"
FEISHU_APP_SECRET = "NezGUyipNeOsJVKIM1hmCKegtrJcFpnY"

# ── Token 管理 ──
def _get_tenant_token(app_id: str, app_secret: str) -> str:
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = Request(
        f"{FEISHU_DOMAIN}/open-apis/auth/v3/tenant_access_token/internal",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urlopen(req, timeout=10).read())
    return resp["tenant_access_token"]


# ── 消息发送 ──
def send_message(chat_id: str, text: str, app_id: str = "", app_secret: str = "") -> bool:
    """向指定群聊发送文本消息."""
    app_id = app_id or FEISHU_APP_ID
    app_secret = app_secret or FEISHU_APP_SECRET
    if not app_id or not chat_id:
        return False
    try:
        token = _get_tenant_token(app_id, app_secret)
        content = json.dumps({"text": text[:MSG_MAX]})
        body = json.dumps({"receive_id": chat_id, "msg_type": "text", "content": content}).encode()
        url = f"{FEISHU_DOMAIN}/open-apis/im/v1/messages?receive_id_type=chat_id"
        req = Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        })
        urlopen(req, timeout=10)
        return True
    except Exception as e:
        logger.warning(f"飞书消息发送失败: {e}")
        return False


# ── LLM 回复 ──
def _call_llm(user_text: str, history: list | None = None) -> str:
    """调用后端 LLM 生成回复."""
    system_prompt = (
        "你是一个A股市场分析助手，部署在市场认知引擎中。"
        "你可以回答关于A股市场行情、技术分析、资金流向等问题。"
        "请用中文回复，保持专业简洁。"
    )
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-10:])  # 保留最近10轮
    messages.append({"role": "user", "content": user_text})

    try:
        if AI_PROVIDER == "claude":
            from anthropic import Anthropic
            client = Anthropic(api_key=CLAUDE_API_KEY, base_url=CLAUDE_API_BASE)
            resp = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                messages=messages,
            )
            return resp.content[0].text
        else:
            client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=2048,
            )
            return resp.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        return f"抱歉，我暂时无法回复（LLM 调用出错: {e}）"


# ── 消息处理器 ──
MessageHandler = callable


def default_handler(chat_id: str, user_text: str) -> str | None:
    """默认处理器：调用 LLM 回复用户（回复由 _on_message 统一发送，避免重复）。"""
    logger.info(f"收到飞书消息 [{chat_id}]: {user_text[:80]}")
    return _call_llm(user_text)


# ── SDK 长连接接收器 ──
class Receiver:
    """基于官方 SDK 的飞书长连接接收器."""

    def __init__(self, app_id: str, app_secret: str, handler: MessageHandler | None = None):
        self._app_id = app_id
        self._app_secret = app_secret
        self._handler = handler or default_handler
        self._client = None
        self._running = False
        self._processed: set[str] = set()

    def start(self) -> None:
        from lark_oapi.event.dispatcher_handler import EventDispatcherHandler
        from lark_oapi.ws import Client

        handler = (
            EventDispatcherHandler.builder("", "")
            .register_p2_im_message_receive_v1(lambda e: self._on_message(e))
            .build()
        )

        self._client = Client(
            app_id=self._app_id,
            app_secret=self._app_secret,
            event_handler=handler,
            domain=FEISHU_DOMAIN,
        )
        self._running = True
        logger.info("飞书长连接启动中...")
        self._client.start()

    def stop(self) -> None:
        self._running = False

    def _on_message(self, event) -> None:
        try:
            msg = event.event.message
            if msg.message_type != "text":
                return

            chat_id = msg.chat_id
            sender = event.event.sender
            if sender and sender.sender_type == "app":
                return
            content = json.loads(msg.content)
            user_text = content.get("text", "")
            user_text = re.sub(r'@_\w+\s*', '', user_text).strip()
            if not user_text:
                return

            msg_id = getattr(msg, 'message_id', '') or getattr(event.event.message, 'message_id', '')
            if msg_id:
                if msg_id in self._processed:
                    return
                self._processed.add(msg_id)
                if len(self._processed) > 500:
                    self._processed.clear()

            logger.info(f"飞书消息: [{chat_id}] {user_text[:50]}")
            reply = self._handler(chat_id, user_text)
            if reply:
                send_message(chat_id, reply, self._app_id, self._app_secret)
        except Exception as e:
            logger.warning(f"飞书消息处理异常: {e}")


# ── 全局管理 ──
_receiver: Receiver | None = None
_thread: threading.Thread | None = None


def start_bot(handler: MessageHandler | None = None) -> None:
    """启动飞书机器人（后台线程）."""
    global _receiver, _thread
    if _receiver:
        logger.info("飞书机器人已在运行")
        return
    _receiver = Receiver(FEISHU_APP_ID, FEISHU_APP_SECRET, handler)
    _thread = threading.Thread(target=_receiver.start, daemon=True, name="feishu-bot")
    _thread.start()
    logger.info("飞书机器人已启动")


def stop_bot() -> None:
    global _receiver
    if _receiver:
        _receiver.stop()
        _receiver = None
        logger.info("飞书机器人已停止")
