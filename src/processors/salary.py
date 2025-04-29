"""
Salary-Range Processor
----------------------

Recomputes **salary_range** when *task_list*, *must_have_skills* or
`parsed_data_raw` change.

❶  If a human value already exists → keep it.  
❷  Otherwise call OpenAI to obtain a benchmark string "min – max EUR".
❸  Fallback: placeholder.
"""
from __future__ import annotations
from typing import Any, Dict
from src.utils.tool_registry import chat_completion
import os
from openai import APIConnectionError

_OPENAI_KEY = os.getenv("OPENAI_API_KEY")
answer = chat_completion(prompt, model="gpt-4o-mini", temperature=0.2, max_tokens=40)
state["salary_range"] = answer

def _llm_salary_estimate(role: str, tasks: str, skills: str, city: str) -> str:
    """Tiny helper – wraps the OpenAI completion."""
    if client is None:
        return "n/a"

    prompt = (
        "Estimate a realistic salary range in EUR for the following position "
        "in Germany.  Answer **only** as \"min – max EUR\" (e.g. \"55 000 – 65 000 EUR\").\n\n"
        f"Job title: {role or 'unknown'}\n"
        f"City: {city or 'n/a'}\n"
        f"Key tasks: {tasks or '-'}\n"
        f"Must-have skills: {skills or '-'}\n"
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=25,
            messages=[
                {"role": "system", "content": "You are a labour-market analyst."},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content.strip()
    except APIConnectionError:
        return "n/a"


# --------------------------------------------------------------------------- #
# Public processor – imported & registered in *app.py*
# --------------------------------------------------------------------------- #
def update_salary_range(state: Dict[str, Any]) -> None:
    """Processor called by TriggerEngine – mutates state in-place."""
    # keep manual edits
    if state.get("salary_range"):
        return

    tasks = state.get("task_list", "")
    skills = state.get("must_have_skills", "")
    role  = state.get("job_title", "")
    city  = state.get("city", "")

    estimate = _llm_salary_estimate(role, tasks, skills, city)
    state["salary_range"] = estimate or "Auto-estimation pending"
