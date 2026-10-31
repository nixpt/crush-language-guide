# GUIDE-6 — Sync the guide with crush-ast 0.9.0

**Status**: PR open (nixpt/crush-language-guide, branch `agent/nova/GUIDE-6`) · **Priority**: P1
**Validated against**: crush-ast `v0.9.0` (`bad8104818387f7ef791a518bca2503d88793e0b`, 2026-10-31),
using the **released** artifacts, not a local build: `crush-0.9.0-x86_64-unknown-linux-gnu.tar.gz`
and `crush-web-0.9.0-pkg.tar.gz` from the GitHub release (`sha256sum -c SHA256SUMS`: both OK).

Follows [GUIDE-3](GUIDE-3-sync-with-crush-ast.md): same method (run everything; docs follow what the
binaries do), now for a release instead of a `main` commit.

## Method

- `CRUSH_AST_COMMIT` → the v0.9.0 commit; every "Verified against" line updated.
- `scripts/verify-examples --bin-dir <release bin dir>` and `scripts/check-examples.py --bin-dir <same>`
  (without `--crush-ast`: the `rust,no_run` embedding blocks are skipped, since the box had ~3 GB free
  and the point of the exercise was not to build crush-ast; CI runs them).
- `src/play/pkg` replaced with the released `pkg/` (`PROVENANCE.md` has tag, commit, hashes).
- Each new feature below was checked against crush-ast's source/CHANGELOG `## [0.9.0]` **and run**
  with the 0.9.0 binaries before it was written down.

## Results against 0.9.0 (before editing the guide)

| Check | Result |
|---|---|
| `verify-examples` | `fail=2, ok=121 (total 123)` |
| `check-examples.py` | `fail=1, green=208, nyi=7, skipped=20 (total 236)` |

The three failures were all real 0.9.0 behaviour changes (none is a crush-ast bug):

- `polyglot/bash` and `src/crush/polyglot.md` (the `@bash` block): crush-ast #255 is fixed. A `@bash` block
  now receives the Crush variables it names as `$name` / `${name}` (compile.rs `bash_var_refs`). The
  PITFALL program became a normal one, the "Known bug" box became prose, and #255 left the pitfall table.
- `strings/slice-is-arrays-only`: string slices work (`s[a:b]`, `s[::step]` lower to `seq.slice`). The
  program was replaced by `strings/slices`, `strings/slice-step` and `strings/slice-zero-step`.

After: `verify-examples` **ok=130 (total 130)**; `check-examples.py` **green=217, nyi=7, skipped=20
(total 244)**; `node scripts/check-browser.mjs` **run=150, fail=42, host=8, none=1** (0 misclassified);
`mdbook build` ok.

## What changed in the guide

| Page | Change |
|---|---|
| getting-started | install rewritten: `cargo install crush-lang-sdk` (and *not* `crush`), prebuilt Linux release (first at v0.9.0, with `SHA256SUMS`), from-source; binary table (+`crush-debug`, `crush-gui`); default features (`net`, `tcp`, `debug`); flags `--net` / `--tcp`; crates.io note now 0.9.0 |
| crush/types | new "Slicing strings"; array slices with step |
| crush/syntax | hex / binary integer literals (checked example) |
| crush/capabilities | `--tcp`, `--tcp-listen`, `--ui` in the flag table; `net.*` compiled in by default; renamed `http.*` refused with its replacement; new "Raw sockets (`tcp.*`)" section |
| crush/debugging (new) | `crush debug`, grants `--step` / `--inspect[=redacted]`, commands, NDJSON mode |
| crush/gui (new) | `crush gui run FILE --ui`, `ui.*` API and events; says it is the separate `crush-gui` package and what was and was not verified |
| crush/diagnostics (new) | text vs `--message-format json`, the one seven-field schema, line/col on semantic errors |
| crush/polyglot, README, examples/async-dom | `@bash` reads `$name` variables (#255 fixed) |
| crush/README | "New in 0.9.0" index |
| appendix/quick_reference | debug, gui, tcp flags, `--message-format json` |
| verified-corpus | counts (130 programs), pitfall table |
| notebooks, gh-pages.yml | the notebook kernel is one release behind (below) |

New corpus programs: `basics/int-literals`, `basics/bad-hex-literal` (.err), `strings/slices`,
`strings/slice-step`, `strings/slice-zero-step` (.err), `capabilities/tcp-loopback`,
`capabilities/tcp-listen-needs-its-flag` (.err), `capabilities/http-renamed` (.err); removed
`strings/slice-is-arrays-only`.

`crush update` is **not** documented: it merged after 0.9.0.

## Not verified / open

- **Windows (`ui.*`) were not opened**: no desktop session here. Verified: the refusal without `--ui`,
  the "no display" error with it, and the API/events from `crates/crush-gui` source and
  `docs/design/ui-api.md`. crush-ast's own README says the same of its desktop backend. The counter
  block on the page is `text`, unchecked, and the page says so.
- **Notebooks**: needed a kernel on crush-ast 0.9.0. `crush-notebook-kernel` 0.3.0 was published
  for this (nixpt/crush-notebook#2); `KERNEL_VERSION` is 0.3.0. All 32 notebooks (134 cells) run
  clean through it with `scripts/run-notebooks.py` (checked locally, 2026-10-31).
- **Released `crush_web_bg.wasm` is 9,702,572 bytes**, 2.8 MB larger than the guide's own build of the
  previous commit (6,869,494). The entire difference is the 2,858,761-byte `name` section: crush-ast's
  `artifacts.yml` runs `wasm-bindgen --target web` without `--remove-name-section`
  (`scripts/build-play-pkg` passes it). Suggest the flag upstream; the code is identical. Used as
  released, as instructed; documented in `src/play/pkg/PROVENANCE.md`.
- `rust,no_run` embedding blocks (getting-started) and `--crush-ast` checks were not run locally.
- `scripts/test-interactive.py` and `scripts/check-corpus-browser.py` (Playwright) were not run.
- `{"code":"E-CAPS"}` JSON for a renamed `http.get` says "no grant in this build provides them" and
  omits the rename hint that the text output shows (`http.get was renamed to net.http_get`). Minor
  inconsistency, noted rather than filed: `crush-run run h.crush --message-format json` with
  `let r = http.get("http://x")`.

## Done when

- [x] `sha256sum -c` OK
- [x] verify-examples + check-examples green against 0.9.0
- [x] `mdbook build` ok
- [ ] PR merged (not by the author)
