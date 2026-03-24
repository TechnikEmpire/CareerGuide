"""Scope and safety checks for user requests."""

from __future__ import annotations

import re

from fastapi import HTTPException

_SELF_HARM_PATTERN = re.compile(r"\b(self-harm|suicide|kill myself)\b", flags=re.IGNORECASE)
_EXPLOITATION_PATTERN = re.compile(
    r"\b(pimp|pimping|sex traffick|trafficking|human traffick)\b"
    r"|сутен|торговл.*люд|трафик.*люд",
    flags=re.IGNORECASE,
)


def ensure_request_is_in_scope(user_text: str) -> None:
    """Reject obviously out-of-scope requests.

    The career assistant can discuss wellbeing in a work-design sense, but it
    should not position itself as a therapy or crisis-response system.
    """

    if _SELF_HARM_PATTERN.search(user_text):
        raise HTTPException(
            status_code=400,
            detail=(
                "This prototype is not a crisis-response system. "
                "Escalation and support guidance should be handled separately."
            ),
        )
    if _EXPLOITATION_PATTERN.search(user_text):
        raise HTTPException(
            status_code=400,
            detail=(
                "This prototype can't assist with exploitative, coercive, or illegal work. "
                "It only supports grounded career guidance for legitimate roles and transitions."
            ),
        )
