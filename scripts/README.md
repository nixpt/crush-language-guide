# scripts/

Two scripts run the guide's code through the real crush-ast toolchain, so the book
cannot show code that does not work:

- `verify-examples` runs the **verified corpus** in `examples/verified/`: 120+
  standalone programs, each beside its exact expected output (`.out`) or expected
  failure (`.err`). See `src/verified-corpus.md` for the file conventions.
- `check-examples.py` runs every code block **on the pages** (below).

Both run in CI (`gh-pages.yml`, job `verify`) against the crush-ast commit pinned
in `../CRUSH_AST_COMMIT`. To move the guide to a newer crush-ast: change that
file, run both scripts, fix what they report, and rebuild `src/play/pkg` at the
same commit (see its `PROVENANCE.md`).

## Run it

```sh
# 1. Build the toolchain from a crush-ast checkout (the commit in CRUSH_AST_COMMIT), with buckets next to it
git clone https://github.com/nixpt/crush-ast ../crush-ast
git -C ../crush-ast checkout "$(cat CRUSH_AST_COMMIT)"
git clone https://github.com/nixpt/buckets ../buckets
(cd ../crush-ast && cargo build -p crush-lang-sdk)          # -> target/debug/{crushc,crush-run}

# 2. The corpus, then every block in src/
scripts/verify-examples --bin-dir ../crush-ast/target/debug
scripts/check-examples.py --bin-dir ../crush-ast/target/debug --crush-ast ../crush-ast -v
```

Without `--crush-ast` the ```crush and ```casm blocks are still checked; the
`rust,no_run` embedding examples and the JSON CASM/CAST blocks are reported as
skipped (they need the helper below, which is built against that checkout).
Exit status is non-zero if any block misbehaves.

## What is checked

| Fence | Check |
|---|---|
| ```` ```crush ```` | `crushc -C` (parse, type-check, compile; `<!-- check: nocrushc ISSUE -->` skips it), then `crush-run run` |
| ```` ```casm ```` | `crush-run run --cap io.print` (CASM text assembly) |
| ```` ```json ```` after `<!-- check: casm-json -->` / `cast-json` / `cast-validate` | `casm-check` helper (below) |
| ```` ```rust,no_run ```` | `cargo run` against the checkout's `crush-lang-sdk` |
| ```` ```text ```` after `<!-- check: output -->` | compared with the previous block's stdout |

`casm-check/main.rs` is a ~100-line Rust helper the checker builds into
`$CARGO_TARGET_DIR` against the checkout: it loads JSON CASM through
`casm::Program::deserialize`, validates/compiles JSON CAST, and runs both.

Directives go in HTML comments directly above a block (invisible in the book); the
full list is in the docstring at the top of `check-examples.py`. Blocks that
document something crush-ast does not do yet carry `<!-- check: nyi TICKET -->`: the
checker requires them to *fail*, so the day the feature lands the check flags the
page for an update.

## The interactive book (Run / Edit buttons)

| File | Role |
|---|---|
| `mdbook-crush-run.py` | mdBook preprocessor (wired in `book.toml`): wraps each ```` ```crush ```` block in a `<div class="crush-block" data-crush=run\|fail\|host\|none>` derived from the directives above plus the block's capability calls. `--manifest` prints every block's classification as JSON. |
| `../interactive/crush-run.{js,css}` | The Run / Edit / Reset controls (mdBook `additional-js` / `additional-css`). |
| `../src/play/` | `worker.js`, `guest-js.js` (runs granted `@javascript` blocks as `node -e` does: async, with node's formatting), `node-inspect.js` (node's own `util.inspect`, vendored from node-inspect-extracted 3.3.4), `guest-py.js` (runs granted `@python` blocks in Pyodide), `pyodide.json` (the pinned Pyodide release the page downloads on the first `@python` run, with each file's sha256) + the vendored crush-web build (`pkg/`, provenance in `pkg/PROVENANCE.md`). |
| `fetch-pyodide` | `scripts/fetch-pyodide`: downloads the release in `src/play/pyodide.json` into `.pyodide/` (gitignored), checking each sha256, for `check-browser.mjs`; `--update` re-pins the hashes after a version change. |
| `check-corpus-browser.py` | `mdbook build && scripts/check-corpus-browser.py [--markdown]`: runs the verified corpus through the built book's Run-button runtime in headless Chromium and compares with each `.out`/`.err`, like `verify-examples` does for `crush-run` (each program is a match, a loud refusal, or a listed known difference). Runs in CI. |
| `build-play-pkg` | `scripts/build-play-pkg ../crush-ast`: rebuilds `src/play/pkg` reproducibly at the pinned commit and prints its sizes and hashes. |
| `check-browser.mjs` | `scripts/fetch-pyodide && node scripts/check-browser.mjs`: runs every block through `src/play/pkg` (`@python` in the pinned Pyodide) and fails if a label is wrong (a "runnable" block that fails, a "needs the host" block that would run, an output that differs from the page). Runs in CI. |
| `test-interactive.py` | `mdbook build && scripts/test-interactive.py`: headless Chromium (Playwright) clicks Run on every runnable / expected-failure block, exercises Edit / Reset, no-JS, mobile width and a dark theme. Runs in CI. |

When crush-web is rebuilt with more capabilities, update `BROWSER_CAPS` in
`mdbook-crush-run.py`; `check-browser.mjs` tells you which labels changed.

## Chapter notebooks

| File | Role |
|---|---|
| `build-notebooks.py` | One [crush-notebook](https://github.com/nixpt/crush-notebook) (`.crush-nb`) per chapter with ```` ```crush ```` examples, written to `book/notebooks/` after `mdbook build` (generated output, never committed). `--validate schemas/notebook.schema.json` checks each against crush-notebook's schema (needs `jsonschema`). |
| `run-notebooks.py` | Runs every notebook through `crush-notebook-kernel` over stdio MCP and judges each cell against the guide: runnable cells must print the page's output, expected failures must fail, host-only cells must be refused. `--markdown` prints the per-notebook table. |

The preprocessor (`mdbook-crush-run.py`) puts an "Open as a notebook" link under
each such chapter's title and fills the list on `src/notebooks.md`; `notebook_path()`
and `has_notebook()` there are shared with `build-notebooks.py`, so links and files
cannot disagree. Under `mdbook serve` the links 404 until you generate the files.

```sh
mdbook build
python3 scripts/build-notebooks.py --out book/notebooks --validate schemas/notebook.schema.json
cargo install --locked --root /tmp/nbk crush-notebook-kernel@0.2.0
python3 scripts/run-notebooks.py --kernel /tmp/nbk/bin/crush-notebook-kernel --dir book/notebooks
```

CI (`gh-pages.yml`) runs all three: generation in the deploy and interactive jobs,
and the `notebooks` job validates and runs every notebook on the published kernel
(the installed binary is cached by version; bump `KERNEL_VERSION` there to move).
