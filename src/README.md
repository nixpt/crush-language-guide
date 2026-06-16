# The Crush Language Guide

**Crush** is a capability-based, polyglot programming language and virtual runtime. It lets you
write in multiple languages (Python, Rust, Bash, C, Go) within a single program while enforcing
fine-grained security through an explicit capability system.

## What this guide covers

| Section | What you'll learn |
|---------|-------------------|
| [Crush Language](crush/README.md) | Syntax, types, control flow, functions, capabilities, polyglot embedding |
| [CAST](cast/README.md) | The intermediate AST format that walkers produce |
| [CASM](casm/README.md) | The stack-based bytecode the VM executes |
| [Appendix](appendix/glossary.md) | Glossary, quick reference, language comparisons |

## The compilation pipeline

```
Source (.crush / .py / .rs / ...)
         │
    Walker (language-specific)
         │
    CAST  (Crush AST — JSON)
         │
    Crush Compiler
         │
    CASM  (Crush Assembly — JSON / binary .castb)
         │
    NanoVM  (execution)
```

## Hello, Crush

```crush
fn main() {
    @io.print("Hello, Crush!");
}
```

The `@` prefix marks a **capability call** — a crossing of the VM boundary that requires an
explicit permission in the program manifest.

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
