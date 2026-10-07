# Serialization Formats

A Crush program exists in several on-disk forms, one per layer of the pipeline.
This chapter lists them, says which tool reads and writes each, and describes the
version checks that gate loading. For the layouts themselves see
[Program Structure](structure.md).

| Layer | Form | Extension | Written by | Read by |
|---|---|---|---|---|
| source | Crush text | `.crush` | you | `crushc`, `crush-run`, `crush run` |
| CAST | JSON | `.cast.json` (any non-`.castb`/`.cbor` name) | walkers, agents, `casm`-side tools | `crush_cast::Program::{deserialize,load}`, `crush_frontend::compile_cast` |
| CAST | CBOR | `.castb`, `.cbor` | `crush_cast::Program::save` | same |
| CASM IR | JSON | `.casm` | `casm::Program::{serialize,save}` | `casm::Program::{deserialize,load}` |
| CASM IR | MessagePack | `.casmb` | `casm::Program::{serialize,save}` | **see the bug note below** |
| CASM text | assembly | `.casm` | `crushc --emit casm`, you | `crush-run run`, `crush-compile` |
| CVM1 | binary | `.cvm1` | `crushc -o`, `crush build`, `crush-compile` | `crush-run run`, `crush run`, `Runtime::run_blob` |

## CASM IR: JSON (`.casm`)

This is the readable form of a compiled program and the one you diff, commit and
generate from tools. `casm::Program::load` / `save` choose the codec from the file
extension: `.casmb` means binary, **anything else is JSON**.

<!-- check: casm-json -->
```json
{
  "version": "1.0",
  "functions": {
    "main": {
      "params": [],
      "locals": [],
      "body": [
        {"op": "push_int", "value": 42},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        {"op": "halt"}
      ]
    }
  },
  "manifest": { "permissions": ["io.print"] }
}
```

<!-- check: output -->
```text
42
```

The compiler writes pretty-printed JSON with `meta` on every instruction, so a
compiled program is verbose: the five-line `add` program in the
[overview](index.md) is about 3 KB as IR JSON and 199 bytes as `.cvm1`.

## CASM IR: MessagePack (`.casmb`)

`Program::serialize(Format::Binary)` writes the line `#!/usr/bin/env crush run`
followed by the program as MessagePack (via `rmp_serde`), and `save` marks the file
executable on Unix. The reader skips a leading `#!` line.

> **Known bug (crush-ast `v0.3.9`).** A `.casmb` file cannot be read back. The
> writer emits MessagePack's compact array encoding but `Instruction` flattens its
> operands into a map, so every load fails with `invalid type: sequence, expected a
> map`. Until that is fixed, treat `.casmb` as write-only and ship `.cvm1`
> instead. The block below fails exactly this way:

<!-- check: casmb-fails expected a map -->
<!-- check: casm-json -->
```json
{
  "version": "1.0",
  "functions": { "main": { "body": [ {"op": "halt"} ] } }
}
```

Note also that `crush run` and `crush-run run` accept only `.crush`, `.casm` (as
*text assembly*) and `.cvm1`. Neither can execute IR JSON or `.casmb` directly; that
needs the Rust API.

## CVM1 (`.cvm1`)

The executable form: `CVM1` magic, a version byte, a JSON manifest, a constant
pool and a flat code section, described byte by byte in
[Program Structure](structure.md#the-cvm1-binary).

```bash
crushc add.crush -o add.cvm1     # or: crush build add.crush
crush-run run add.cvm1
```

```bash
crush-compile prog.casm -o prog.cvm1 --cap io.print --name prog   # text assembly -> CVM1
```

## Version gates

Every loader fails closed on an incompatible version, comparing the **major**
component only (minor bumps stay compatible):

| Format | Constant | Accepts | Error |
|---|---|---|---|
| CASM IR | `casm::CASM_VERSION = "1.0"` | `version` with major `1` (`"1.0"`, `"1.0.0"`, `"1.4"`) | `version mismatch at casm boundary: expected 1.0, found 2.0` |
| CVM1 | `bytecode::VERSION = 2` | version byte `1` or `2` | `UnsupportedVersion(n)` |
| CAST | `crush_cast::CAST_VERSION = "0.1"` | `cast_version` with major `0` | `version mismatch at cast boundary: expected 0.1, found …` |

The old docs said `"version": "0.1"` for CASM; that is now rejected (major `0`).

<!-- check: casm-json -->
<!-- check: runfail version mismatch at casm boundary: expected 1.0, found 0.1 -->
```json
{ "version": "0.1", "functions": { "main": { "body": [ {"op": "halt"} ] } } }
```

> **Known inconsistency (crush-ast `v0.3.9`).** `CAST_VERSION` is `"0.1"` but the
> Crush front end stamps the CAST it produces with `cast_version: "1.0.0"`. The
> versioned loader (`Program::deserialize`/`load`) therefore rejects the front end's
> *own* output, while plain `serde_json` and `validate_json` accept it. Example
> programs in `examples/cast/` carry `"0.1.0"` and load fine. See
> [CAST](../cast/index.md#serialization).

## Rust API

```rust,no_run
use casm::{Format, Program};

fn main() -> anyhow::Result<()> {
    let program = crush_lang_sdk::compile::compile_crush_to_casm(
        "io.print(6 * 7)",
    )?;

    // JSON IR, round trip through bytes.
    let bytes = program.serialize(Format::Json)?;
    let back = Program::deserialize(&bytes, Format::Json)?;
    assert_eq!(back.functions.len(), program.functions.len());

    // Lower to a runnable CVM1 program and execute it.
    let vm_program = crush_lang_sdk::compile::casm_to_vm(&back)?;
    let result = crush_lang_sdk::Runtime::new().run(&vm_program)?;
    print!("{}", result.output);
    assert_eq!(result.output, "42\n");

    // CVM1 blob round trip.
    let blob = vm_program.to_blob();
    let result = crush_lang_sdk::Runtime::new().run_blob(&blob)?;
    assert_eq!(result.output, "42\n");
    Ok(())
}
```

`Format::from_path` picks `Json` or `Binary` from a path. `Program::save(path)` and
`Program::load(path)` combine that with file I/O.

## Practical advice

- **Distribute `.cvm1`**; it is the format with a working load path in every tool, a
  magic number and a version byte.
- **Commit `.crush` source**, not generated IR; regenerate IR when you need to
  inspect it (`crushc --emit casm` for text, `compile_crush_to_casm` for JSON).
- When an *agent* produces programs, have it emit [CAST](../cast/ai-native.md) JSON
  and let the compiler produce CASM — see the doctrine there.
