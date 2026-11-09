"""Structured errors."""

from __future__ import annotations


class ComputerUseError(Exception):
    """Base error."""


class TakeoverRequiredError(ComputerUseError):
    """Raised when a human must take over (captcha, login wall, unknown state)."""

    def __init__(self, reason: str, url: str = "") -> None:
        super().__init__(f"Human takeover required ({reason}) at {url or 'unknown page'}")
        self.reason = reason
        self.url = url


class ActionFailedError(ComputerUseError):
    """Raised when an action cannot be completed."""


class PlanningError(ComputerUseError):
    """Raised when a task cannot be planned without inventing details."""
