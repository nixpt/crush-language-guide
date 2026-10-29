# play/pkg

Generated files. Do not edit by hand.

`crush_web_bg.wasm` and `crush_web.js` are the browser build of the `crush-web`
crate:

- source: [nixpt/crush-ast](https://github.com/nixpt/crush-ast) at commit `b1791d8e`
  (2026-10-29), the same commit the guide's examples are verified against
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
- size: `crush_web_bg.wasm` is 9,786,136 bytes (2,656,656 gzipped). The
  previous build (`aa07413`, same features) was 6,856,830 bytes (1,966,985
  gzipped): +2.93 MB raw, +0.69 MB over the wire. Almost all of it is the
  `polyglot-javascript` feature, i.e. the JavaScript walker it links: the JS class
  work since `aa07413` (CRUSH-277/284/285/293: classes, accessors, `super`,
  statics). With default features only, `b1791d8e` builds to 5,283,340 bytes
  (`cb655f3`: 5,001,948), so the feature now adds ~4.5 MB where it added ~1.85 MB.
  The JS glue (`crush_web.js`) is byte-identical to the `aa07413` build.
- sha256:
  - `crush_web_bg.wasm` `ff04754c654f8948073e9534aefb82ee8d654809471ff65aa7f301760231f893`
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
