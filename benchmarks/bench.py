"""Benchmark: task success + takeover rate on the fixture site.

Run: python benchmarks/bench.py

Genuine tasks are counted once each (no duplicates). The captcha probe
is reported separately: it is an expected takeover, and folding it into
the success rate without saying so would flatter the number.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from computer_use_agent.agent import ComputerUseAgent
from computer_use_agent.cli import DEMO_TASKS, fixture_dir
from computer_use_agent.tracker import SuccessTracker

GENUINE_TASKS: list[str] = [*DEMO_TASKS, "Book a table for John Lee for 3 guests"]


def main() -> int:
    """Run fixture tasks and print headline metrics."""
    tracker = SuccessTracker()
    with tempfile.TemporaryDirectory() as tmp:
        agent = ComputerUseAgent(fixture_dir(), tracker=tracker,
                                 handoff_path=Path(tmp) / "h.json")
        for task in GENUINE_TASKS:
            agent.run(task)
        genuine = list(tracker.records)
        agent.run("Open the captcha page")  # deliberate takeover probe
    genuine_rate = sum(int(r.success) for r in genuine) / max(len(genuine), 1)
    print(f"genuine_tasks: {len(genuine)}")
    print(f"genuine_task_success_rate: {genuine_rate:.2f}")
    print(f"overall_success_rate_incl_probe: {tracker.success_rate:.2f}")
    print(f"takeover_rate_incl_probe: {tracker.takeover_rate:.2f}")
    print("note: fixture-site numbers only; no live-site measurement exists yet.")
    print("target (aspirational, for a future live adapter): 90% success, <10% takeover.")
    return 0 if genuine_rate >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
