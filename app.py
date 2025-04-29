# app.py – Vacalyser Wizard main application
from __future__ import annotations
import sys
from pathlib import Path
import streamlit as st

# 1. Ensure local src/ package is on Python path
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# 2. Local imports (initialized modules)
from state.session_state import initialize_session_state      # src/state/session_state.py
from logic.trigger_engine import TriggerEngine, build_default_graph  # src/logic/trigger_engine.py
from processors import register_all_processors                      # src/processors.py
from pages.wizard import run_wizard                                  # src/pages/wizard.py

# 3. Streamlit page config (wide layout, title, icon)
st.set_page_config(page_title="Vacalyser Wizard", page_icon="🧩", layout="wide")

# 4. Initialize session state and TriggerEngine on first load
initialize_session_state()
if "trigger_engine" not in st.session_state:
    engine = TriggerEngine()
    build_default_graph(engine)
    register_all_processors(engine)  # registers all processors (salary_range, publication_channels, etc.)
    st.session_state["trigger_engine"] = engine
# Ensure trace_events list for logging (for Trace-Viewer)
if "trace_events" not in st.session_state:
    st.session_state["trace_events"] = []

# 5. Run the multi-step wizard UI
run_wizard()

# 6. Optional Trace-Viewer panel in sidebar (for debugging/tracing events)
if st.session_state.get("trace_events"):
    with st.sidebar.expander("🪄 Trace-Viewer", expanded=False):
        for ev in st.session_state.trace_events:
            st.write(ev)
