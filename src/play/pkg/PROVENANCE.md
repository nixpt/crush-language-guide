# play/pkg

Generated files. Do not edit by hand.

`crush_web_bg.wasm` and `crush_web.js` are the browser build of the `crush-web`
crate, **built locally** with `scripts/build-play-pkg` (there is no crush-ast
release of this commit):

- source: [nixpt/crush-ast](https://github.com/nixpt/crush-ast) commit
  `7f3fef31ba7df65bb085cde8144c1a1abadec9fe` (main, 2026-11-16, after `v0.11.2`), the
  same commit the guide's examples are verified against (`CRUSH_AST_COMMIT`).
- features: the defaults (`stdlib`, `panic-hook`) plus **`polyglot-javascript`**
  and **`polyglot-python`**, so a granted `@javascript` / `@python` block gets
  Crush variables in and a typed value out, as with `crush-run --polyglot` (the
  page runs the block with `src/play/guest-js.js` (with `src/play/node-inspect.js`),
  or `src/play/guest-py.js` in Pyodide, `src/play/pyodide.json`; see
  `src/play/worker.js`)
- toolchain: rustc 1.100.0 for `wasm32-unknown-unknown` with crush-web's own release
  profile (`opt-level = "s"`, LTO, one codegen unit), then `wasm-bindgen 0.2.126
  --target web --remove-name-section`, local paths remapped. No `wasm-opt` pass.
- size: `crush_web_bg.wasm` is **6,899,558 bytes (2,204,761 gzipped)**.
- sha256 (the `.wasm` hash depends on the checkout path, see the script):
  - `crush_web_bg.wasm` `278e9c1b746446f6d6f194a63ef1bb649dbae3f883410b6d21d35a5348928812`
  - `crush_web.js` `3f4c724d6ff16488d12b9ee2416fe4eb2164ed534eed2dd0817d3776bbcbd3be`
    (byte-identical to the previous build's glue)

> **Known bug at this commit.** Granting this build the in-memory filesystem
> (`fs`) panics before the program runs (`RuntimeError: unreachable`): crush-ast's
> in-memory filesystem (CRUSH-240, since v0.11.0) reads the wall clock with
> `SystemTime::now`, which `wasm32-unknown-unknown` does not provide. The book
> therefore does not grant `fs` (`BROWSER_FLAGS` in `scripts/mdbook-crush-run.py`),
> and `--fs` examples are labelled as needing the host.

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
