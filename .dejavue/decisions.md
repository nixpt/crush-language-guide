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

