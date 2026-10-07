# CASM Overview

**CASM** (Crush Assembly) is the stack-machine instruction set that Crush programs
compile to. The name covers three closely related things, and most confusion about
it comes from mixing them up:

| Form | What it is | Extension | Defined in | Who produces / runs it |
|---|---|---|---|---|
| **CASM IR** (JSON) | The compiler's structured output: functions of JSON instructions, `{"op": "push_int", "value": 42}` | `.casm` JSON, or `.casmb` (MessagePack) | the `casm` crate (`casm::Program`) | `compile_crush_to_casm` produces it; embedders load it with `casm::Program::load` |
| **CASM text** | A line-oriented assembly you can write by hand: `.func main` / `PUSH 42` / `CAP_CALL "io.print" 1` | `.casm` | `crush-vm`'s assembler | `crushc --emit casm` prints it; `crush-run run x.casm` and `crush-compile` consume it |
| **CVM1** (binary) | The bytecode the VM actually executes: magic `CVM1`, constant pool, flat code | `.cvm1` | `crush-vm` (`bytecode.rs`) | `crushc` writes it; `crush-run run x.cvm1` runs it |

(The extension `.casm` is shared by the JSON IR and the text assembly; the tools
that read a file expect one of them — `crush-run` expects text.)

They fit together like this:

```
 Crush source ──parse──▶ CAST (JSON AST) ──compile──▶ CASM IR (JSON) ──lower──▶ CASM text ──assemble──▶ CVM1 bytes ──▶ VM
                                                                      (crush_lang_sdk::compile::casm_to_vm)
```

`crushc` runs the whole chain; `crush-run run FILE.crush` compiles in memory and
runs. The CASM IR is the **interchange point**: every front-end (the Crush parser,
the polyglot walkers, an agent writing [CAST](../cast/README.md) directly) ends up
there, and every back-end (the VM, the AOT compilers `crush-aot` / `crush-aotc`,
the FastVM lowering) starts there.

## What is real and what is not

- **The VM is stack-based**, with a flat operand stack, per-frame local slots, a
  call stack, and a `try`/`throw` handler stack.
- **Host access is capability-only.** There is no syscall instruction. A program
  talks to the outside world with `CAP_CALL "name" argc`, and the VM refuses a
  capability that the host did not register *or* that the program's manifest does
  not list.
- **The IR has more instructions than the VM bytecode.** The `casm` crate's
  `OpCode` enum is a superset; `casm_to_vm` lowers only part of it (see the
  [Instruction Reference](instructions.md#what-lowers-to-cvm1)). Some IR
  instructions lower to a `NOP`; some are rejected with `Unsupported CVM1 opcode`.
- **The `ai_*`, `dom_*`, `spawn`/`yield`/`await` instructions are stubs.** In the
  IR→CVM1 lowering the `ai_*` and `dom_*` instructions become `NOP`s; a hand-written
  CVM1 `AI_QUERY` reaches an `ai_native.query` capability that returns
  `{ok: true, kind: "query", echo: []}` and does nothing else. See
  [AI-Native CAST](../cast/ai-native.md#what-actually-runs).
- **Source mapping** is carried in each IR instruction's `meta` (`line`, `col`);
  the CVM1 binary does not store it (the text assembler keeps a line→offset map for
  debuggers only).

## Seeing it for yourself

Compile a small program to text assembly:

```crush
fn add(a, b) {
    return a + b
}
let x = add(2, 3)
io.print("x = ", x)
```

<!-- check: output -->
```text
x = 5
```

```bash
crushc add.crush --emit casm
```

<!-- check: run -->
```casm
.func main
    PUSH 3
    PUSH 2
    CALL add
    STORE 0
    PUSH_STR "x = "
    LOAD 0
    CAP_CALL "io.print" 2
    PUSH_NULL
    RET
.func add
    STORE 0
    STORE 1
    LOAD 0
    LOAD 1
    ADD
    RET
```

Two things to notice, both explained in [Program Structure](structure.md): arguments
are pushed in **reverse** order (`3` then `2`), so the callee's first `STORE` pops the
first argument into slot 0, the second `STORE` the next one, and so on; and all top-level statements live in a
function called `main`.

## Next steps

- **[Program Structure](structure.md)** — the JSON IR, the text assembly and the CVM1 binary layout.
- **[Instruction Reference](instructions.md)** — every opcode, with stack effects.
- **[Examples](examples.md)** — hand-written programs, all run by the guide's checker.
- **[Serialization](serialization.md)** — `.casm`, `.casmb`, `.cvm1` and the version gates.
- **[Crush Language Guide](../crush/README.md)** — the source language that compiles to it.
