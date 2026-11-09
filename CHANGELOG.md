# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-11-09

World-class remediation after an adversarial audit (was scored 4/10, FIX).

### Honesty
- Removed all "on live sites" and Playwright-backend claims from the
  README, docs and packaging. The project is repositioned accurately
  as an offline fixture-site agent core with a defined
  `BrowserAdapter` interface; no live-browser code ships. The unused
  `playwright` optional-dependency was removed from pyproject.

### Fixed
- CLICK on a missing link now returns `ok=False` (was a silent
  "success" no-op).
- SUBMIT validates required fields and derives the confirmation from
  the submitted values; a cold submit of an empty form now fails.
- EXTRACT of a missing target returns `ok=False` instead of returning
  the whole page as a "successful" extraction.
- The planner no longer fabricates a guest name / party size: booking
  tasks missing either now fail with PlanningError.
- Page loading is jailed to the fixture directory via
  `Path.is_relative_to`; `/etc/...` and `../` escapes are refused.
- Takeover handoff and tracker are persisted to a real `--out-dir`
  (default `./agent-output`) instead of a TemporaryDirectory that was
  deleted when the CLI exited.

### Changed
- Benchmark no longer double-counts the extract task: 4 genuine tasks
  counted once — genuine success 1.00, overall incl. captcha probe
  0.80, takeover incl. probe 0.20 (was: 6 counted tasks, success 0.83,
  takeover 0.17, "genuine" 1.00 over a duplicated set).
- Added tests/test_remediation.py with one test per fix above. All
  pre-existing tests pass unmodified.

## [0.1.0] - 2026-11-09

### Added
- Initial public release: core engine, CLI, offline demo, tests, benchmarks, CI.
