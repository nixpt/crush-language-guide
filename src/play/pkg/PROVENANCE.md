# play/pkg

Generated files. Do not edit by hand.

`crush_web_bg.wasm` and `crush_web.js` are the browser build of the `crush-web`
crate:

- source: [nixpt/crush-ast](https://github.com/nixpt/crush-ast) at `b1791d8e`
  (2026-10-29), the commit the guide's examples are verified against, **plus
  crush-ast [#311](https://github.com/nixpt/crush-ast/pull/311)** (`f0e292c6`).
  #311 changes only `crush-web`'s and `crush-lang-sdk`'s manifests and
  `crush-web/Cargo.lock`, so no Crush source differs from `b1791d8e`. Rebuild
  from the commit that merges it, and drop this note, once it is on `main`.
- features: the defaults (`stdlib`, `panic-hook`) plus **`polyglot-javascript`**,
  so a granted `@javascript` block gets Crush variables in and a typed value out,
  as with `crush-run --polyglot` (the page runs the block with
  `src/play/guest-js.js`; see `src/play/worker.js`)
- toolchain: rustc 1.96.0 for `wasm32-unknown-unknown` with crush-web's own
  release profile (#311: `opt-level = "s"`, LTO, one codegen unit, debug info
  stripped), then `wasm-bindgen 0.2.126 --target web --remove-name-section` (the
  version in crush-web's `Cargo.lock`), as `scripts/build-play-pkg` does, with
  local paths remapped, so the file names no local directory (cargo still hashes
  the checkout's location into symbol names, so a build from a checkout elsewhere
  has other hashes; the program is the same)
- no `wasm-opt` pass
- size: `crush_web_bg.wasm` is 4,987,479 bytes (1,506,581 gzipped). Built from
  `b1791d8e` itself it was 9,786,136 (2,656,656 gzipped), and from `aa07413`
  6,856,830 (1,966,985). The JS support itself was not the cause:
  `polyglot-javascript` also linked swc, a second JavaScript parser that only
  whole-file `.js` lowering uses (never in the browser, ~1.1 MB), and crush-web,
  being its own workspace root, built with cargo's default profile (no LTO, ~1 MB
  of function names kept). #311 fixes both. Interpreter-bound programs run ~10%
  slower than the 9.79 MB build. `crush_web.js` is byte-identical to the
  `aa07413` and `b1791d8e` builds.
- sha256:
  - `crush_web_bg.wasm` `ac07728c639255086ec5b5ea1e4918577f470999def86c3a1b4ef1a50dc59214`
  - `crush_web.js` `384bf65ce36b1834c63b995fb9e0607579c3cd96f00fb1bef0fa2c9b63f9e8a9`

The book serves its own copy: the page fetches these files and hands them to the
worker in its sandboxed iframe, which has no network of its own.

To refresh: run `scripts/build-play-pkg ../crush-ast` with crush-ast at the commit
the guide is verified against, update the commit, sizes and hashes here, update
`BROWSER_CAPS` / `HOST_CAPS` / `BROWSER_LANGS` / `BROWSER_FLAGS` in `scripts/mdbook-crush-run.py` if
crush-web's capabilities changed, then run `node scripts/check-browser.mjs`: it
runs every guide block through this build and fails if any block's Run/label
would now be wrong. After `mdbook build`, `scripts/check-corpus-browser.py` runs
the verified corpus through it in headless Chromium.
