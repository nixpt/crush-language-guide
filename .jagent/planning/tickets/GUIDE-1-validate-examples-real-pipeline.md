# GUIDE-1 — Validate every guide example through the real pipeline

**Status**: Backlog · **Priority**: P1

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
