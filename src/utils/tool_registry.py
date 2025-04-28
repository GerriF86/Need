# src/utils/tool_registry.py
# ────────────────────────────────────────────────────────────────────────────
"""Global Tool & LLM helper for Vacalyser.

* **LLM wrapper** (`chat_completion`) – OpenAI v1 client, 3-retry back-off
* **Tool registry**   (`@tool`)        – makes any callable discoverable
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Union

from openai import OpenAI          # pip install openai>=1.0
from tenacity import (             # pip install tenacity
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# ────────────────────────────────────────────────────────────────────────────
# 1.  OpenAI client – pulled from env / st.secrets automatically
# ────────────────────────────────────────────────────────────────────────────
_client = OpenAI()     # auto-reads OPENAI_API_KEY + OPENAI_ORG
_MODEL_DEFAULT = "gpt-4o"


# ------------------------------------------------------------------------
# 1a  – helper with 3-retry exponential back-off (1s → 4s)
# ------------------------------------------------------------------------
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=(
        retry_if_exception_type(IOError)
        | retry_if_exception_type(RuntimeError)
        | retry_if_exception_type(Exception)   # generic OpenAI error
    ),
    reraise=True,
)
def _send_chat(messages: List[Dict[str, str]], *, model: str, **kwargs: Any) -> str:
    """Raw call to OpenAI with retry."""
    resp = _client.chat.completions.create(model=model, messages=messages, **kwargs)
    return resp.choices[0].message.content.strip()


def chat_completion(
    prompt: str,
    *,
    system: str | None = None,
    model: str = _MODEL_DEFAULT,
    temperature: float = 0.7,
    max_tokens: int = 256,
) -> str:
    """Public helper → returns *content* only (no role metadata)."""
    msgs: list[dict[str, str]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return _send_chat(
        msgs,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ────────────────────────────────────────────────────────────────────────────
# 2.  Tool registry (very small)
# ────────────────────────────────────────────────────────────────────────────
_TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {}


def tool(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that auto-adds *func* to the global registry."""
    _TOOL_REGISTRY[func.__name__] = func
    return func


def get_tool(name: str) -> Callable[..., Any]:
    """Look up a tool – raises *KeyError* if missing."""
    return _TOOL_REGISTRY[name]


def all_tools() -> Dict[str, Callable[..., Any]]:
    """Returns the full mapping (read-only!)."""
    return dict(_TOOL_REGISTRY)


# ────────────────────────────────────────────────────────────────────────────
# 3.  Convenience logging
# ────────────────────────────────────────────────────────────────────────────
_log = logging.getLogger("tool_registry")
if not _log.handlers:
    logging.basicConfig(level=logging.INFO)
