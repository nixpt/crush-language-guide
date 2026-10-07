<p align="center">
  <img src="assets/hero.png" alt="Crush Banner" width="100%" />
</p>

<h1 align="center">
  <img src="assets/logo.png" alt="Crush Logo" width="40" height="40" style="vertical-align: middle;" />
  The Crush Language Guide
</h1>

**Crush** is a capability-based scripting language with polyglot blocks, plus the
toolchain that runs it: a compiler to bytecode, a sandboxed VM, and an
intermediate representation (CAST) that other languages can be translated into.

> **Alpha.** This guide documents what the toolchain does today, verified against
> crush-ast `main` — every `crush` example on these pages is executed by
> `scripts/check-examples.py`. Features that exist in the design but not in the
> implementation are marked *not yet implemented*, with the crush-ast ticket.

## What this guide covers

| Section | What you'll learn |
|---------|-------------------|
| [Getting Started](getting-started.md) | Build the toolchain, run a program, embed the VM from Rust |
| [Crush Language](crush/index.md) | Syntax, types, control flow, functions, capabilities, polyglot blocks |
| [Examples](examples/index.md) | Runnable programs |
| [CAST](cast/index.md) | The AST format that walkers and the compiler share |
| [CASM](casm/index.md) | The bytecode formats the VM executes |
| [Appendix](appendix/glossary.md) | Glossary, quick reference, language comparisons |

## The compilation pipeline

```
 Crush source (.crush)                     Other languages (.py / .rs / .go / ...)
        │                                              │
  crush-frontend                                walker (language-specific)
  parse · check · optimize                              │
        │                                               │
        └───────────────►  CAST  (JSON AST)  ◄──────────┘
                              │
                        compiler
                              │
                  CASM  (bytecode: JSON IR or CVM1 text)
                              │
             assembler → CVM1 binary (.cvm1)
                              │
        crush-vm  (portable VM · FastVM · JIT · AOT backends)
```

`crush run prog.crush` runs the whole left-hand path in one step.

## Hello, Crush

```crush
fn main() {
    io.print("Hello, Crush!")
}
```

<!-- check: output -->
```text
Hello, Crush!
```

`io.print` is a **capability call**: a call that crosses the VM boundary to the
host, and so only works if the host grants it. Capability calls are written like
any other dotted call — there is no `@` prefix. (The `@` sigil in Crush
introduces polyglot blocks such as `@python { ... }`, and annotations.)

Press **Run** under the example to run it in your browser, or **Edit** to change
it first. [Running the Examples](running-examples.md) explains the buttons and
labels, and what the in-browser runtime can and cannot do.

## Where the source lives

The language implementation is the standalone
[crush-ast](https://github.com/nixpt/crush-ast) repository, extracted from
the exosphere agent-native OS monorepo on 2026-06-12. It contains the CAST
intermediate representation, tree-sitter grammar, polyglot walkers, compiler
frontend, VM runtime, package manager, and installer.

The upstream [exosphere](https://github.com/nixpt/exosphere) project retains
a subprocess-based walker registry that invokes the crush-ast walker binaries,
and its own `crush-cast`/`casm`/`nanovm` crates for the Crush language
compiler running inside the agent-native OS.

## License

Licensed under either of [MIT](https://github.com/nixpt/crush-language-guide/blob/main/LICENSE-MIT) or
[Apache License 2.0](https://github.com/nixpt/crush-language-guide/blob/main/LICENSE-APACHE) at your option.
