# Decisions


## 2026-06-12T04:41:58-05:00 — [ADOPTED] Standalone doc repo for Crush (Language+CAST+CASM only)

Reason:
Exosphere book buried Crush docs inside a larger book; scope is language-only, not unarchiving old crush-language repo which had more than docs


## 2026-06-12T04:42:00-05:00 — [VERIFIED] Docs audited against exosphere source 2026-06-12

Reason:
crushed-book had ~12 categories of errors: keywords list incomplete (21 vs 28), try/catch/structs/match/lambdas falsely marked Future Feature, range() not ..., closures syntax wrong, Bash walker falsely presented as a real walker


## 2026-10-08T16:08:34-05:00 — Chapter notebooks: crush cells verbatim; only expected-failure cells wrapped in fn main; files generated into book/notebooks after mdbook build, never committed

Reason:
crush-notebook >=0.1.1 shares lets/fns/structs across cells, so a session name can mask the error an expected-failure example demonstrates (variables.md:128 ran without the wrapper); standalone fn main programs don't see session vars. Generated files can't drift from the guide; link paths come from mdbook-crush-run.notebook_path.


## 2026-10-16T03:17:47-05:00 — [STRATEGIC] [VERIFIED] Verified corpus + pinned crush-ast commit; CI builds crush-ast and runs it

Reason:
Every language claim must come from a program that was run. examples/verified/<area>/NAME.crush with .out/.err/.flags/.stdin/.needs sidecars, run by scripts/verify-examples; CRUSH_AST_COMMIT pins the crush-ast commit the guide is verified against, and the gh-pages 'verify' job builds that commit (buckets is now public) and runs the corpus plus check-examples.py. PITFALL programs encode wrong-today behaviour with the crush-ast issue, so a fix flips them red and forces a doc update.

Rejected alternatives:
- **local-only checking:scripts/README said buckets was private; it is public now, so CI can build crush-ast**
- **pin to crates.io 0.6.0:predates Records/@kind, -> outputs, AOT refusals**


## 2026-10-16T03:17:47-05:00 — [TACTICAL] [ADOPTED] Notebooks CI job non-blocking until crush-notebook-kernel moves past crush-ast 0.3.x

Reason:
crush-notebook-kernel 0.1.1 (latest on crates.io) depends on crush-* ^0.3.9, so cells using closures, struct methods, green tasks or -> outputs fail in it even though the pinned crush-ast runs them; the verify job is the authority. Revert continue-on-error once a kernel on the pinned crush-ast is published.


## 2026-10-16T03:17:47-05:00 — [TACTICAL] [VERIFIED] Vendored crush-web rebuilt at the pinned crush-ast commit; standard library is browser-runnable

Reason:
Browser classification must match the commit the guide documents. crush-web at 3ae0b4a registers the default-on stdlib, so STDLIB host-needs is empty; crypto and file text.* are host caps. check-browser.mjs proves every label (129 run, 24 host, 36 fail).


## 2026-10-29T22:31:04-05:00 — Run @python on the page in Pyodide (exec mode), not through crush-web's lower mode

Reason:
Exact semantics: Pyodide 314.0.7 is CPython 3.14, the Python the guide verifies with natively; guest-py.js matches python3 -c byte for byte on output, tracebacks, exit codes, stdin and imports, and refuses (loudly) only what needs the host: files, processes, network, packages. Lower mode ran 5 of the guide's Python blocks, refused 8, and needs walker work for the rest. Cost: ~6.3 MB compressed, fetched from jsDelivr only on a page's first @python run, each file checked against src/play/pyodide.json; +0.66 MB gzipped for crush-web's polyglot-python marshaling, on every page.

Artifacts: src/play/guest-py.js, src/play/pyodide.json

Rejected alternatives:
- **crush-web polyglot**: lower (Python walker)
- **vendoring Pyodide into the repo (13 MB of binaries per version)**

Outcome:
11 more guide blocks runnable; whole verified corpus and the UI test pass in headless Chrome


## 2026-10-29T23:39:32-05:00 — Run @javascript on the page as node -e does: async via crush-web deferLang, node's own util.inspect

Reason:
The synchronous executor could not wait for promises or timers, so async blocks were refused, and the hand-written formatter refused Map/Set/classes/long arrays. crush-ast #314 adds Session deferLang (need_lang / provide_lang / fail_lang), so guest-js.js runs a block as an async function with its own event loop over the browser's timers, until nothing is pending; uncaught errors, unhandled rejections and non-zero exit fail it like node. console.* use node-inspect-extracted 3.3.4 (node's lib/internal/util/inspect.js, MIT, vendored as src/play/node-inspect.js): 57/59 values byte-identical to node 26; the two V8-internal ones (a Promise's state, a native Proxy) are refused, or made exact by handing the block the library's Proxy. 31 compared cases match node -e or are refused loudly.

Artifacts: src/play/guest-js.js, src/play/node-inspect.js

Rejected alternatives:
- **keep refusing async and special formatting**
- **hand-written inspect (cannot stay exact)**

Outcome:
check-browser 193/0 FAIL; corpus in Chrome 118 + 4 refusals; UI test 312 ok, 0 FAIL

