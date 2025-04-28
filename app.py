# ──────────────────────────────────────────────────────────────────────────────
#  Vacalyser-Wizard – single-entry Streamlit application
#  --------------------------------------------------------------------------
#  • keeps “src/” on the Python path
#  • initialises session state – all keys come from src.state.session_state
#  • initialises the TriggerEngine (+ default graph & processors)
#  • shows ONE page whose contents are rendered step-by-step by run_wizard()
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

# --------------------------------------------------------------------------- #
# 1.  Make sure the local src/ package is importable
# --------------------------------------------------------------------------- #
_ROOT = Path(__file__).resolve().parent
_SRC  = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# --------------------------------------------------------------------------- #
# 2.  Local imports  (all must exist!)
# --------------------------------------------------------------------------- #
from state.session_state import initialize_session_state           # → src/state
from logic.trigger_engine import TriggerEngine, build_default_graph  # → src/logic
from pages.wizard import run_wizard                                # → src/pages
from processors.salary          import update_salary_range          # → src/processors
from processors.publication     import update_publication_channels  # →   “        ”

# --------------------------------------------------------------------------- #
# 3.  Streamlit config (sidebar logo, page title …)
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Vacalyser Wizard",
    page_icon="🧩",
    layout="wide",
)

# --------------------------------------------------------------------------- #
# 4.  Initialise session state *once* and expose TriggerEngine via st.session_state
# --------------------------------------------------------------------------- #
initialize_session_state()

if "trigger_engine" not in st.session_state:
    engine = TriggerEngine()
    build_default_graph(engine)
    # Register real processors
    engine.register_processor("salary_range",            update_salary_range)
    engine.register_processor("desired_publication_channels",
                              update_publication_channels)
    st.session_state["trigger_engine"] = engine          # persist between reruns

# --------------------------------------------------------------------------- #
# 5.  The UI – a single Wizard function that handles the multi-step flow
# --------------------------------------------------------------------------- #
run_wizard()

# (Optionally) show the Trace-Viewer panel on the right
if "trace_events" in st.session_state and st.session_state.trace_events:
    with st.sidebar.expander("🪄 Trace-Viewer", expanded=False):
        for ev in st.session_state.trace_events:
            st.write(ev)
