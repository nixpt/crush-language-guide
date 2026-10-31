# play/pkg

Generated files. Do not edit by hand.

`crush_web_bg.wasm` and `crush_web.js` are the browser build of the `crush-web`
crate, taken **unmodified from the crush-ast release** rather than built locally:

- source: [nixpt/crush-ast](https://github.com/nixpt/crush-ast) tag **`v0.9.0`**,
  commit `bad8104818387f7ef791a518bca2503d88793e0b` (2026-10-31), the same commit the
  guide's examples are verified against (`CRUSH_AST_COMMIT`). The files are from the
  release asset `crush-web-0.9.0-pkg.tar.gz` (checked against the release's
  `SHA256SUMS`; its `pkg/BUILD-INFO` carries the hashes below).
- features: the defaults (`stdlib`, `panic-hook`) plus **`polyglot-javascript`**
  and **`polyglot-python`**, so a granted `@javascript` / `@python` block gets
  Crush variables in and a typed value out, as with `crush-run --polyglot` (the
  page runs the block with `src/play/guest-js.js` (with `src/play/node-inspect.js`),
  or `src/play/guest-py.js` in Pyodide, `src/play/pyodide.json`; see
  `src/play/worker.js`)
- toolchain (from BUILD-INFO): rustc 1.99.1 (2026-10-13) for `wasm32-unknown-unknown`
  with crush-web's own release profile (`opt-level = "s"`, LTO, one codegen unit),
  then `wasm-bindgen 0.2.126 --target web`, as crush-ast's `artifacts.yml` does. No
  `wasm-opt` pass.
- size: `crush_web_bg.wasm` is **9,702,572 bytes (2,480,083 gzipped)**. That is
  2.8 MB more than the guide's own reproducible build of the previous commit
  (6,869,494 bytes), and the whole difference is the 2,858,761-byte debugging `name`
  section: the release workflow runs `wasm-bindgen` without `--remove-name-section`
  (this guide's `scripts/build-play-pkg` passes it) and without local path remapping.
  The code is the same; the page just downloads more. To get the smaller file,
  rebuild with `scripts/build-play-pkg ../crush-ast` at the pinned commit.
- sha256:
  - `crush_web_bg.wasm` `3399a3863e30978430af46976e43c130dd973e3fab377faafb3a4c9c8272521e`
  - `crush_web.js` `3f4c724d6ff16488d12b9ee2416fe4eb2164ed534eed2dd0817d3776bbcbd3be`
    (byte-identical to the previous build's glue)

The book serves its own copy: the page fetches these files and hands them to the
worker in its sandboxed iframe, which has no network of its own.

To refresh: download `crush-web-<ver>-pkg.tar.gz` from the crush-ast release of the
pinned commit, check it against `SHA256SUMS`, copy `crush_web_bg.wasm` and
`crush_web.js` here, and update the tag, commit, sizes and hashes above. (Or run
`scripts/build-play-pkg ../crush-ast` to build the same commit locally.) Then update
`BROWSER_CAPS` / `HOST_CAPS` / `BROWSER_LANGS` / `BROWSER_FLAGS` in
`scripts/mdbook-crush-run.py` if crush-web's capabilities changed, and run
`node scripts/check-browser.mjs`: it runs every guide block through this build and
fails if any block's Run/label would now be wrong. After `mdbook build`,
`scripts/check-corpus-browser.py` runs the verified corpus through it in headless
Chromium.
