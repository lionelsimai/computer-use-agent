"""Agent orchestration: planner -> browser -> tracker, with takeover."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from computer_use_agent.actions import StepResult
from computer_use_agent.browser import LocalBrowser
from computer_use_agent.errors import TakeoverRequiredError
from computer_use_agent.planner import Planner
from computer_use_agent.takeover import TakeoverDetector
from computer_use_agent.tracker import SuccessTracker, TaskRecord


@dataclass
class AgentOutcome:
    """Outcome of one agent task."""

    task: str
    success: bool
    takeover: bool = False
    takeover_reason: str = ""
    steps: list[StepResult] = field(default_factory=list)
    extracted: str = ""


class ComputerUseAgent:
    """Run planned browser tasks against a site directory."""

    def __init__(self, site_dir: Path, tracker: SuccessTracker | None = None,
                 handoff_path: Path | None = None) -> None:
        self.browser = LocalBrowser(site_dir)
        self.planner = Planner()
        self.tracker = tracker or SuccessTracker()
        self.handoff_path = handoff_path

    def run(self, task: str) -> AgentOutcome:
        """Execute a task end to end, recording the outcome."""
        steps: list[StepResult] = []
        extracted = ""
        try:
            for action in self.planner.plan(task):
                result = self.browser.execute(action)
                steps.append(result)
                if result.extracted:
                    extracted = result.extracted
                if not result.ok:
                    self.tracker.record(TaskRecord(task, False, steps=len(steps)))
                    return AgentOutcome(task, False, steps=steps, extracted=extracted)
            self.tracker.record(TaskRecord(task, True, steps=len(steps)))
            return AgentOutcome(task, True, steps=steps, extracted=extracted)
        except TakeoverRequiredError as exc:
            event = TakeoverDetector().inspect(self.browser.html or "captcha", exc.url)
            if event is not None and self.handoff_path is not None:
                TakeoverDetector.write_handoff(event, self.handoff_path)
            self.tracker.record(TaskRecord(task, False, takeover=True, steps=len(steps)))
            return AgentOutcome(task, False, takeover=True, takeover_reason=exc.reason,
                                steps=steps, extracted=extracted)
