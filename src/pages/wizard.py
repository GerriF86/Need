from __future__ import annotations
import streamlit as st
from src.state.session_state import ensure_keys
from src.config.keys import STEP_KEYS
from src.core.trigger_engine_runtime import dispatch_triggers
from src.components.dynamic_questions import maybe_render_followups  # stub
from src.components.guardrails import guard_all_inputs               # stub

ensure_keys()
step: int = st.session_state["wizard_step"]

st.title("Vacalyser – Vacancy Wizard")

# ───────────────────────── navigation header ─────────────────────────
col_prev, col_next = st.columns(2)
if step > 1 and col_prev.button("← Previous"):
    st.session_state["wizard_step"] -= 1
if step < 8 and col_next.button("Next →"):
    st.session_state["wizard_step"] += 1

st.divider()

# ───────────────────────── step renderer loop ────────────────────────
def render_inputs(keys: list[str]) -> None:
    """Render simple text inputs (you can replace with your fancy components)."""
    for k in keys:
        if k in {"uploaded_file"}:
            st.session_state[k] = st.file_uploader("Ad PDF / DOCX / TXT", key=k) or st.session_state[k]
        elif k.endswith("_range"):   # quick heuristic for salary_range
            st.session_state[k] = st.text_input(k.replace("_", " ").title(), key=k)
        else:
            st.session_state[k] = st.text_input(k.replace("_", " ").title(), key=k)

if step == 1:
    st.header("Step 1 – Discovery")
    render_inputs(STEP_KEYS[1])
    st.expander("Parsed preview").markdown(st.session_state.get("parsed_data_raw", "—"))

elif step == 2:
    st.header("Step 2 – Job & Company")
    render_inputs(STEP_KEYS[2])

elif step == 3:
    st.header("Step 3 – Role Definition")
    render_inputs(STEP_KEYS[3])

elif step == 4:
    st.header("Step 4 – Tasks & Responsibilities")
    render_inputs(STEP_KEYS[4])

elif step == 5:
    st.header("Step 5 – Skills & Competencies")
    render_inputs(STEP_KEYS[5])

elif step == 6:
    st.header("Step 6 – Compensation & Benefits")
    render_inputs(STEP_KEYS[6])

elif step == 7:
    st.header("Step 7 – Recruitment Process")
    render_inputs(STEP_KEYS[7])

elif step == 8:
    st.header("Step 8 – Additional & Summary")
    render_inputs(STEP_KEYS[8])
    st.success("All steps completed – you can now generate artefacts.")

# ───────────────────── dynamic questions & guardrails ────────────────
maybe_render_followups()   # shows queued questions (stub)
guard_all_inputs()         # real-time validation (stub)

# ───────────────────── trigger engine dispatch (last) ────────────────
dispatch_triggers()
