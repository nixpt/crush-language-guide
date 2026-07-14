# Getting Started

The Crush toolchain is published on [crates.io](https://crates.io) as a set of
small, composable crates (all at `0.2.0`). You embed Crush in a Rust application
by depending on the SDK; the lower-level crates are available if you need direct
access to the IR, bytecode, or VM.

## The crates

| Crate | What it gives you |
|---|---|
| [`crush-lang-sdk`](https://crates.io/crates/crush-lang-sdk) | **Start here.** Ergonomic `Runtime` + `ProgramBuilder` over the VM: load, compile, and run Crush programs; register host capabilities. |
| [`crush-frontend`](https://crates.io/crates/crush-frontend) | Parser, semantic analyzer, optimizer, and CASM compiler (`parse_source`). |
| [`crush-vm`](https://crates.io/crates/crush-vm) | The CVM1 runtime: bytecode assembler/disassembler and the sandboxed interpreter with quotas + capability gates. |
| [`crush-cast`](https://crates.io/crates/crush-cast) | The CAST intermediate representation (the stable AST). |
| [`casm`](https://crates.io/crates/casm) | The CASM bytecode format. |
| [`crush-errors`](https://crates.io/crates/crush-errors) | Shared error types. |
| [`tree-sitter-crush`](https://crates.io/crates/tree-sitter-crush) | Tree-sitter grammar (editor tooling, syntax highlighting). |

## Add it to a project

```sh
cargo add crush-lang-sdk
```

or in `Cargo.toml`:

```toml
[dependencies]
crush-lang-sdk = "0.2"
```

The SDK pulls in `crush-vm`, `crush-frontend`, `crush-cast`, `casm`, and
`crush-errors` transitively — you usually don't depend on them directly.

### Optional features

`crush-lang-sdk` keeps its default surface lean; opt into host integrations as
needed:

```toml
crush-lang-sdk = { version = "0.2", features = ["net", "db", "graphics"] }
```

- `net` — networking host capabilities (`@net.*`)
- `db` — database host capabilities
- `graphics` — graphics host capabilities
- `repl-helper` — richer REPL line editing

## Quick start (embedding)

```rust,no_run
use crush_lang_sdk::{Runtime, ProgramBuilder};

fn main() -> anyhow::Result<()> {
    let program = ProgramBuilder::new()
        .permission("io.print")
        .line(r#".func main"#)
        .line(r#"PUSH_STR "hello, cvm1""#)
        .line(r#"CAP_CALL "io.print" 1"#)
        .line(r#"HALT"#)
        .build()?;

    let result = Runtime::new().run(&program)?;
    assert_eq!(result.output, "hello, cvm1");
    Ok(())
}
```

To compile Crush *source* (rather than hand-written CASM), use
`crush_frontend::parse_source` to produce a [CAST](cast/README.md) `Program`,
then compile and run it through the SDK.

## A note on capabilities

Crush is **capability-gated**: a program can only call host functions
(`io.print`, `fs.read`, `net.get`, …) that it declares a permission for and
that the host has actually registered. The published crates give you:

- the **capability framework** — `HostCaps` / `HostCap` and the SDK's
  `host_caps` extension point to register your own handlers, plus built-in
  basics like `io.print`;
- the **`stdlib`** module and the feature-gated host capabilities above.

The *full* batteries-included capability set documented in the
[Standard Library](crush/stdlib.md) and [Capability System](crush/capabilities.md)
chapters describes the capability **interface**. A host environment supplies the
implementations — the [exosphere](https://github.com/nixpt/exosphere) agent-native
OS ships the complete corecaps set; when you embed Crush in your own application
you register exactly the capabilities you want to expose.
