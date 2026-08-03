# GUIDE-2 — Document the polyglot lanes (deps, sandbox, timeouts, errors)

**Status**: Backlog · **Priority**: P2

The polyglot surface shipped in crush-ast s390 (CRUSH-18/19/20) is
user-facing and undocumented here: `@lang { }` blocks, `@lang[deps]`
annotation syntax, the sandboxed-polyglot lane (buckets/bwrap, off by
default), guest-error semantics (`LangRuntimeError` with crush line numbers),
and wall-clock timeout behavior. Write the chapter from the shipped behavior
(cite the crush-ast tickets), with runnable examples that GUIDE-1's CI check
covers.

## Done
- [ ] Chapter merged; examples pass the GUIDE-1 check
