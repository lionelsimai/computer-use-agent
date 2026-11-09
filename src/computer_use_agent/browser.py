"""Offline browser core over local HTML fixtures.

This is the ONLY browser implementation that ships in this package.
It uses the standard library to parse static fixture HTML — there is
no network code, no JavaScript, and no live-browser backend.

Adapter interface: any future live-browser adapter must implement the
same contract as :class:`LocalBrowser` — ``execute(Action) ->
StepResult`` plus ``page_text`` — so the planner, takeover detector
and tracker can be reused unchanged. No such adapter exists today;
claims otherwise in older docs were removed in 0.1.1.

All page loads are jailed to the fixture directory via
``Path.is_relative_to``: absolute paths and ``../`` escapes are refused.
"""

from __future__ import annotations

import re
from html import escape as html_escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol

from computer_use_agent.actions import Action, ActionType, StepResult
from computer_use_agent.errors import ActionFailedError, TakeoverRequiredError
from computer_use_agent.takeover import TakeoverDetector

#: Fields the fixture booking form requires before a submit is accepted.
REQUIRED_FORM_FIELDS: tuple[str, ...] = ("name", "guests")


class BrowserAdapter(Protocol):
    """The adapter interface a browser backend must implement."""

    def execute(self, action: Action) -> StepResult:
        """Execute one action and return its result."""
        ...


def playwright_available() -> bool:
    """Informational only: is the Playwright package importable?

    This project ships NO Playwright backend; the flag exists so users
    are not misled into thinking an installed package is being used.
    """
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return True


class _PageParser(HTMLParser):
    """Collect text, links, inputs and element text by id."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self.links: dict[str, str] = {}
        self.inputs: list[str] = []
        self.by_id: dict[str, str] = {}
        self._cur_id: str | None = None
        self._cur_link: str | None = None
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs)
        if tag == "a" and d.get("href"):
            self._cur_link = d["href"]
        if tag == "input" and d.get("name"):
            self.inputs.append(str(d["name"]))
        if d.get("id"):
            self._cur_id = str(d["id"])
            self._buf = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.text_parts.append(text)
            self._buf.append(text)

    def handle_endtag(self, tag: str) -> None:
        if self._cur_id:
            self.by_id[self._cur_id] = " ".join(self._buf)
            self._cur_id = None
        if tag == "a" and self._cur_link:
            self.links[" ".join(self._buf).lower()] = self._cur_link
            self._cur_link = None


class LocalBrowser:
    """A deterministic browser over a directory of HTML fixture pages."""

    def __init__(self, site_dir: Path, detector: TakeoverDetector | None = None) -> None:
        self.site_dir = Path(site_dir)
        self.detector = detector or TakeoverDetector()
        self.current_url = ""
        self.html = ""
        self.parser = _PageParser()
        self.form_values: dict[str, str] = {}
        self.visited: list[str] = []

    def _resolve_page(self, page: str) -> Path:
        """Resolve a page inside the fixture dir or raise (jail)."""
        base = self.site_dir.resolve()
        target = (base / page).resolve()
        if not target.is_relative_to(base):
            raise ActionFailedError(f"page escapes site directory: {page!r}")
        return target

    def _load(self, page: str) -> None:
        path = self._resolve_page(page)
        if not path.exists():
            raise ActionFailedError(f"page not found: {page}")
        self.html = path.read_text(encoding="utf-8")
        self.current_url = page
        self.visited.append(page)
        self.parser = _PageParser()
        self.parser.feed(self.html)
        event = self.detector.inspect(self.html, page)
        if event is not None:
            raise TakeoverRequiredError(event.reason, page)

    def _submit(self, action: Action) -> StepResult:
        """Validate required fields, then derive a confirmation from the
        submitted values (never a canned success for an empty form)."""
        missing = [f for f in REQUIRED_FORM_FIELDS if not self.form_values.get(f)]
        if missing:
            return StepResult(
                action, False, f"missing required fields: {', '.join(missing)}"
            )
        name = self.form_values["name"]
        guests = self.form_values["guests"]
        detail = f"Booking confirmed for {name} - {guests} guests"
        page = action.target or "confirmation.html"
        self.html = (
            f'<html><body><p id="confirmation">'
            f"Booking confirmed for {html_escape(name)} - {html_escape(guests)} guests"
            f"</p></body></html>"
        )
        self.current_url = page
        self.visited.append(page)
        self.parser = _PageParser()
        self.parser.feed(self.html)
        return StepResult(action, True, f"submitted for {name}", extracted=detail)

    def execute(self, action: Action) -> StepResult:
        """Execute one action and return its result."""
        try:
            if action.type == ActionType.GOTO:
                self._load(action.target)
                return StepResult(action, True, f"loaded {action.target}")
            if action.type == ActionType.FILL:
                if action.target not in self.parser.inputs:
                    return StepResult(action, False, f"no input named {action.target!r}")
                self.form_values[action.target] = action.value
                return StepResult(action, True, f"filled {action.target}")
            if action.type == ActionType.CLICK:
                key = action.target.lower()
                href = self.parser.links.get(key)
                if href is None:
                    for text, link in self.parser.links.items():
                        if key in text:
                            href = link
                            break
                if href:
                    self._load(href)
                    return StepResult(action, True, f"clicked through to {href}")
                return StepResult(
                    action, False,
                    f"no link matching {action.target!r} on {self.current_url or 'no page'}",
                )
            if action.type == ActionType.SUBMIT:
                return self._submit(action)
            if action.type == ActionType.EXTRACT:
                value = self.parser.by_id.get(action.target, "")
                if not value:
                    match = re.search(rf"{re.escape(action.target)}[:\s]*([^<\n]+)", self.html)
                    value = match.group(1).strip() if match else ""
                if not value:
                    return StepResult(
                        action, False, f"nothing to extract for {action.target!r}"
                    )
                return StepResult(action, True, f"extracted {action.target}", extracted=value)
        except TakeoverRequiredError:
            raise
        except ActionFailedError as exc:
            return StepResult(action, False, str(exc))
        return StepResult(action, False, f"unsupported action {action.type}")

    @property
    def page_text(self) -> str:
        """Visible text of the current page."""
        return " ".join(self.parser.text_parts)
