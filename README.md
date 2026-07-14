<p align="center">
  <img src="src/assets/hero.png" alt="Crush" width="100%" />
</p>

<h1 align="center">The Crush Language Guide</h1>

<p align="center">
  <a href="https://nixpt.github.io/crush-language-guide/"><strong>📖 Read the guide →</strong></a>
</p>

---

**Crush** is a capability-based, polyglot programming language and virtual runtime. You write in
several languages — Python, Rust, Bash, C, Go — inside a single program, and the runtime enforces
fine-grained security through an explicit capability system: code gets exactly the authority you
hand it, and nothing more.

This repository is the **source for the guide**, not the language itself. It is an
[mdBook](https://rust-lang.github.io/mdBook/); the published site is what you probably want:

### 👉 https://nixpt.github.io/crush-language-guide/

## What the guide covers

- **The Crush language** — syntax, types, scoping, operators, control flow, functions
- **The capability system** — the security model, and why it is the point of the language
- **Polyglot programming** — embedding other languages, and where the boundaries sit
- **The standard library**
- **CAST / CASM** — the AST and assembly layers underneath
- **Worked examples** — Fibonacci, arrays and loops, exception handling, concurrency and structs,
  lambdas and pipes, import styles, a system-info dashboard

## Building it locally

```bash
cargo install mdbook     # if you don't have it
mdbook serve             # http://localhost:3000, live-reloads as you edit
```

Chapters live in `src/`; the table of contents is `src/SUMMARY.md` — a page that isn't listed
there won't appear in the book.

## How it publishes

Every push to `main` runs `.github/workflows/gh-pages.yml`, which builds the book and pushes the
result to the `gh-pages` branch, which GitHub Pages serves. There is nothing to deploy by hand.

## Where the code lives

The guide documents the toolchain, it does not contain it. The language, compiler, and runtime
live in **[crush-ast](https://github.com/nixpt/crush-ast)**, which ships `crushc` (compile),
`crush-run` (execute), and `crush-repl` (interactive).

## Contributing

Corrections are welcome, and the most useful ones are the boring ones: an example that doesn't
actually run, a described behaviour that the runtime doesn't have. If the guide and the code
disagree, the guide is wrong — please open an issue saying so.

## Licence

Dual-licensed under [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE), at your option.
