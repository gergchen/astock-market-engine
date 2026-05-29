"""LLM 客户端 — 统一 Claude / OpenAI 调用"""
import logging

from openai import OpenAI

from backend.config import (
    AI_PROVIDER,
    CLAUDE_API_BASE,
    CLAUDE_API_KEY,
    CLAUDE_MODEL,
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

logger = logging.getLogger('astock.llm')


def call_llm(prompt: str) -> str:
    """根据 AI_PROVIDER 调用对应的 LLM"""
    if AI_PROVIDER == 'claude':
        return _call_claude(prompt)
    return _call_openai(prompt)


def _call_claude(prompt: str) -> str:
    """调用 Claude API"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, base_url=CLAUDE_API_BASE)
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return message.content[0].text
    except Exception as e:
        logger.warning('Claude API 调用失败: %s', e)
        raise


def _call_openai(prompt: str) -> str:
    """调用 OpenAI / DeepSeek 兼容接口"""
    try:
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=2000,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning('OpenAI API 调用失败: %s', e)
        raise
