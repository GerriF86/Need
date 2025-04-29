# src/processors/processors.py
# ─────────────────────────────────────────────────────────────────────────────
"""Processor registration for dynamic field updates in Vacalyser.

Attach all reactive field processors to TriggerEngine.
Each processor must accept one argument: a mutable dict (e.g. st.session_state).
"""

from __future__ import annotations
from typing import Callable

from src.logic.trigger_engine import TriggerEngine

# 🟢 Actual implementations
from src.processors.salary import update_salary_range
from src.processors.publication import update_publication_channels

# 🔘 Optional/Planned imports
# from src.processors.tasks import classify_tasks
# from src.processors.skills import analyse_skill_rarity
# from src.processors.relocation import suggest_relocation_package
# from src.processors.legal import suggest_disclaimer_for_fixed_term
# from src.processors.boolean_query import generate_boolean_query

# 🔧 Optional type alias for documentation clarity
StateDict = dict[str, object]

def register_all_processors(engine: TriggerEngine) -> None:
    """Attach all known processors to the engine."""
    
    # 🟢 Core processors (already wired via DAG in trigger_engine.py)
    engine.register_processor("salary_range", update_salary_range)
    engine.register_processor("desired_publication_channels", update_publication_channels)

    # 🔘 Future extensions (add DAG edges in _DEPENDENCY_PAIRS as needed)
    # engine.register_processor("technical_tasks", classify_tasks)
    # engine.register_processor("skillRarityIndex", analyse_skill_rarity)
    # engine.register_processor("relocation_assistance", suggest_relocation_package)
    # engine.register_processor("legalDisclaimers", suggest_disclaimer_for_fixed_term)
    # engine.register_processor("booleanQueryDachJobboards", generate_boolean_query)

    # 🧪 Optional: add validation hooks
    # engine.register_processor("jobLevel", validate_job_level_against_contract_type)
