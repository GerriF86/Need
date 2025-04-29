# ── src/cross_components.py ─────────────────────────────────────────────
import json
import time
import streamlit as st
from typing import Callable, Any, Dict, List

# --------------------------------------------------------------------- #
#  1 · Tool-Registry – nur ChatGPT-Alias                                #
# --------------------------------------------------------------------- #
class ToolRegistry:
    """Speichert callable-Handles für externe Tools (hier nur ChatGPT)."""
    _registry: Dict[str, Callable] = {}

    @classmethod
    def get_or_register(cls, name: str, fn: Callable) -> Callable:
        if name not in cls._registry:
            cls._registry[name] = fn
        return cls._registry[name]

    # Ein sehr schlanker Wrapper um openai.ChatCompletion
    @staticmethod
    def chatgpt_call(prompt: str, **kw) -> str:
        import openai
        model      = kw.get("model",        "gpt-3.5-turbo")
        temperature= kw.get("temperature",  0.7)
        max_tokens = kw.get("max_tokens",   300)

        rsp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return rsp.choices[0].message.content.strip()


# --------------------------------------------------------------------- #
#  2 · Guardrails – triviale JSON-Validierung                           #
# --------------------------------------------------------------------- #
class Guardrails:
    """Nur eine einfache JSON-Schema-Prüfung, um Abstürze zu vermeiden."""
    @staticmethod
    def json_or_raise(txt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = json.loads(txt)
        except Exception as e:
            raise ValueError(f"Kein gültiges JSON: {e}")

        for k, typ in schema.items():
            if k not in data:
                raise ValueError(f"Schlüssel fehlt: {k}")
            if not isinstance(data[k], typ if isinstance(typ, tuple) else (typ,)):
                raise ValueError(f"Typ von {k} sollte {typ} sein, ist aber {type(data[k])}")
        return data


# --------------------------------------------------------------------- #
#  3 · TraceViewer – sammelt Events in st.session_state                 #
# --------------------------------------------------------------------- #
class TraceViewer:
    _STATE_KEY = "_trace_log"

    def __init__(self) -> None:
        if self._STATE_KEY not in st.session_state:
            st.session_state[self._STATE_KEY] = []

    def log(self, event: str, **payload):
        st.session_state[self._STATE_KEY].append(
            {"ts": round(time.time(), 3), "event": event, **payload}
        )

    def render_ui(self):
        for row in st.session_state[self._STATE_KEY]:
            st.write(f"• {time.strftime('%H:%M:%S', time.localtime(row['ts']))}",
                     row["event"], row.get("details", ""), row.get("data", ""))


# --------------------------------------------------------------------- #
#  4 · DynamicQuestionEngine – einfache Warteschlange                   #
# --------------------------------------------------------------------- #
class DynamicQuestionEngine:
    _QUEUE_KEY = "_dq_queue"
    _ANSW_KEY  = "_dq_answers"

    def __init__(self) -> None:
        if self._QUEUE_KEY not in st.session_state:
            st.session_state[self._QUEUE_KEY]: List[Dict[str, str]] = []
        if self._ANSW_KEY not in st.session_state:
            st.session_state[self._ANSW_KEY]: Dict[str, str] = {}

    # Frage einstellen
    def enqueue(self, key: str, question: str):
        if key in st.session_state[self._ANSW_KEY]:
            return                          # schon beantwortet
        if not any(q["key"] == key for q in st.session_state[self._QUEUE_KEY]):
            st.session_state[self._QUEUE_KEY].append({"key": key, "q": question})

    # Alle offenen Fragen rendern
    def render_pending_questions(self):
        if not st.session_state[self._QUEUE_KEY]:
            return

        st.subheader("↪ Folgefragen")
        remaining = []
        for item in st.session_state[self._QUEUE_KEY]:
            answer = st.text_input(item["q"], key=f"dq_{item['key']}")
            if answer:
                st.session_state[self._ANSW_KEY][item["key"]] = answer
            else:
                remaining.append(item)      # bleibt weiter offen
        st.session_state[self._QUEUE_KEY] = remaining
