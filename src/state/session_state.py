import streamlit as st
from src.config import keys  # assuming keys.py defines STEP_KEYS or similar

class SessionState:
    """Helper class to manage Vacalyser session state across Streamlit reruns."""
    def __init__(self):
        # Initialize all expected keys in session_state if not present
        for step, field_list in keys.STEP_KEYS.items():
            for field in field_list:
                if field not in st.session_state:
                    st.session_state[field] = None

    def reset(self):
        """Clear all job spec fields from session state (e.g., to start a new session)."""
        for step, field_list in keys.STEP_KEYS.items():
            for field in field_list:
                if field in st.session_state:
                    del st.session_state[field]

    # Convenience getters/setters can be added for frequently accessed fields, e.g.:
    def get_job_spec_dict(self):
        """Return a dictionary of all JobSpec fields from session state."""
        spec = {}
        for step, field_list in keys.STEP_KEYS.items():
            for field in field_list:
                spec[field] = st.session_state.get(field)
        return spec

    def load_from_dict(self, data: dict):
        """Load multiple fields into session state from a given dict (e.g., from AI output)."""
        for key, value in data.items():
            if key in st.session_state:
                st.session_state[key] = value
