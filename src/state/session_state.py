"""Initialises **all** keys exactly once."""
from __future__ import annotations
import streamlit as st
from src.config.keys import STEP_KEYS, GENERATED_KEYS

_ALL_KEYS: list[str] = [k for keys in STEP_KEYS.values() for k in keys] + GENERATED_KEYS + [
    "wizard_step",            # current page
    "_snapshot",              # prev-run value cache for TriggerEngine diff
]

def ensure_keys() -> None:
    for k in _ALL_KEYS:
        st.session_state.setdefault(k, "")
    st.session_state.setdefault("wizard_step", 1)

def initialize_session_state() -> None:          # ← new public alias
    """Backwards-compat wrapper for older imports."""
    ensure_keys()
