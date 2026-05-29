"""飞书通知 — 通过 Webhook 推送消息到飞书群聊."""

import json
import logging
from urllib.request import Request, urlopen

from ..config import FEISHU_WEBHOOK_URL

logger = logging.getLogger(__name__)

MAX_BODY = 8000


def send_text(text: str, webhook_url: str = "") -> bool:
    """发送文本消息到飞书群聊."""
    url = webhook_url or FEISHU_WEBHOOK_URL
    if not url:
        logger.warning("FEISHU_WEBHOOK_URL 未配置")
        return False

    payload = json.dumps({
        "msg_type": "text",
        "content": {"text": text[:MAX_BODY]},
    }).encode()

    try:
        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        urlopen(req, timeout=5)
        return True
    except Exception as e:
        logger.warning(f"飞书消息发送失败: {e}")
        return False


def send_markdown(title: str, content: str, webhook_url: str = "") -> bool:
    """发送富文本/ Markdown 消息到飞书群聊."""
    url = webhook_url or FEISHU_WEBHOOK_URL
    if not url:
        logger.warning("FEISHU_WEBHOOK_URL 未配置")
        return False

    payload = json.dumps({
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title[:128],
                    "content": [
                        [{"tag": "text", "text": content[:MAX_BODY]}],
                    ],
                }
            }
        },
    }).encode()

    try:
        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        urlopen(req, timeout=5)
        return True
    except Exception as e:
        logger.warning(f"飞书消息发送失败: {e}")
        return False
