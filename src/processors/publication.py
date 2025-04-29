
"""
Publication-Channel Processor
-----------------------------

Sets **desired_publication_channels** based on the remote/onsite pattern.
"""
from __future__ import annotations
from typing import Any, Dict
from src.utils.tool_registry import chat_completion

_REMOTE_BOARDS = "LinkedIn Remote • WeWorkRemotely • Remote-OK"
_HYBRID_BOARDS = "LinkedIn • StepStone • HybridJobs"
_ONSITE_BOARDS = "LinkedIn • Indeed • StepStone"

answer = chat_completion(prompt, model="gpt-4o-mini", temperature=0.2, max_tokens=40)

def update_publication_channels(state: Dict[str, Any]) -> None:
    """Triggered by changes to *remote_work_policy*."""
    policy = (state.get("remote_work_policy") or "").lower()

    # If the user already chose channels we *never* overwrite them
    if state.get("desired_publication_channels"):
        return

    if "full" in policy and "remote" in policy:
        state["desired_publication_channels"] = _REMOTE_BOARDS
    elif "hybrid" in policy:
        state["desired_publication_channels"] = _HYBRID_BOARDS
    else:
        state["desired_publication_channels"] = _ONSITE_BOARDS
