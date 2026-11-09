# Architecture

## Components
- `planner.Planner` — deterministic task text -> Action list (LLM planner can replace it).
- `browser.LocalBrowser` — stdlib HTML browser over fixture pages; Playwright is an
  optional backend sharing the same Action vocabulary.
- `takeover.TakeoverDetector` — captcha / login-wall / 2FA / empty-state detection,
  writes a JSON handoff file for a human operator.
- `tracker.SuccessTracker` — success and takeover rates, persisted as JSON.
- `agent.ComputerUseAgent` — orchestration and outcome recording.

## Flow
Task -> plan -> execute steps -> detector checks every page load -> success,
failure, or takeover handoff. Takeovers are a designed outcome, not a crash.
