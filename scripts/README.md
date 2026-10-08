# scripts/

`check-examples.py` runs the guide's code blocks through the real crush-ast
toolchain, so the book cannot show code that does not work. It is a **local check**,
not a CI job: building crush-ast needs a checkout of `crush-ast` with its private
`buckets` sibling beside it (`crush-vm` has a path dependency on `../buckets`), which
GitHub-hosted CI for this repo cannot fetch.

## Run it

```sh
# 1. Build the toolchain from a crush-ast checkout (tag v0.3.9 or newer), with buckets next to it
cd ../crush-ast
cargo build -p crush-lang-sdk --features stdlib,net,db,graphics   # -> target/debug/{crushc,crush-run}

# 2. Check every block in src/
cd ../crush-language-guide
scripts/check-examples.py --bin-dir ../crush-ast/target/debug --crush-ast ../crush-ast -v
```

Without `--crush-ast` the ```crush and ```casm blocks are still checked; the
`rust,no_run` embedding examples and the JSON CASM/CAST blocks are reported as
skipped (they need the helper below, which is built against that checkout).
Exit status is non-zero if any block misbehaves.

## What is checked

| Fence | Check |
|---|---|
| ```` ```crush ```` | `crushc -C` (parse, type-check, compile), then `crush-run run` |
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
| `../src/play/` | `worker.js` + the vendored crush-web build (`pkg/`, provenance in `pkg/PROVENANCE.md`). |
| `check-browser.mjs` | `node scripts/check-browser.mjs`: runs every block through `src/play/pkg` and fails if a label is wrong (a "runnable" block that fails, a "needs the host" block that would run, an output that differs from the page). Runs in CI. |
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
cargo install --locked --root /tmp/nbk crush-notebook-kernel@0.1.1
python3 scripts/run-notebooks.py --kernel /tmp/nbk/bin/crush-notebook-kernel --dir book/notebooks
```

CI (`gh-pages.yml`) runs all three: generation in the deploy and interactive jobs,
and the `notebooks` job validates and runs every notebook on the published kernel
(the installed binary is cached by version; bump `KERNEL_VERSION` there to move).
