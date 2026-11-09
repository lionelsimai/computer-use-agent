"""Command-line interface for computer-use-agent."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from computer_use_agent.agent import ComputerUseAgent
from computer_use_agent.tracker import SuccessTracker

FIXTURE_DIR = Path(__file__).resolve().parent / "fixture_site"
DEMO_TASKS: list[str] = [
    "Book a table for Alex Tan for 2 guests",
    "Extract the price from the menu",
    "Book a table for Maria Lim for 4 guests",
]


def fixture_dir() -> Path:
    """Locate the bundled fixture site, falling back to examples/."""
    if FIXTURE_DIR.exists():
        return FIXTURE_DIR
    alt = Path(__file__).resolve().parents[2] / "examples/fixture_site"
    return alt


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(prog="computer-use-agent", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="Run one task against the fixture site")
    run_p.add_argument("task")
    run_p.add_argument("--site", default=None)
    sub.add_parser("demo", help="Run the offline demo (fixture site, no network)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = build_parser().parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp:
        handoff = Path(tmp) / "handoff.json"
        tracker = SuccessTracker()
        if args.cmd == "demo":
            agent = ComputerUseAgent(fixture_dir(), tracker=tracker, handoff_path=handoff)
            for task in DEMO_TASKS:
                outcome = agent.run(task)
                status = "PASS" if outcome.success else "FAIL"
                print(f"[{status}] {task} steps={len(outcome.steps)} extracted={outcome.extracted!r}")
            blocked = agent.run("Open the captcha page")
            print(f"[TAKEOVER] captcha task takeover={blocked.takeover} reason={blocked.takeover_reason!r}")
            print(f"success_rate: {tracker.success_rate:.2f} takeover_rate: {tracker.takeover_rate:.2f}")
            print(json.dumps({"success_rate": tracker.success_rate,
                              "takeover_rate": tracker.takeover_rate}))
            return 0
        agent = ComputerUseAgent(
            Path(args.site) if args.site else fixture_dir(),
            tracker=tracker, handoff_path=handoff,
        )
        outcome = agent.run(args.task)
        print(f"task: {args.task}")
        print(f"success: {outcome.success} takeover: {outcome.takeover}")
        print(f"extracted: {outcome.extracted}")
        for step in outcome.steps:
            print(f"  {step.action.type.value} {step.action.target} ok={step.ok} {step.detail}")
        return 0 if outcome.success or outcome.takeover else 1


if __name__ == "__main__":
    sys.exit(main())
