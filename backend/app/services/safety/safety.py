"""Scope and safety checks for user requests."""

from __future__ import annotations

from fastapi import HTTPException


def ensure_request_is_in_scope(user_text: str) -> None:
    """Reject obviously out-of-scope requests.

    The career assistant can discuss wellbeing in a work-design sense, but it
    should not position itself as a therapy or crisis-response system.
    """

    lowered_text = user_text.lower()
    blocked_terms = ("self-harm", "suicide", "kill myself")
    if any(term in lowered_text for term in blocked_terms):
        raise HTTPException(
            status_code=400,
            detail=(
                "This prototype is not a crisis-response system. "
                "Escalation and support guidance should be handled separately."
            ),
        )
