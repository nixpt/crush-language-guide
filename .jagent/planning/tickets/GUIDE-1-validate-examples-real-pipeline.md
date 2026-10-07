# GUIDE-1 — Validate every guide example through the real pipeline

**Status**: Done (PR #1, panini) · **Priority**: P1

crush-ast has a documented pattern of syntax that exists in docs/grammars but
not in the real parser (lambdas were unparseable for months while
test_lambda.crush documented them — CRUSH-75). A language guide that shows
unrunnable code is worse than none. Ticket: extract every code block, run each
through the REAL crush-ast pipeline (parse → compile → execute where
self-contained), fix or annotate the failures, and wire the extraction as a CI
check so the guide can't rot again. Bonus: passing examples become seed
fixtures for crush-ast's conformance corpus (CRUSH-73) — coordinate.

## Done
- [ ] Every example verified (green, fixed, or explicitly marked not-yet-implemented with the crush-ast ticket ref)
- [ ] CI extraction check live; corpus handoff noted in CRUSH-73

## Outcome (GUIDE-3, 2026-10-07)

- `scripts/check-examples.py` extracts and runs every ```crush block through `crushc -C` + `crush-run`, plus ```casm text assembly, JSON CASM/CAST blocks (via `scripts/casm-check`), and the `rust,no_run` embedding examples against a crush-ast checkout. See `scripts/README.md`.
- Final run against crush-ast `v0.3.9`: **181 blocks, 165 green, 15 marked not-yet-implemented (each cites a CRUSH ticket or a GAP-* id), 1 skipped (needs a `sandboxed-polyglot` build)**, 0 failing.
- **CI decision:** not wired. The checker needs a crush-ast build, and crush-ast's `crush-vm` has a path dependency on the private `buckets` repo that GitHub-hosted CI here cannot fetch. It is documented as a local check; wire it once crush-vm builds without `../buckets` or CI gets a deploy key.
- Seed fixtures for crush-ast's conformance corpus (CRUSH-73): the ```crush blocks with `<!-- check: output -->` pairs are self-contained programs with expected stdout.
