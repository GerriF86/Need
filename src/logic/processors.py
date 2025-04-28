from __future__ import annotations
from src.logic.trigger_engine import TriggerEngine
from src.utils.tool_registry import call_with_retry   # tenacity-wrapped openai call
from openai import OpenAI

client = OpenAI()

# ───────────────────────── processors ──────────────────────────
def update_salary_range(state: dict) -> None:
    if state.get("salary_range") and state["salary_range"] != "competitive":
        return                      # already concrete

    prompt = (
        "Estimate a fair annual salary range in EUR for the following role.\n"
        f"City: {state.get('city')}\n"
        f"Tasks: {state.get('task_list')}\n"
        f"Must-have skills: {state.get('must_have_skills')}"
    )
    answer = call_with_retry(client.chat.completions.create,
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}],
        temperature=0.2, max_tokens=40
    )
    state["salary_range"] = answer.choices[0].message.content.strip()

def update_publication_channels(state: dict) -> None:
    remote = state.get("remote_work_policy", "").lower()
    if remote in {"hybrid", "full remote"}:
        state["desired_publication_channels"] = "LinkedIn Remote Jobs; WeWorkRemotely"

def register_all_processors(engine: TriggerEngine) -> None:
    engine.register_processor("salary_range", update_salary_range)
    engine.register_processor("desired_publication_channels", update_publication_channels)
