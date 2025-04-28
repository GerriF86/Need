"""
Vacalyser – Streamlit bootstrap.

Keeps the file ultra-thin; all real UI lives inside `src.pages.wizard`.
Feel free to add global theming, telemetry or error-handling here.
"""

from __future__ import annotations

import streamlit as st

# Make sure Python finds `src/` when running `streamlit run app.py`
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pages.wizard import run_wizard          # noqa: E402  (import after sys.path hack)

# --------------------------------------------------------------------------- #
# Streamlit configuration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Vacalyser – Vacancy Wizard",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Kick off the UI
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    run_wizard()
