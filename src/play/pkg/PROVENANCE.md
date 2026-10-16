# play/pkg

Generated files. Do not edit by hand.

`crush_web_bg.wasm` and `crush_web.js` are the browser build of the `crush-web`
crate:

- source: [nixpt/crush-ast](https://github.com/nixpt/crush-ast) at commit `cb655f3`
  (2026-10-16), the same commit the guide's examples are verified against
- toolchain: rustc 1.96.0, `cargo build --release --target wasm32-unknown-unknown`
  in `crates/crush-web` (with `buckets` checked out beside crush-ast), then
  `wasm-bindgen 0.2.126 --target web` (the version in crush-web's `Cargo.lock`)
- no `wasm-opt` pass (that is why it is larger than the earlier 4e9c388 build,
  which also lacked the standard library)
- sha256:
  - `crush_web_bg.wasm` `d31fa7b09840fa943604468d736f0c4b77d9c0d5b692ac331ea5b45c83a0042a`
  - `crush_web.js` `e6eaba3a29c62ac8a06584f3a93b666ce75a4bb99b001ad9790c5707ecce4643`

The book serves its own copy because module workers must be same-origin.

To refresh: rebuild as above at the crush-ast commit the guide is verified
against, update the commit and hashes here, update `BROWSER_CAPS` / `HOST_CAPS` in
`scripts/mdbook-crush-run.py` if crush-web's capabilities changed, then run
`node scripts/check-browser.mjs`: it runs every guide block through this build and
fails if any block's Run/label would now be wrong.
