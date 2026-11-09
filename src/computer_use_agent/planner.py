"""Rule-based planner: task text -> action list (no LLM needed offline)."""

from __future__ import annotations

import re

from computer_use_agent.actions import Action, ActionType


class Planner:
    """Plan fixture-site tasks deterministically.

    Recognises booking and extraction intents; unknown tasks fall back to a
    goto + extract plan so the agent still does something inspectable.
    """

    def plan(self, task: str, start_page: str = "index.html") -> list[Action]:
        """Return the action list for a natural-language task."""
        low = task.lower()
        name_match = re.search(r"for ([A-Z][a-z]+(?: [A-Z][a-z]+)?)", task)
        name = name_match.group(1) if name_match else "Alex Tan"
        guests_match = re.search(r"(\d+)\s*(?:guest|people|person)", low)
        guests = guests_match.group(1) if guests_match else "2"
        if "book" in low or "reserve" in low:
            return [
                Action(ActionType.GOTO, start_page),
                Action(ActionType.CLICK, "book"),
                Action(ActionType.FILL, "name", name),
                Action(ActionType.FILL, "guests", guests),
                Action(ActionType.SUBMIT, "confirmation.html"),
                Action(ActionType.EXTRACT, "confirmation"),
            ]
        if "extract" in low or "price" in low or "find" in low:
            return [
                Action(ActionType.GOTO, start_page),
                Action(ActionType.EXTRACT, "price"),
            ]
        if "captcha" in low or "login" in low:
            page = "captcha.html" if "captcha" in low else "login.html"
            return [Action(ActionType.GOTO, page)]
        return [Action(ActionType.GOTO, start_page), Action(ActionType.EXTRACT, "title")]
