"""Typed browser actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ActionType(StrEnum):
    """Supported action kinds."""

    GOTO = "goto"
    CLICK = "click"
    FILL = "fill"
    EXTRACT = "extract"
    SUBMIT = "submit"


@dataclass
class Action:
    """One planner step."""

    type: ActionType
    target: str = ""
    value: str = ""
    meta: dict[str, str] = field(default_factory=dict)


@dataclass
class StepResult:
    """Result of executing one action."""

    action: Action
    ok: bool
    detail: str = ""
    extracted: str = ""
