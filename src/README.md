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

The language implementation is in the `exosphere` monorepo at
`crates/core/crush-lang/`. This guide is the standalone documentation extracted from the
`docs/crushed-book/` mdBook.
