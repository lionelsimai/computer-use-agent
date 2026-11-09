"""Remediation tests (0.1.1): one per audit fix for computer-use-agent."""
from __future__ import annotations

from pathlib import Path

import pytest

from computer_use_agent.actions import Action, ActionType
from computer_use_agent.agent import ComputerUseAgent
from computer_use_agent.browser import LocalBrowser
from computer_use_agent.cli import fixture_dir, main
from computer_use_agent.errors import PlanningError
from computer_use_agent.planner import Planner


@pytest.fixture()
def site() -> Path:
    return fixture_dir()


def test_click_missing_link_fails(site: Path) -> None:
    b = LocalBrowser(site)
    assert b.execute(Action(ActionType.GOTO, "index.html")).ok
    r = b.execute(Action(ActionType.CLICK, "nonexistent-link"))
    assert not r.ok


def test_submit_requires_filled_fields(site: Path) -> None:
    b = LocalBrowser(site)
    assert b.execute(Action(ActionType.GOTO, "booking.html")).ok
    r = b.execute(Action(ActionType.SUBMIT, "confirmation.html"))
    assert not r.ok and "missing required fields" in r.detail


def test_submit_confirmation_derives_from_values(site: Path) -> None:
    b = LocalBrowser(site)
    assert b.execute(Action(ActionType.GOTO, "booking.html")).ok
    assert b.execute(Action(ActionType.FILL, "name", "Priya Nair")).ok
    assert b.execute(Action(ActionType.FILL, "guests", "5")).ok
    r = b.execute(Action(ActionType.SUBMIT, "confirmation.html"))
    assert r.ok and "Priya Nair" in r.extracted and "5 guests" in r.extracted


def test_planner_never_invents_name_or_guests() -> None:
    with pytest.raises(PlanningError):
        Planner().plan("Book a table for 2 guests")  # no name given
    with pytest.raises(PlanningError):
        Planner().plan("Book a table for Alex Tan")  # no guest count given


def test_agent_task_without_name_fails_honestly(site: Path) -> None:
    out = ComputerUseAgent(site).run("Book a table for 2 guests")
    assert out.success is False and "invent" in out.error


@pytest.mark.parametrize("page", ["../README.md", "../../etc/passwd", "/etc/passwd"])
def test_jail_escape_blocked(site: Path, page: str) -> None:
    b = LocalBrowser(site)
    r = b.execute(Action(ActionType.GOTO, page))
    assert not r.ok


def test_extract_missing_target_fails(site: Path) -> None:
    b = LocalBrowser(site)
    assert b.execute(Action(ActionType.GOTO, "index.html")).ok
    r = b.execute(Action(ActionType.EXTRACT, "opening-hours"))
    assert not r.ok and r.extracted == ""


def test_handoff_and_tracker_persist_to_out_dir(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    code = main(["run", "Open the captcha page", "--out-dir", str(out_dir)])
    assert code == 0  # takeover is a designed outcome
    assert (out_dir / "handoff.json").exists()
    assert (out_dir / "tracker.json").exists()


def test_no_live_site_claims_in_packaging() -> None:
    root = fixture_dir().parents[2]
    readme = (root / "README.md").read_text(encoding="utf-8").lower()
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8").lower()
    assert "on live sites" not in readme
    assert "playwright" not in pyproject
