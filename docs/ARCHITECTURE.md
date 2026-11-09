# Architecture

## Components
- `planner.Planner` — deterministic task text -> Action list. Refuses
  (PlanningError) rather than inventing missing booking details. An LLM
  planner could replace it behind the same interface.
- `browser.BrowserAdapter` — the interface a browser backend must
  implement: `execute(Action) -> StepResult` and `page_text`.
- `browser.LocalBrowser` — the ONLY backend that ships: a stdlib HTML
  parser over fixture pages, jailed to the fixture directory. There is
  no Playwright or network backend in this repository.
- `takeover.TakeoverDetector` — captcha / login-wall / 2FA / empty-state
  detection, writes a JSON handoff file for a human operator.
- `tracker.SuccessTracker` — success and takeover rates, persisted as
  JSON to the CLI's `--out-dir`.
- `agent.ComputerUseAgent` — orchestration and outcome recording.

## Flow
Task -> plan -> execute steps -> detector checks every page load ->
success, failure, or takeover handoff. Takeovers are a designed
outcome, not a crash. Actions are honest: a click/submit/extract that
did not actually happen returns `ok=False`.
