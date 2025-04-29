# src/processors/processors.py
# ─────────────────────────────────────────────────────────────────────────────
from src.logic.trigger_engine import TriggerEngine
from src.processors.salary import update_salary_range
from src.processors.publication import update_publication_channels
# (you can import more processor functions here as you add them)

def register_all_processors(engine: TriggerEngine) -> None:
    """Registers all field-update processors with the TriggerEngine."""
    engine.register_processor("salary_range", update_salary_range)
    engine.register_processor("desired_publication_channels", update_publication_channels)
    # Add more as needed
