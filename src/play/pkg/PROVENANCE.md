# play/pkg

Generated files. Do not edit by hand.

`crush_web_bg.wasm` and `crush_web.js` are the browser build of the `crush-web`
crate:

- source: [nixpt/crush-ast](https://github.com/nixpt/crush-ast) at commit `4a4b6dd`
  (branch `agent/claude/CRUSH-web-parity`): `cb655f3`, the commit the guide's
  examples are verified against, plus crush-web's browser changes (refusing
  ungranted capabilities before running, as crush-run does; grantable `time` and
  `env`; guest errors reported as natively). Rebuild at the merge commit once
  that lands, and move `CRUSH_AST_COMMIT` to it.
- features: the defaults (`stdlib`, `panic-hook`) plus **`polyglot-javascript`**,
  so a granted `@javascript` block gets Crush variables in and a typed value out,
  as with `crush-run --polyglot` (the page runs the block with
  `src/play/guest-js.js`; see `src/play/worker.js`)
- toolchain: rustc 1.96.0 for `wasm32-unknown-unknown`, then `wasm-bindgen 0.2.126
  --target web` (the version in crush-web's `Cargo.lock`), built by
  `scripts/build-play-pkg` with local paths remapped, so the file names no local
  directory (cargo still hashes the checkout's location into symbol names, so a
  build from a checkout elsewhere has other hashes; the program is the same)
- no `wasm-opt` pass
- size: `crush_web_bg.wasm` is 6,854,107 bytes (1,959,155 gzipped). The
  previous build (`cb655f3`, default features, no `polyglot-javascript`) was
  5,001,948 bytes (1,439,176 gzipped): +1.85 MB raw, +0.52 MB over the wire, almost
  all of it `@javascript` marshaling (the same commit with only that feature added
  is 6,835,626 bytes).
- sha256:
  - `crush_web_bg.wasm` `1eca4dac3013e343df58d977306f0fb7ef7252463fd2f4a3b3742e6a249ed98e`
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
