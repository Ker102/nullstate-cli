# Public Documentation Translation Implementation Plan

**Goal:** Faithful, auditable multilingual public documentation.
**Architecture:** Repo-relative mirrors, explicit inventory, English fallback links,
and read-only local validation. No CLI implementation changes.
**Tech Stack:** Existing Python runtime and unittest; Python standard library only.

1. [x] Inspect inherited instructions, git status, tracked Markdown, and runtime.
2. [x] Read README and primary operational/security guides; classify public and
   excluded materials. Initial checkout is clean on `docs/open-source-readiness`.
3. [x] Add validator in `scripts/docs/validate_i18n.py` and focused tests in
   `tests/test_i18n_docs.py`; test missing mirrors, link rewrites, code/fence drift,
   source hash drift, and honest pending coverage without executing CLI commands.
4. [x] Translate full README and core security/contribution/operational docs in six
   locales using apply_patch; retain source anchors and literal executable content.
5. [x] Extend to all maintained public references/examples; inventory any
   remaining maintained documents as pending, never silently excluded.
6. [x] Add English/native README switchers, `docs/i18n/README.md`, and
   `docs/i18n/manifest.json` with normalized SHA-256 source hashes and actual mirrors.
7. [x] Run local validator, unittest, lint/diff checks, safety wording review,
   inventory reconciliation, and final git status. Report per-locale counts/gaps.

Risks: translated headings break anchors; code snippets become accidentally
localized; relative assets resolve under the mirror instead of the source tree;
future product intentions become present capabilities. Preserve explicit source
anchors, compare protected code/URLs, resolve links to mirrors only when completed,
and review local-only/live-cloud and offline/model boundaries in each language.

Publication checkpoint: on 2026-10-11 the owner authorized a scoped documentation
commit and publication of the existing readiness branch as a pull request. Its
18 prior development commits remain reviewable rather than merged automatically.

Integration: 38 maintained sources across six locales, including the public
external-agent design under docs/plans. Product-validation-model and technical-
walkthrough mirrors were supplied by the parent's two helpers, then integrated
with independently computed current hashes. All other mirrors were completed
here. Strict real-repository tests require every maintained mirror.

Final verification: 228 complete mirrors; 38 sources per locale; zero pending.
`python scripts/docs/validate_i18n.py --require-complete` passed.
All 7 focused unittest tests passed, including strict real-repository validation.
Ruff passed for the validator and tests; `git diff --check` passed. The index is
empty. No software or workflow behavior changed. No attack, deployment, model,
emulator, or live-cloud commands were executed. The full application test suite
was not run; validation remained confined to documentation checks.
