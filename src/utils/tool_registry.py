# src/utils/tool_registry.py
# ────────────────────────────────────────────────────────────────────────────
"""
Global Tool & LLM helper for Vacalyser Wizard
=============================================
*  **chat_completion(...)**  → OpenAI v1 wrapper (3-retry exponential back-off)
*  **@tool** / get_tool()    → tiny registry making any callable discoverable
---------------------------------------------------------------------------
Environment variables *or* Streamlit `st.secrets` are honoured automatically:

    OPENAI_API_KEY       mandatory
    OPENAI_ORGANIZATION  optional
    OPENAI_MODEL         optional (falls back to 'gpt-4o')
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List

import streamlit as st
from openai import OpenAI                     # pip install openai>=1.0
from tenacity import (                        # pip install tenacity
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# ────────────────────────────────────────────────────────────────────────────
# 1  OpenAI client (instantiated exactly once)
# ────────────────────────────────────────────────────────────────────────────
_api_key = (
    os.getenv("OPENAI_API_KEY")
    or st.secrets.get("OPENAI_API_KEY", "")    # ← Streamlit secrets take 2nd priority
)
if not _api_key:
    raise RuntimeError("OPENAI_API_KEY not found (env or st.secrets).")

_client = OpenAI(
    api_key=_api_key,
    organization=os.getenv("OPENAI_ORGANIZATION") or st.secrets.get("OPENAI_ORGANIZATION"),
)

_MODEL_DEFAULT: str = (
    os.getenv("OPENAI_MODEL") or st.secrets.get("OPENAI_MODEL", "gpt-4o")
)

# ────────────────────────────────────────────────────────────────────────────
# 1a  Low-level chat call with three retries (1 → 4 s back-off)
# ────────────────────────────────────────────────────────────────────────────
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _send_chat(
    messages: List[Dict[str, str]],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Returns **content** of the first choice (stripped)."""
    resp = _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def chat_completion(
    prompt: str,
    *,
    system: str | None = None,
    model: str = _MODEL_DEFAULT,
    temperature: float = 0.7,
    max_tokens: int = 256,
) -> str:
    """
    Convenience façade around OpenAI ChatCompletion.

    Only **returns the assistant content** (so callers never need to unpack).
    Retries (3×) are built-in; any exception after three attempts will bubble up.
    """
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
# 2  Tool registry (super-small on purpose)
# ────────────────────────────────────────────────────────────────────────────
_TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {}


def tool(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that registers *func* under its name.

    Example
    -------
        @tool
        def fetch_something(url: str) -> str: ...
    """
    _TOOL_REGISTRY[func.__name__] = func
    return func


def get_tool(name: str) -> Callable[..., Any]:
    """Look up a tool – raises *KeyError* if missing."""
    return _TOOL_REGISTRY[name]


def all_tools() -> Dict[str, Callable[..., Any]]:
    """Return a **copy** of the registry (read-only for callers)."""
    return dict(_TOOL_REGISTRY)

# ────────────────────────────────────────────────────────────────────────────
# 3  Logging (optional)
# ────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)
