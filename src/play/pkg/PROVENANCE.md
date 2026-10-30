# play/pkg

Generated files. Do not edit by hand.

`crush_web_bg.wasm` and `crush_web.js` are the browser build of the `crush-web`
crate:

- source: [nixpt/crush-ast](https://github.com/nixpt/crush-ast) at commit `c1cc21fb`
  (2026-10-30), the same commit the guide's examples are verified against. It
  includes #314 (`Session`'s `deferLang`, so the page runs a `@javascript` block
  asynchronously) and #315 (the `--fs` sandbox over a storage backend, so `fs`
  is grantable as an in-memory directory).
- features: the defaults (`stdlib`, `panic-hook`) plus **`polyglot-javascript`**
  and **`polyglot-python`**, so a granted `@javascript` / `@python` block gets
  Crush variables in and a typed value out, as with `crush-run --polyglot` (the
  page runs the block with `src/play/guest-js.js` (with `src/play/node-inspect.js`),
  or `src/play/guest-py.js` in Pyodide, `src/play/pyodide.json`; see
  `src/play/worker.js`)
- toolchain: rustc 1.96.0 for `wasm32-unknown-unknown` with crush-web's own
  release profile (#311: `opt-level = "s"`, LTO, one codegen unit, debug info
  stripped), then `wasm-bindgen 0.2.126 --target web --remove-name-section` (the
  version in crush-web's `Cargo.lock`), as `scripts/build-play-pkg` does, with
  local paths remapped, so the file names no local directory (cargo still hashes
  the checkout's location into symbol names, so a build from a checkout elsewhere
  has other hashes; the program is the same)
- no `wasm-opt` pass
- size: `crush_web_bg.wasm` is 6,869,494 bytes (2,189,504 gzipped; 6,819,694 at
  `d04bc60a`: #314 adds 15 KB, #315's file caps and in-memory tree 37 KB);
  `polyglot-python` (rustpython's parser, for the marshaling) is 1,826,542 bytes
  of it (664,316 gzipped): with only `polyglot-javascript` the same commit is
  4,993,152 (1,509,307). Pyodide itself is not part of this build: the page
  downloads it on the first `@python` run (`src/play/pyodide.json`). Built from
  `b1791d8e` (before #311) it was 9,786,136 (2,656,656 gzipped), and from
  `aa07413` 6,856,830 (1,966,985). The JS support itself was not the cause:
  `polyglot-javascript` also linked swc, a second JavaScript parser that only
  whole-file `.js` lowering uses (never in the browser, ~1.1 MB), and crush-web,
  being its own workspace root, built with cargo's default profile (no LTO, ~1 MB
  of function names kept). #311 fixes both. Interpreter-bound programs run ~10%
  slower than the 9.79 MB build. (#313, also in `d04bc60a`, adds the
  lowered-block output capture to the VM, 5.7 KB.) `crush_web.js` gains
  `Session.provide_lang` / `fail_lang` from #314.
- sha256:
  - `crush_web_bg.wasm` `2413ff5f71f871a7214aea4e9f4ea3dd938ed43d4fc99cede9ebe554eb031c97`
  - `crush_web.js` `3f4c724d6ff16488d12b9ee2416fe4eb2164ed534eed2dd0817d3776bbcbd3be`

The book serves its own copy: the page fetches these files and hands them to the
worker in its sandboxed iframe, which has no network of its own.

To refresh: run `scripts/build-play-pkg ../crush-ast` with crush-ast at the commit
the guide is verified against, update the commit, sizes and hashes here, update
`BROWSER_CAPS` / `HOST_CAPS` / `BROWSER_LANGS` / `BROWSER_FLAGS` in `scripts/mdbook-crush-run.py` if
crush-web's capabilities changed, then run `node scripts/check-browser.mjs`: it
runs every guide block through this build and fails if any block's Run/label
would now be wrong. After `mdbook build`, `scripts/check-corpus-browser.py` runs
the verified corpus through it in headless Chromium.
