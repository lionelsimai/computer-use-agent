"""Tests for computer-use-agent."""
from __future__ import annotations

from pathlib import Path

import pytest

from computer_use_agent.agent import ComputerUseAgent
from computer_use_agent.browser import LocalBrowser, playwright_available
from computer_use_agent.cli import fixture_dir, main
from computer_use_agent.planner import Planner
from computer_use_agent.takeover import TakeoverDetector
from computer_use_agent.tracker import SuccessTracker, TaskRecord


@pytest.fixture()
def site() -> Path:
    return fixture_dir()

def test_planner_booking() -> None:
    plan = Planner().plan("Book a table for Alex Tan for 2 guests")
    kinds = [a.type.value for a in plan]
    assert kinds[0] == "goto" and "fill" in kinds and "submit" in kinds

def test_planner_extract() -> None:
    plan = Planner().plan("Extract the price")
    assert any(a.type.value == "extract" for a in plan)

def test_browser_goto_and_text(site: Path) -> None:
    from computer_use_agent.actions import Action, ActionType
    b = LocalBrowser(site)
    r = b.execute(Action(ActionType.GOTO, "index.html"))
    assert r.ok and "Fixture Bistro" in b.page_text

def test_booking_e2e(site: Path, tmp_path: Path) -> None:
    agent = ComputerUseAgent(site, handoff_path=tmp_path / "h.json")
    out = agent.run("Book a table for Alex Tan for 2 guests")
    assert out.success and "confirmed" in out.extracted.lower()

def test_extract_price(site: Path) -> None:
    agent = ComputerUseAgent(site)
    out = agent.run("Extract the price from the menu")
    assert out.success

def test_takeover_captcha(site: Path, tmp_path: Path) -> None:
    handoff = tmp_path / "handoff.json"
    agent = ComputerUseAgent(site, handoff_path=handoff)
    out = agent.run("Open the captcha page")
    assert out.takeover and out.takeover_reason == "captcha"
    assert handoff.exists()

def test_detector_login() -> None:
    ev = TakeoverDetector().inspect('<input type="password">', "login.html")
    assert ev is not None and ev.reason == "login_wall"

def test_detector_clean_page() -> None:
    assert TakeoverDetector().inspect("<p>Hello, welcome</p>", "x") is None

def test_detector_empty_is_unknown() -> None:
    ev = TakeoverDetector().inspect("   ", "x")
    assert ev is not None and ev.reason == "unknown_state"

def test_tracker_rates(tmp_path: Path) -> None:
    t = SuccessTracker(tmp_path / "t.json")
    t.record(TaskRecord("a", True))
    t.record(TaskRecord("b", False, takeover=True))
    assert t.success_rate == 0.5 and t.takeover_rate == 0.5

def test_tracker_empty_rates() -> None:
    t = SuccessTracker()
    assert t.success_rate == 0.0 and t.takeover_rate == 0.0

def test_edge_missing_page(site: Path) -> None:
    from computer_use_agent.actions import Action, ActionType
    b = LocalBrowser(site)
    r = b.execute(Action(ActionType.GOTO, "nope.html"))
    assert not r.ok

def test_playwright_flag_is_bool() -> None:
    assert isinstance(playwright_available(), bool)

def test_cli_demo_e2e(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "success_rate" in out and "TAKEOVER" in out

def test_cli_run_e2e(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "Book a table for Alex Tan for 2 guests"]) == 0
    assert "success: True" in capsys.readouterr().out
