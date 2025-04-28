from __future__ import annotations
import re, unicodedata
from typing import List, Dict, Any, Tuple, Mapping
import streamlit as st
from pydantic import BaseModel, Field
from openai import OpenAI
from src.trigger_engine import TriggerEngine, build_default_graph

_openai = OpenAI()          # env var / st.secrets

class RoleBreakdown(BaseModel):
    tasks:  List[str] = Field(..., description="Verb-started sentences.")
    skills: List[str] = Field(..., description="Single-word skills.")
    extras: List[str] = Field([],  description="Other bullets.")

JSON_SCHEMA: Dict[str, Any] = RoleBreakdown.model_json_schema()

def _clean_skill(tok: str) -> str:
    tok = unicodedata.normalize("NFKD", tok)
    tok = re.sub(r"[^\w+-]", "", tok)
    return tok.lower().strip()

def extract_role_details(role_description: str,
                         state: Mapping[str, Any] | None = None,
                         engine: TriggerEngine | None = None
                         ) -> Tuple[List[str], List[str]]:
    resp = _openai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        max_tokens=512,
        response_format={"type": "json_object", "schema": JSON_SCHEMA},
        messages=[
            {"role": "system",
             "content": ("Extract bullet tasks + single-word skills as JSON.")},
            {"role": "user", "content": role_description},
        ],
    )
    data = RoleBreakdown.model_validate_json(resp.choices[0].message.content)
    state = state or st.session_state

    for i, t in enumerate(data.tasks, 1):
        state[f"task_{i:02d}"] = t.strip()
    for i, s in enumerate(data.skills, 1):
        state[f"skill_{i:02d}"] = _clean_skill(s)

    state["task_list"]   = "\n".join(data.tasks)
    state["hard_skills"] = ", ".join(sorted({_clean_skill(s) for s in data.skills}))

    if engine is None:
        engine = getattr(st.session_state, "_trigger_engine", None) or TriggerEngine()
        build_default_graph(engine)
        st.session_state._trigger_engine = engine

    for f in [f"task_{i:02d}" for i in range(1, len(data.tasks)+1)] + \
             [f"skill_{i:02d}" for i in range(1, len(data.skills)+1)]:
        engine.notify_change(f, state)

    return data.tasks, data.skills
