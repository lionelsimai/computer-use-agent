"""Benchmark: task success + takeover rate on the fixture site.

Run: python benchmarks/bench.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from computer_use_agent.agent import ComputerUseAgent
from computer_use_agent.cli import DEMO_TASKS, fixture_dir
from computer_use_agent.tracker import SuccessTracker


def main() -> int:
    """Run fixture tasks and print headline metrics."""
    tracker = SuccessTracker()
    with tempfile.TemporaryDirectory() as tmp:
        agent = ComputerUseAgent(fixture_dir(), tracker=tracker,
                                 handoff_path=Path(tmp) / "h.json")
        tasks = [*DEMO_TASKS, "Extract the price from the menu",
                 "Book a table for John Lee for 3 guests"]
        for task in tasks:
            agent.run(task)
        agent.run("Open the captcha page")  # expected takeover, not a failure of design
    total = len(tracker.records)
    print(f"fixture_tasks: {total}")
    print(f"success_rate: {tracker.success_rate:.2f}")
    print(f"takeover_rate: {tracker.takeover_rate:.2f}")
    print("target: 90% task success, human takeover under 10% on real sites;")
    print("fixture run separates genuine tasks from the deliberate captcha probe.")
    genuine = tracker.records[:-1]
    rate = sum(int(r.success) for r in genuine) / max(len(genuine), 1)
    print(f"genuine_task_success_rate: {rate:.2f}")
    return 0 if rate >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
