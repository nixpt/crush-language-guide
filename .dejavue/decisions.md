# Decisions


## 2026-06-12T04:41:58-05:00 — [ADOPTED] Standalone doc repo for Crush (Language+CAST+CASM only)

Reason:
Exosphere book buried Crush docs inside a larger book; scope is language-only, not unarchiving old crush-language repo which had more than docs


## 2026-06-12T04:42:00-05:00 — [VERIFIED] Docs audited against exosphere source 2026-06-12

Reason:
crushed-book had ~12 categories of errors: keywords list incomplete (21 vs 28), try/catch/structs/match/lambdas falsely marked Future Feature, range() not ..., closures syntax wrong, Bash walker falsely presented as a real walker


## 2026-10-08T16:08:34-05:00 — Chapter notebooks: crush cells verbatim; only expected-failure cells wrapped in fn main; files generated into book/notebooks after mdbook build, never committed

Reason:
crush-notebook >=0.1.1 shares lets/fns/structs across cells, so a session name can mask the error an expected-failure example demonstrates (variables.md:128 ran without the wrapper); standalone fn main programs don't see session vars. Generated files can't drift from the guide; link paths come from mdbook-crush-run.notebook_path.


## 2026-10-16T03:17:47-05:00 — [STRATEGIC] [VERIFIED] Verified corpus + pinned crush-ast commit; CI builds crush-ast and runs it

Reason:
Every language claim must come from a program that was run. examples/verified/<area>/NAME.crush with .out/.err/.flags/.stdin/.needs sidecars, run by scripts/verify-examples; CRUSH_AST_COMMIT pins the crush-ast commit the guide is verified against, and the gh-pages 'verify' job builds that commit (buckets is now public) and runs the corpus plus check-examples.py. PITFALL programs encode wrong-today behaviour with the crush-ast issue, so a fix flips them red and forces a doc update.

Rejected alternatives:
- **local-only checking:scripts/README said buckets was private; it is public now, so CI can build crush-ast**
- **pin to crates.io 0.6.0:predates Records/@kind, -> outputs, AOT refusals**


## 2026-10-16T03:17:47-05:00 — [TACTICAL] [ADOPTED] Notebooks CI job non-blocking until crush-notebook-kernel moves past crush-ast 0.3.x

Reason:
crush-notebook-kernel 0.1.1 (latest on crates.io) depends on crush-* ^0.3.9, so cells using closures, struct methods, green tasks or -> outputs fail in it even though the pinned crush-ast runs them; the verify job is the authority. Revert continue-on-error once a kernel on the pinned crush-ast is published.


## 2026-10-16T03:17:47-05:00 — [TACTICAL] [VERIFIED] Vendored crush-web rebuilt at the pinned crush-ast commit; standard library is browser-runnable

Reason:
Browser classification must match the commit the guide documents. crush-web at 3ae0b4a registers the default-on stdlib, so STDLIB host-needs is empty; crypto and file text.* are host caps. check-browser.mjs proves every label (129 run, 24 host, 36 fail).

