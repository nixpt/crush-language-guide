# GUIDE-2 — Document the polyglot lanes (deps, sandbox, timeouts, errors)

**Status**: Done (PR #1, panini) · **Priority**: P2

The polyglot surface shipped in crush-ast s390 (CRUSH-18/19/20) is
user-facing and undocumented here: `@lang { }` blocks, `@lang[deps]`
annotation syntax, the sandboxed-polyglot lane (buckets/bwrap, off by
default), guest-error semantics (`LangRuntimeError` with crush line numbers),
and wall-clock timeout behavior. Write the chapter from the shipped behavior
(cite the crush-ast tickets), with runnable examples that GUIDE-1's CI check
covers.

## Done
- [ ] Chapter merged; examples pass the GUIDE-1 check

## Outcome (GUIDE-3, 2026-10-07)

`src/crush/polyglot.md` rewritten from verified behaviour: lanes are python / javascript / bash only, run as host subprocesses behind `--polyglot` (no WASM, no `@rust`/`@c`/`@go`/`@zig`/`@wasm` executors), guest errors surface as `LangRuntimeError` with the `.crush` line, the 30 s wall-clock quota kills the process group, and the `@lang[deps]` + bwrap/buckets sandbox is a Linux-only opt-in build feature of crush-vm (`sandboxed-polyglot`), not an SDK feature. All runnable examples are covered by the GUIDE-1 checker.
