# Getting Started

Crush is alpha software. This page gets you from a clean machine to a running
program, and then shows how to embed the VM in a Rust application.

> Verified against crush-ast `bad81048`, the **v0.9.0** release (2026-10-31): the
> prebuilt binaries from its GitHub release, which this guide's checker runs.

## 1. Install the toolchain

The language is implemented in [crush-ast](https://github.com/nixpt/crush-ast).
There are two ways to get it. Both give you the same `crush`, `crushc`, `crush-run`,
`crush-compile`, `crush-repl` and `crush-debug`.

**From crates.io** (needs Rust 1.95 or newer):

```sh
cargo install crush-lang-sdk
```

> **Not `cargo install crush`.** The `crush` crate on crates.io is an unrelated
> project. The toolchain is published as **`crush-lang-sdk`**. There is no
> `crush-ast` crate either; that is the repository's name.

**Prebuilt Linux binaries.** Since v0.9.0 every `vX.Y.Z` tag has a GitHub release
(a pre-release until 1.0) with a Linux x86_64 tarball, a tarball of the browser
runtime, and a `SHA256SUMS` file. v0.9.0 is the first such release:

```sh
gh release download v0.9.0 --repo nixpt/crush-ast
sha256sum -c SHA256SUMS
tar -xzf crush-0.9.0-x86_64-unknown-linux-gnu.tar.gz
export PATH="$PWD/crush-0.9.0-x86_64-unknown-linux-gnu:$PATH"
```

The tarball holds `crush`, `crushc`, `crush-run`, `crush-compile`, `crush-repl`,
`crush-debug`, `crush-pkg` and `crush-gui`. `crush doctor` then tells you which
interpreters your polyglot blocks can use.

**From source**, to build a particular commit (this is how the guide's CI builds
the commit in `CRUSH_AST_COMMIT`):

```sh
git clone https://github.com/nixpt/crush-ast
git clone https://github.com/nixpt/buckets      # must sit NEXT TO crush-ast
cd crush-ast
cargo build --release -p crush-lang-sdk                       # crush, crush-run, crushc, ...
cargo build --release -p crush-aot                            # optional: crush-aotc (native AOT)
```

Two things to know:

- **`buckets` must be a sibling directory.** `crush-vm` has an optional
  path-dependency on `../buckets` (the sandbox provisioner), and Cargo resolves it
  even when the feature is off, so a lone `crush-ast` checkout fails with
  `failed to read .../buckets/Cargo.toml`.
- **The standard library is built in by default** (crush-ast CRUSH-113): `str.*`,
  `math.*`, `conv.*`, `collections.*`, `json.*` and friends need no flag. As of
  0.9.0 the HTTP client (`net.*`) and raw TCP sockets (`tcp.*`) are compiled in by
  default too; they are still refused unless you pass `--net` / `--tcp` /
  `--tcp-listen`. Only `db` and `graphics` still need `--features db,graphics`.

The binaries:

| Binary | What it does |
|---|---|
| `crush` | The front door: `crush run FILE`, `crush build FILE`, `crush repl`, `crush debug FILE`, `crush gui run FILE --ui`, `crush doctor` |
| `crush-run` | Run a `.crush`, `.casm` or `.cvm1` file (all the capability flags live here) |
| `crushc` | Compile `.crush` to bytecode (`.cvm1`), or `--emit casm\|ast\|types`; `-C` only checks |
| `crush-compile` | Assemble CASM text into a `.cvm1` binary |
| `crush-repl` | Interactive REPL (`crush repl`; commands are `.help`, `.quit`) |
| `crush-debug` | The debugger (`crush debug`): see [Debugging](crush/debugging.md) |
| `crush-gui` | Programs that draw a window (`crush gui run`): a separate package, see [Windows](crush/gui.md) |
| `crush-diff` | (from a source build) run programs on several engines and report where they disagree |
| `crush-aotc` | (from `-p crush-aot`) compile `.crush` to a native library via Rust or C, or `crush-aotc run FILE` |

Source builds need Rust 1.95 or newer (crush-ast's CI checks that MSRV).

> **Crates.io.** Release `0.9.0` (2026-10-31, crush-ast `bad81048`) is published for
> `crush-lang-sdk` (which installs `crush`, `crushc`, `crush-run`, `crush-compile`,
> `crush-repl`, `crush-debug` and `crush-diff`) and the library crates, all released
> together at the workspace version. Earlier releases (`0.7.1`, `0.8.0`) lack things
> this guide describes: slices on strings, hex and binary literals, the debugger,
> `tcp.*`, and the single diagnostics format. **Never depend on `crush-lang-sdk`
> `0.2`**: that line has been yanked, and it runs `@lang` blocks without the
> `--polyglot` gate.

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

### Three file types

`crush run` (and `crush-run run`) takes source, assembly or bytecode:

```sh
crushc hello.crush -o hello.cvm1         # compile to CVM1 bytecode
crush run hello.cvm1                     # run the bytecode
crushc --emit casm hello.crush -o hello.casm
crush run --cap io.print hello.casm      # CASM text: grant each capability it calls
```

A `.casm` text file has no manifest, so every capability it calls must be named
with `--cap` (without it: `capability not declared in manifest: io.print`).
Arguments after the file name reach the program as `sys.args()`:
`crush run prog.crush a b` → `[a, b]`.

### Capabilities need flags

A program can only reach the outside world through capabilities, and each group is
off until you switch it on:

```sh
crush run prog.crush                             # str.* math.* conv.* json.* ... need nothing
crush run --fs --fs-root ./data prog.crush       # fs.read / fs.write / fs.exists / fs.list
crush run --polyglot prog.crush                  # @python / @javascript / @bash blocks
crush run --net prog.crush                       # net.http_get / http_post / ... (HTTP only)
crush run --tcp prog.crush                       # tcp.connect / send / recv (client sockets)
crush-run caps prog.crush                        # what does it need? (runs nothing)
```

For example, this reads a file, so it needs `--fs`:

<!-- check: runfail fs.read -->
```crush
print(fs.read("notes.txt"))
```

Run it without the flag and nothing runs: `needs capabilities this run does not
grant; nothing was run: --fs: fs.read`. The full flag list is in
[Capability System](crush/capabilities.md) (`crush-run run --help` prints it
too).

### Limits worth knowing on day one

- `crush doctor` reports which polyglot interpreters (`python3`, `node`, `bash`)
  it can find.
- Defaults: 1,000,000 instructions, 256 call frames, 1 MiB of output, 30 s per
  polyglot block (all in [Capability System](crush/capabilities.md#resource-limits)).
- Named functions can't see top-level variables (lambdas can), and `import`
  doesn't load code yet — see [Variables](crush/variables.md) and
  [Syntax](crush/syntax.md#imports-and-exports).

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

SDK Cargo features: the defaults `stdlib` (the standard library), `net` (the HTTP
client), `tcp` and `tcp-tls` (raw sockets), `debug` (the debugger),
`native-plugins`, `polyglot-python`, `polyglot-javascript` and `polyglot-rust` (the
analyses that marshal values into and out of `@lang` blocks), plus the optional
`db`, `graphics`, `gpu`, `repl-helper` and `polyglot-typescript`. A default feature
only compiles the capability in; the program still needs the matching flag at run time.

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

Both snippets are compiled and run against crush-ast `bad81048` by
`scripts/check-examples.py --crush-ast`. `Runtime::new()` registers only the
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
