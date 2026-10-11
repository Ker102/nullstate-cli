# Translation Maintenance

[English source](../../README.md) | [Español](es/README.md) |
[简体中文](zh-CN/README.md) | [Français](fr/README.md) |
[日本語](ja/README.md) | [Deutsch](de/README.md) |
[Português (Brasil)](pt-BR/README.md)

## Source of Truth

English files at their original repository paths are authoritative. Translations
are full document equivalents, not summaries or a separate product specification.
The mirror of `docs/runbook.md` in Spanish is
`docs/i18n/es/docs/runbook.md`. Run documented commands from the repository root,
not from a translated document's directory. Example fixtures, schemas, scripts,
and configuration remain at their original paths.

## Inventory and Coverage

`manifest.json` is the explicit inventory. It records every maintained public
Markdown source, its normalized SHA-256 hash, and a `complete` or `pending` entry
for each of `es`, `zh-CN`, `fr`, `ja`, `de`, and `pt-BR`. Complete entries include
the actual mirror path and mirror hash. Pending entries have no mirror path.
Absence from the complete set never means that a maintained source was translated.

Current reviewed coverage: 38 complete sources in each of the six locales,
228 mirrors total, with no pending maintained documents. The manifest and strict
repository test are authoritative for this count.

Scope includes the full README, contributor/security/community policies, changelog,
PR template, architecture and operational guides, public product/security
references, case-study material, ADRs, and all nine maintained example READMEs.
The README-linked external-agent trust design is included even though it lives
under `docs/plans/`; a folder name alone does not establish an exclusion.

Internal handoff/progress notes, the historical red-command implementation plan,
`docs/superpowers/` implementation plans/specs, and generated `examples/sample-runs/`
records remain in English. Their tracked Markdown paths and reasons are recorded
under `excluded`. Agent instructions, this task's internal planning artifacts,
private local evidence, ignored run directories, and vendor documentation are not
translation sources. Exclusion patterns describe these classes without ingesting
private local evidence.

`shared_assets` inventories authoritative schemas, workflow templates, the Mermaid
diagram, and legal texts. These are linked at their original locations, not copied
or translated into runnable lookalikes. Existing historical information inside a
maintained public guide is translated in full; it is not silently removed.

## Links and Literal Content

Link to the same-locale mirror when its inventory entry is complete. Otherwise
link explicitly to the original English document; this applies to untranslated
historical materials too. Rebase asset links to original repository assets.
Translated headings retain explicit English anchor IDs so existing fragment links
still resolve. README switchers use native language names and relative paths.

Keep fenced code (including comments, Mermaid, shell syntax, and info strings),
inline commands, API identifiers, environment names, versions, numeric literals,
and external URLs unchanged. Translate surrounding prose, headings, table labels,
and checklist descriptions without shortening the document or changing its claims.

## Local Validation

From the repository root:

```powershell
python scripts/docs/validate_i18n.py
python -m unittest discover -s tests -p test_i18n_docs.py -v
```

Existing PR checks already discover `tests/test_i18n_docs.py`. Its real-repository
test requires complete maintained coverage and loads the actual manifest and
mirrors, so stale English hashes, missing
completed mirrors, missing tracked source inventory, invalid links/anchors,
changed fences/code, and changed recorded translation hashes fail those checks.
No additional CI workflow is needed.

```powershell
python scripts/docs/validate_i18n.py --require-complete
```

This stricter check also fails when any maintained source/locale pair is pending.
The default check reports pending counts but does not falsely treat them as
complete. Validation is read-only, uses the project's Python runtime and standard
library, and never runs the commands quoted in documentation. It does not fetch
external URLs or claim any runtime, model, emulator, or cloud validation.

## Updating Translations

1. Change the authoritative English source first and run the validator. A source
   hash mismatch intentionally fails; do not merely update the hash to hide drift.
2. Review and update every completed mirror of that source. Preserve safety
   boundaries, certainty levels, and implementation-versus-roadmap distinctions.
3. When completing a previously pending document, update links in documents that
   linked to its English fallback. Maintain the English anchor IDs.
4. Recompute SHA-256 from UTF-8 text after replacing CRLF with LF, retaining the
   final newline. This makes hashes portable across Windows/Linux checkouts.
   Record source and mirror hashes only after review. Hashes include README
   switchers; code comparisons exclude the marked switcher blocks.
5. Update complete/pending entries truthfully, then run local tests and the strict
   check. A new tracked public Markdown source must be inventoried explicitly;
   assess exclusions by content and audience, not only by directory.

The parser supports the Markdown inline/reference/HTML links, backtick and tilde
fences used in this repository. Structural and literal checks catch omissions
and code drift, not translation semantics. Human review is still needed.

## Safety and Historical Claims

Maintain the distinction between live-validated LocalStack AWS, pending Azure
Emulator entitlement, offline deterministic evidence, and scaffolded adapters.
Built-in probes remain local/offline; future non-local HTTP(S) probes need explicit
`--allow-live-cloud` approval and applicable policy allowlists. `--offline` controls
Terraform/cloud execution, not configured model calls; `--mock-agents` disables
model calls. Upload dry-run prepares a plan without sending data.

English sources currently contain historical inconsistencies: some example
READMEs still call AWS scaffolded and name Azure as the working V1 loop, while the
main README records live-validated AWS and pending Azure. The security-model and
cost-report offline/no-model statements must be read alongside the main README
and runbook's explicit `--offline`/`--mock-agents` distinction. Translations retain
the source claims, not fabricated corrections or new validation. Fix such issues
in English first, then propagate them through the hash-based review process.
