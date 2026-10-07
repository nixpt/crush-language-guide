# play/pkg

Generated files. Do not edit by hand.

`crush_web_bg.wasm` and `crush_web.js` are the browser build of the `crush-web`
crate, copied unchanged from [nixpt/crush-website](https://github.com/nixpt/crush-website)
`playground/pkg/` at commit `2f5469f` (the build behind crushlang.org/playground):

- source: [nixpt/crush-ast](https://github.com/nixpt/crush-ast) at commit `4e9c388` (2026-10-07)
- toolchain: `cargo build --release --target wasm32-unknown-unknown` in
  `crates/crush-web`, then `wasm-bindgen 0.2.126 --target web`
- sha256:
  - `crush_web_bg.wasm` `f1c4120d64afbedd8e6608e5629b5ca79dba219de825aa428817df933455940a`
  - `crush_web.js` `26db524c5ed5c94fc89fd1a34f26def9be06820308c90dd760b9a3ccd6caa9d2`

The book serves its own copy because module workers must be same-origin.

To refresh: rebuild as described in crush-website's `playground/pkg/PROVENANCE.md`
(or copy a newer crush-website build), update the commits and hashes above, update
`BROWSER_CAPS` in `scripts/mdbook-crush-run.py` if crush-vm's built-in capabilities
changed, then run `node scripts/check-browser.mjs` — it runs every guide block
through this build and fails if any block's Run/label would now be wrong.
