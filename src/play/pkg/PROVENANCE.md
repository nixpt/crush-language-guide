# play/pkg

Generated files. Do not edit by hand.

`crush_web_bg.wasm` and `crush_web.js` are the browser build of the `crush-web`
crate:

- source: [nixpt/crush-ast](https://github.com/nixpt/crush-ast) at commit `cb655f3`
  (2026-10-16), the same commit the guide's examples are verified against
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
- size: `crush_web_bg.wasm` is 6,835,626 bytes (1,949,934 gzipped). The same
  commit without `polyglot-javascript` is 5,001,948 bytes (1,439,176 gzipped), so
  `@javascript` marshaling costs 1.83 MB raw, 0.51 MB over the wire.
- sha256:
  - `crush_web_bg.wasm` `ce876631119be9322f27ec949c87b45ece7612e4fb77eb917c8aa63ba62fce54`
  - `crush_web.js` `e6eaba3a29c62ac8a06584f3a93b666ce75a4bb99b001ad9790c5707ecce4643`

The book serves its own copy: the page fetches these files and hands them to the
worker in its sandboxed iframe, which has no network of its own.

To refresh: run `scripts/build-play-pkg ../crush-ast` with crush-ast at the commit
the guide is verified against, update the commit, sizes and hashes here, update
`BROWSER_CAPS` / `HOST_CAPS` / `BROWSER_LANGS` in `scripts/mdbook-crush-run.py` if
crush-web's capabilities changed, then run `node scripts/check-browser.mjs`: it
runs every guide block through this build and fails if any block's Run/label
would now be wrong.
