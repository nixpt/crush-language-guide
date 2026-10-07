# GUIDE-3 — Sync the guide with crush-ast `main` (folds in GUIDE-1, GUIDE-2)

**Status**: Done (PR #1, panini) · **Priority**: P1 · **Branch**: `agent/panini/GUIDE-3`
**Validated against**: crush-ast `v0.3.9` (`4034d92`, the crates.io release; the first pass ran against `4e9c388`),
built with `cargo build -p crush-lang-sdk --features stdlib,net,db,graphics`.

The guide was last touched 2026-08-02. This ticket records what had drifted
(Step 1 audit), then tracks the fixes. Evidence column cites crush-ast paths
(all relative to the crush-ast repo root) or a probe run against the binary.

## Method

- `scripts/check-examples.py` extracts every ```` ```crush ```` block and runs it through
  `crushc -C` (parse + semantic check + compile) and then `crush-run run` (execute).
- Language facts below were confirmed by probing the built binaries, not by
  reading docs. Where a ticket explains the gap, it is cited (`CRUSH-NN`).
- First checker run (before any edits): **183 blocks — 50 green, 133 fail** (80 fail at
  compile, 53 at run; of the run failures ~36 need a host flag/capability, 13 are bare
  definitions with no top-level statement).

## Stale claims → current truth (page by page)

| Page | Stale claim | Current truth (evidence) | Action |
|---|---|---|---|
| getting-started | "all at `0.2.0`", `crush-lang-sdk = "0.2"` | crates.io today: `crush-vm` 0.3.6; `casm`/`crush-errors`/`crush-ffi`/`crush-diagnostics`/`crush-lint`/`crush-installer`/`tree-sitter-crush` 0.3.7; `crush-frontend`/`crush-cast`/`crush-cson`/`crush-index`/`crush-jit`/`crush-python` 0.3.0; `crush-lang-sdk` **0.2.0** (stale); workspace is 0.3.8. `crush-pkg`, `crush-aot*`, `crush-walker` are not on crates.io (crates.io API, 2026-10-07) | Rewrite table with per-crate versions + note the SDK lag |
| getting-started | No way to run `.crush` files; embedding only | `crush run FILE`, `crushc`, `crush-run`, `crush-compile`, `crush-repl` (`crates/crush-lang-sdk/src/bin/`); install = build from source + `crush-installer` (README.md) | Add install + first-program section (checker-proven) |
| getting-started | `--features net,db,graphics`; `net` = "`@net.*`" | SDK features: `net db graphics stdlib repl-helper native-plugins polyglot-*` (`crates/crush-lang-sdk/Cargo.toml`); `stdlib` is **off by default** (CRUSH-113) and `--stdlib` silently warns without it | Document |
| README / crush/README | "capsule / Exo-Core / HAL / `Capsule.toml`" vOS framing; "Python, Rust, Bash, C, Go" first-class | Standalone crush-ast has no capsule/HAL. Executable `@lang` lanes: python, javascript, bash. `@rust`/`@go` → `no executor registered` (probe) | Cut/replace |
| README / crush/README | "The `@` prefix marks a capability call" (README.md line 56) | Capability calls are unprefixed; `@` is for polyglot blocks, annotations, directives (already said in capabilities.md; README contradicts it) | Fix |
| crush/syntax | `;` mandatory, `/* */` comments, `'single'` strings, ternary, `**`, `+=`, `and/or/not` | `;` optional; `//` and `#` comments only; double-quoted strings only; no ternary/`**`/`+=`/word operators (probes; `lexer.rs`) | Rewrite |
| crush/syntax, types | `let mut`, `T?` optional types, `Array`/`Function` types, `0xFF`, `1e3` | `mut` is rejected after `let` (`parse_let_statement`, mod.rs:845); `String?` fails to parse; hex/exponent literals unsupported (probes) | Cut / mark |
| crush/functions | Lambdas `|x| { ... }` / `|x| => x*x`, closures | Unreachable from source (bare `\|` lexes as ident) — CRUSH-75 open; compiler captures nothing (no closures) | Mark not-yet-implemented, cite CRUSH-75 |
| crush/functions | `fn f(a: Int) -> Int` | Works (probe); param/return types are hints | Keep |
| crush/control_flow | `for i in range(n)`, `match`, `if` as expression | `for i in 0..n` and `for x in array` work; `range()` is undefined (probe); `match` works only as an expression (`let r = match x {...}`), statement form hits stack underflow (probe) | Rewrite |
| crush/operators | `and`/`or`/`not`, `**`, `//`, `+=` | `&&` `\|\|` `!` (short-circuit since CRUSH-125); `|>` pipeline; none of the others (probes) | Rewrite |
| crush/types, variables | Structs with typed construction `Point { x: 1 }`; "`new Point(1,2)`" | `struct P { x, y }` then `new P()` and assign fields; constructor args rejected by the parser (probe) | Rewrite |
| crush/types, variables | `io.print(a, b)` joins with space, `print` as variadic | `print` takes exactly 1 argument (`semantics.rs:35`); `io.print` takes N and concatenates with no separator (probe) | Fix |
| crush/capabilities | Manifest `permissions` object with path scoping (`"fs.read": ["./data"]`) | CASM manifest is `{"permissions": ["name", ...]}` (`casm/src/lib.rs:551`); at the CLI, grants are flags: `--fs --fs-root DIR --env --time --net --process --stdlib --cap NAME` (`crush-run run --help`) | Rewrite |
| crush/capabilities, stdlib | `import std.io;` and a `std.*` module system | `import` lowers to an unregistered `module.load` cap and fails at run time (CRUSH-110, open); there is no `std.*` | Cut; mark NYI |
| crush/capabilities, stdlib | `sys.*`, `net.get/post`, `fs.delete`, `io.eprint`, `type.of`, `array.length`, `map.*` | Not registered. Real: `fs.read/write/exists/list` (`--fs`), `env.get` (`--env`), `time.*` (`--time`), `net.http_get/http_post` (`--net`), `process.exec` (`--process`), `crypto.*`, `db.*`, `task.*`, `message_bus.*`, `akg.*`, plus the `--stdlib` families `str.* math.* conv.* collections.* json.* path.* regex.*` (`crush-lang-sdk/src/stdlib.rs`). `io.read` **is** implemented now (CRUSH-115, v0.3.6) | Rewrite tables from source |
| crush/stdlib | Same as above; `conv.to_string`, `type.of` | `conv.to_str`, `conv.type_of` (`stdlib.rs`) | Rewrite |
| crush/polyglot | "Python, Rust, Bash, C, Go"; `let r = @python { ... }` returns a value; typed returns; error model; timeouts; sandbox | Lanes: `python`, `javascript`, `bash` (run with host authority and **only** with `--polyglot`); other tags → `no executor registered`. Block form is a statement; free vars marshalled in, assigned variables (`result = …`) marshalled out; guest exceptions → `VmError::LangRuntimeError` with the `.crush` line (CRUSH-18); `Quotas::max_wall_time_ms` default 30 000 ms, kills the process group (CRUSH-19, `vm.rs:731`); `@lang[deps]` + bwrap/buckets sandbox only when `crush-vm` is built with `sandboxed-polyglot` — **off by default and not an SDK feature** (CRUSH-20/66, `crush-vm/Cargo.toml:94`) | Rewrite (GUIDE-2) |
| examples/* | 9 pages built on the same unrunnable syntax | See checker results; each block fixed, marked, or cut | Rewrite |
| cast/README | CAST schema | Checked against `crush-cast/src/lib.rs` (Statement/Expression variants) — see section below | Reconcile |
| cast/ai-native | AI opcodes "execute" | Opcodes parse/compile but execution is NOP/partial (CRUSH-1 open, CRUSH-34 in progress; TASKS.md M5) | Add status note |
| casm/* | Only the JSON IR is documented; examples use `"version": "0.1"`; "MessagePack, `.castb`/`.casmb`"; opcode set of 58 | `casm::Program::deserialize` **rejects** any version whose major ≠ `1` (`CASM_VERSION = "1.0"`, `casm/src/lib.rs`); real binary ext `.casmb` = shebang + MessagePack; `OpCode` has ~110 variants (try/throw/await/halt/list/tuple/set/exec_lang/ai_*/dom_*/str_*/math_*…) the instruction reference omits; the text assembly `crushc --emit casm` emits (`.func`, `PUSH_STR`, `CAP_CALL "io.print" 1`) and `crush-run`/`crush-compile` consume is a *second*, undocumented form | Add the text-assembly form; fix version; reconcile opcode list |
| appendix/* | Same syntax claims as the language chapters | — | Follow chapters |

## Status log

- 2026-10-07 (run 1): language chapters, stdlib, capabilities, polyglot, getting started, examples, README rewritten (11 commits).
- 2026-10-07 (run 2): casm/* (README, structure, instructions, serialization, examples), cast/* (README, ai-native), appendix/* (quick reference, comparison, glossary) rewritten against `crates/casm`, `crates/crush-vm`, `crates/crush-cast`; getting-started crate versions updated for the published 0.3.9 set (sdk 0.2.0 is yanked).
- **Final checker run (crush-ast `v0.3.9`):** 181 blocks = 141 ```crush + 24 ```casm + 12 JSON CASM/CAST + 4 `rust,no_run`. **165 green, 15 not-yet-implemented (CRUSH-75, CRUSH-34, CRUSH-110 + GAP-* ids), 1 skipped, 0 failing.** (First run before any edit: 183 crush blocks, 50 green, 133 failing; many of those blocks were cut or merged as pages were rewritten.)
- Foreman sweep corrections (no WASM sandbox, no `@rust/@c/@go/@zig/@wasm` executors, lambdas CRUSH-75 and imports CRUSH-110 not implemented, per-crate versions) applied; `grep` for those claims across `src/` is clean.
- Findings filed in TASKS (crush-ast bugs the guide now documents): `.casmb` cannot be read back; `CAST_VERSION` "0.1" vs front-end "1.0.0"; `casm_to_vm` `new_array` size ignored and most IR opcodes unsupported.

## Done when

- [x] PR open, `mdbook build` green
- [x] Checker covers every ```` ```crush ```` block; counts in the PR body
- [x] No page claims a feature, crate version or command crush-ast `v0.3.9` doesn't back
- [x] GUIDE-1 and GUIDE-2 tickets updated
