# Eval Baseline Comparison Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and superpowers:verification-before-completion for this batch.

**Goal:** Extend `nullstate eval` so case-study reports can compare Nullstate's evidence output against a transparent baseline such as a generic IaC-only review.

**Architecture:** Keep the first comparator deterministic and local. Eval cases may define a `baseline` object describing what a conventional IaC-only review is expected to provide. `run_eval_suite()` should calculate per-case `comparison` fields and aggregate `totals.comparison` without invoking external tools yet. This gives the case study measurable deltas without making unsupported claims about third-party scanners.

## Scope

- Add optional `baseline` to eval cases.
- Calculate whether Nullstate adds:
  - runtime attack evidence
  - post-remediation validation
  - structured artifacts
  - token/runtime metrics
- Render comparison rows in `eval-report.md`.
- Document that external scanner/coding-agent baselines remain future integrations.

## Validation

- `python -m unittest tests.test_evaluation -v`
- `python -m unittest tests.test_github_workflows tests.test_evaluation -v`
- `python -m ruff check src tests`
- `python -m mypy src`
- `python -m unittest discover -s tests -v`
