"""
Trigger-Engine
==============

*Pure-Python, Streamlit-agnostic* dependency engine used by Vacalyser.

An edge **A → B** means: *whenever field A changes, recompute B*.
Processor callbacks receive **state** (normally `st.session_state`) so they can
read & mutate wizard values.

Typical usage
-------------
>>> from logic.trigger_engine import TriggerEngine, build_default_graph
>>> engine = TriggerEngine()
>>> build_default_graph(engine)
>>> engine.register_processor("salary_range", update_salary_range)
>>> engine.notify_change("task_list", st.session_state)
"""
from __future__ import annotations

from typing import Callable, Dict, Iterable, Set
import networkx as nx

__all__ = ["TriggerEngine", "build_default_graph"]  # re-export


# ────────────────────────────────────────────────────────────────────────────
# Core engine
# ────────────────────────────────────────────────────────────────────────────
class TriggerEngine:
    """DAG of field-dependencies + processor registry."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self._processors: Dict[str, Callable[[dict], None]] = {}

    # ------------------------------------------------------------------ graph
    def register_node(self, key: str) -> None:
        if key not in self.graph:
            self.graph.add_node(key)

    def register_dependency(self, source: str, target: str) -> None:
        """Declare *target* depends on *source* (edge source→target)."""
        self.register_node(source)
        self.register_node(target)
        self.graph.add_edge(source, target)

    def register_dependencies(self, pairs: Iterable[tuple[str, str]]) -> None:
        for src, tgt in pairs:
            self.register_dependency(src, tgt)

    # ---------------------------------------------------------- processors API
    def register_processor(self, key: str, func: Callable[[dict], None]) -> None:
        """Attach callback that refreshes *key*."""
        self._processors[key] = func

    # -------------------------------------------------------------- run-time
    def notify_change(self, updated_key: str, state: dict) -> None:
        """Call all processors downstream of *updated_key* (depth-first)."""
        if updated_key not in self.graph:
            return  # nothing depends on it

        affected: Set[str] = nx.descendants(self.graph, updated_key)
        for node in affected:
            processor = self._processors.get(node)
            if processor is not None:
                processor(state)


# ────────────────────────────────────────────────────────────────────────────
# Default dependency map  (v0 wizard – 11 refined reasoning-hooks)
# ────────────────────────────────────────────────────────────────────────────
_DEPENDENCY_PAIRS: list[tuple[str, str]] = [
    # 1  Tasks  → Salary Range (supply/demand complexity)
    ("task_list", "salary_range"),
    # 2  Must-Have Skills → Salary Range
    ("must_have_skills", "salary_range"),
    # 5  Remote Policy → Publication Channels
    ("remote_work_policy", "desired_publication_channels"),
    # 6  Role Keywords → SEO Keyword set (aux field)
    ("role_keywords", "seo_keywords"),
    # 7  Industry Experience → Task Suggestions
    ("industry_experience", "task_list"),
    # 8  Team Structure → Reports To & Supervises
    ("team_structure", "reports_to"),
    ("team_structure", "supervises"),
    # 9  Tool Proficiency → Technical Tasks
    ("tool_proficiency", "technical_tasks"),
    # 11 Competitive-placeholder → Salary Range
    ("parsed_data_raw", "salary_range"),
    # 13 Soft Skills → Interview Questions (aux field)
    ("soft_skills", "interview_questions"),
    # 17 Language Reqs → Translation Required flag
    ("language_requirements", "translation_required"),
    # 18 Company-Candidate distance → Relocation Assistance
    ("company_location_distance", "relocation_assistance"),
]


def build_default_graph(engine: TriggerEngine) -> None:
    """Populate *engine* with the canonical Vacalyser dependency graph."""
    engine.register_dependencies(_DEPENDENCY_PAIRS)
