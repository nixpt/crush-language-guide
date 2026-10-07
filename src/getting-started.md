# Getting Started

Crush is alpha software. This page gets you from a clean machine to a running
program, and then shows how to embed the VM in a Rust application. Everything here
was run against crush-ast `v0.3.9` (the release on crates.io).

## 1. Build the toolchain

The language is implemented in [crush-ast](https://github.com/nixpt/crush-ast).
Build it from source — this is the path this guide's examples are validated
against:

```sh
git clone https://github.com/nixpt/crush-ast
git clone https://github.com/nixpt/buckets      # must sit NEXT TO crush-ast
cd crush-ast
cargo build --release -p crush-lang-sdk --features stdlib,net,db,graphics
```

Two things to know:

- **`buckets` must be a sibling directory.** `crush-vm` has an optional
  path-dependency on `../buckets` (the sandbox provisioner), and Cargo resolves it
  even when the feature is off, so a lone `crush-ast` checkout fails with
  `failed to read .../buckets/Cargo.toml`.
- **`--features stdlib` is not optional for this guide.** The standard library is
  off by default (crush-ast CRUSH-113); without it `--stdlib` only prints a
  warning and `str.*`, `math.*`, `conv.*` and friends don't exist.

You need Rust 1.85 or newer. The build produces these binaries in
`target/release/`:

| Binary | What it does |
|---|---|
| `crush` | The front door: `crush run FILE`, `crush build FILE`, `crush repl` |
| `crush-run` | Run a `.crush`, `.casm` or `.cvm1` file (all the capability flags live here) |
| `crushc` | Compile `.crush` to bytecode (`.cvm1`), or `--emit casm\|ast\|types`; `-C` only checks |
| `crush-compile` | Assemble CASM text into a `.cvm1` binary |
| `crush-repl` | Interactive REPL |

Put them on your `PATH`, or install them with the bundled installer
(`cargo run -p crush-installer -- install --bin-dir target/release` copies them
into `~/.crush/bin`; it does not currently include the `crush` wrapper).

> **Crates.io.** The `0.3.9` release is published: `crush-lang-sdk` (which installs
> `crush`, `crushc`, `crush-run`, `crush-compile`, `crush-repl` and `crush-diff`),
> `crush-vm`, `crush-frontend`, `casm`, `crush-cast`, `crush-errors`,
> `crush-diagnostics`, `crush-ffi`, `crush-cson`, `crush-index`, `crush-walker-core`,
> `crush-lang-python` and `crush-lang-js`. So `cargo install crush-lang-sdk` works and
> gives the toolchain this guide describes, and an embedding project can depend on
> `crush-lang-sdk = "0.3.9"`. Four crates lag: `crush-lint`, `crush-installer` and
> `tree-sitter-crush` are at `0.3.7`, `crush-jit` and `crush-python` at `0.3.0`;
> `crush-pkg`, `crush-aot` and `crush-aotc` are not published. **Never depend on
> `crush-lang-sdk` `0.2`**: that line has been yanked, and it runs `@lang` blocks
> without the `--polyglot` gate.
>
> The `cargo install` route does not enable the optional SDK features
> (`stdlib`, `net`, `db`, `graphics`): add them with
> `cargo install crush-lang-sdk --features stdlib,net,db,graphics`.

## 2. Hello, Crush

Save this as `hello.crush`:

```crush
let name = "Crush"
print("Hello, " + name + "!")
```

<!-- check: output -->
```text
Hello, Crush!
```

Run it:

```sh
crush run hello.crush
```

```text
Hello, Crush!
[steps=6, stack=0]
```

The `[steps=…]` line is a run summary on standard error. Compile-only checking is
`crushc -C hello.crush`; to see the bytecode, `crushc --emit casm hello.crush`.

### Capabilities need flags

A program can only reach the outside world through capabilities, and each group is
off until you switch it on:

```sh
crush run --stdlib prog.crush                    # str.* math.* conv.* json.* ...
crush run --fs --fs-root ./data prog.crush       # fs.read / fs.write / fs.exists / fs.list
crush run --polyglot prog.crush                  # @python / @javascript / @bash blocks
```

For example, this reads a file, so it needs `--fs`:

<!-- check: runfail unknown capability: fs.read -->
```crush
print(fs.read("notes.txt"))
```

Run it without the flag and it fails with `unknown capability: fs.read`. The full
flag list is in [Capability System](crush/capabilities.md) (`crush-run run --help`
prints it too).

### Limits worth knowing on day one

- Output is buffered: if a program fails at run time, what it printed before the
  failure is not shown.
- Defaults: 1,000,000 instructions, 256 call frames, 1 MiB of output, 30 s per
  polyglot block (all in [Capability System](crush/capabilities.md#resource-limits)).
- Functions can't see top-level variables, and `import` doesn't load code yet — see
  [Variables](crush/variables.md) and [Syntax](crush/syntax.md#imports-and-exports).

## 3. The crates

Embedding Crush in a Rust program means depending on the SDK; the lower-level
crates give direct access to the IR, bytecode, or VM.

| Crate | What it gives you |
|---|---|
| [`crush-lang-sdk`](https://crates.io/crates/crush-lang-sdk) | **Start here.** `Runtime`, `ProgramBuilder`, host-capability registration, and the `compile` module that turns Crush source into a runnable program. |
| [`crush-frontend`](https://crates.io/crates/crush-frontend) | Parser, semantic analyzer, optimizer, and CASM compiler (`parse_source`). |
| [`crush-vm`](https://crates.io/crates/crush-vm) | The CVM1 runtime: assembler/disassembler and the sandboxed interpreter with quotas + capability gates; also the FastVM. |
| [`crush-cast`](https://crates.io/crates/crush-cast) | The CAST intermediate representation. |
| [`casm`](https://crates.io/crates/casm) | The CASM IR (`casm::Program`, JSON and MessagePack) — see [CASM](casm/index.md). |
| [`crush-errors`](https://crates.io/crates/crush-errors) | Shared error types. |
| [`tree-sitter-crush`](https://crates.io/crates/tree-sitter-crush) | Tree-sitter grammar (editor tooling, syntax highlighting). |

SDK Cargo features: `stdlib` (the standard library), `net`, `db`, `graphics`,
`repl-helper`, plus the default `native-plugins`, `polyglot-python` and
`polyglot-javascript` (the free-variable analysis that marshals values into and out
of `@python`/`@javascript` blocks).

## 4. Embedding

Compile Crush source and run it on the VM — the same thing `crush run` does:

```rust,no_run
use crush_lang_sdk::compile::compile_crush_source;
use crush_lang_sdk::Runtime;

fn main() -> anyhow::Result<()> {
    let program = compile_crush_source(r#"print("hello from crush")"#)?;
    let result = Runtime::new().run(&program)?;
    assert_eq!(result.output, "hello from crush\n");
    Ok(())
}
```

Or hand-write CVM1 assembly (what `crushc --emit casm` prints) with
`ProgramBuilder`:

```rust,no_run
use crush_lang_sdk::{ProgramBuilder, Runtime};

fn main() -> anyhow::Result<()> {
    let program = ProgramBuilder::new()
        .permission("io.print")
        .line(r#".func main"#)
        .line(r#"PUSH_STR "hello, cvm1""#)
        .line(r#"CAP_CALL "io.print" 1"#)
        .line(r#"HALT"#)
        .build()?;

    let result = Runtime::new().run(&program)?;
    assert_eq!(result.output, "hello, cvm1\n");
    Ok(())
}
```

Both snippets are compiled and run against crush-ast `main` as part of this
guide's checks (`scripts/embed-check`). `Runtime::new()` registers only the
built-in primitives (`io.print`, `io.read`, …); to expose more — the standard
library, filesystem, polyglot — build a `HostCaps` with `HostCapsBuilder` and pass
it with `Runtime::with_quotas(..).with_host_caps(..)`, which is exactly what
`crush-run` does for its flags. The permission names a program may call are part of
its manifest ([CASM structure](casm/structure.md)).

## 5. Where next

- **[The language](crush/index.md)**: syntax, types, control flow, functions
- **[Capability System](crush/capabilities.md)** and **[Polyglot](crush/polyglot.md)**:
  the security model — read the "what is not enforced" sections
- **[Examples](examples/index.md)**: runnable programs
- **[CAST](cast/index.md)** and **[CASM](casm/index.md)**: the compiler's formats
