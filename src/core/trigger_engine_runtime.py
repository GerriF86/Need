"""
Glue-code that
• instantiates the TriggerEngine only once,
• computes diffs on every rerun,
• fires processors for *each* changed key.
"""

from __future__ import annotations
import streamlit as st
from copy import deepcopy
from src.logic.trigger_engine import TriggerEngine, build_default_graph
from src.logic.processors import register_all_processors   # you’ll create this

# one global engine
if "_engine" not in st.session_state:
    st.session_state["_engine"] = TriggerEngine()
    build_default_graph(st.session_state["_engine"])
    register_all_processors(st.session_state["_engine"])

engine: TriggerEngine = st.session_state["_engine"]

def dispatch_triggers() -> None:
    prev: dict = st.session_state.get("_snapshot", {})
    current = {k: v for k, v in st.session_state.items() if not k.startswith("_")}
    changed = [k for k, v in current.items() if prev.get(k) != v]

    for key in changed:
        engine.notify_change(key, st.session_state)

    # store deep copy for next run
    st.session_state["_snapshot"] = deepcopy(current)
