# Program Structure

This chapter describes the three forms of CASM from the top down: the JSON IR
(`casm::Program`), the text assembly, and the CVM1 binary. Field names and layouts
are taken from `crates/casm/src/lib.rs`, `crates/crush-vm/src/assembler.rs` and
`crates/crush-vm/src/bytecode.rs` in crush-ast.

## The JSON IR

```json
{
  "version": "1.0",
  "functions": { "main": { "params": [], "locals": [], "body": [ /* instructions */ ] } },
  "manifest": { "permissions": ["io.print"] },
  "lang": "crush"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `version` | string | yes | CASM format version. The loader accepts any version whose **major** is `1` (`CASM_VERSION = "1.0"`); the Crush compiler writes `"1.0.0"`. Anything else is rejected at load time. |
| `functions` | object | yes | function name → function definition |
| `manifest` | object | no | `{"permissions": [capability names…]}`. Defaults to no permissions. |
| `lang` | string | no | source-language hint (`"crush"`, `"python"`, …); informational |

There is **no `entry` field**. When the program is lowered to CVM1, execution
starts at the function named `main` (the assembler picks `main` if one exists,
otherwise the first function it sees — and `functions` is an unordered map, so
always name your entry function `main`). The Crush compiler puts all top-level
statements into `main`.

### Functions

| Field | Type | Required | Description |
|---|---|---|---|
| `params` | array of strings | no (default `[]`) | parameter names |
| `locals` | array of strings | no (default `[]`) | declared local names |
| `type_hints` | object | no | name → type string, tooling only |
| `body` | array of instructions | yes | the code |

`params` and `locals` are **documentation for tools**: the VM does not bind
parameters for you. A call pushes its arguments (last argument first) and jumps; the
callee's body must begin by `store`-ing them. This is what the compiler emits for
`fn add(a, b)`:

```json
{ "params": ["a", "b"], "locals": [],
  "body": [ {"op":"store","name":"a"}, {"op":"store","name":"b"},
            {"op":"load","name":"a"},  {"op":"load","name":"b"},
            {"op":"add"}, {"op":"ret"} ] }
```

Variables are referred to **by name** in the IR; lowering assigns each distinct name
in a function a numeric slot (in order of first use), and slots are local to the
call frame.

### Instructions

```json
{ "op": "push_int", "value": 42, "instr_lang": "crush", "meta": { "line": 4, "col": 15 } }
```

| Field | Type | Required | Description |
|---|---|---|---|
| `op` | string | yes | the operation, lower-case snake case (`"push_int"`, `"cap_call"`, …) |
| `instr_lang` | string or null | no | source language of this instruction (the Rust field is `lang`, the JSON key is `instr_lang`) |
| `meta` | any JSON | no | free-form metadata; the compiler writes `line` and `col` |
| *(others)* | varies | per op | operation arguments, flattened into the same object |

Operation arguments sit **next to** `op`, not in a nested object:

```json
{"op": "push_int", "value": 42}
{"op": "store",    "name": "x"}
{"op": "cap_call", "name": "io.print", "argc": 1}
{"op": "call",     "function": "add", "argc": 2}
{"op": "jmp",      "target": 10}
```

**Jump targets are instruction indices** within the same function's `body`
(`"target": 10` means "the eleventh instruction"). A target equal to
`body.len()` jumps past the end.

A complete program, written by hand and checked by this guide:

<!-- check: casm-json -->
```json
{
  "version": "1.0",
  "functions": {
    "main": {
      "params": [],
      "locals": [],
      "body": [
        {"op": "push_int", "value": 3},
        {"op": "push_int", "value": 2},
        {"op": "call", "function": "add", "argc": 2},
        {"op": "push_str", "value": "2 + 3 = "},
        {"op": "swap"},
        {"op": "cap_call", "name": "io.print", "argc": 2},
        {"op": "halt"}
      ]
    },
    "add": {
      "params": ["a", "b"],
      "locals": [],
      "body": [
        {"op": "store", "name": "a"},
        {"op": "store", "name": "b"},
        {"op": "load", "name": "a"},
        {"op": "load", "name": "b"},
        {"op": "add"},
        {"op": "ret"}
      ]
    }
  },
  "manifest": { "permissions": ["io.print"] }
}
```

<!-- check: output -->
```text
2 + 3 = 5
```

(`push_str` then `swap` puts the label *under* the sum, so `io.print` sees the
label first.)

### The manifest

`manifest.permissions` lists the capability names the program may call. The check
happens at run time, on every `cap_call`: a capability that is not in the list is
refused with `capability not declared in manifest: NAME`, even if the host has it
registered. When the Crush compiler lowers a program it adds every capability the
code actually calls, so a manifest only matters when you write or edit IR by hand
(or want to *restrict* a program).

## The text assembly

This is what `crushc --emit casm` prints and `crush-run run FILE.casm` /
`crush-compile` read. One instruction per line:

```casm
; a comment (# also works)
.func main              ; start of function "main"
    PUSH 40
    PUSH 2
    ADD
    CAP_CALL "io.print" 1
    JMP done            ; jump to a label
done:                   ; a label is "name:" on its own line (or before an instruction)
    HALT
```

- `.func NAME` begins a function. Functions share one flat code section; a `CALL`
  must name a function defined **somewhere** in the file (forward references are
  fine — the assembler runs two passes).
- `LABEL:` marks a jump target; `JMP`/`JZ`/`JNZ`/`ENTER_TRY` take a label name.
- Mnemonics are case-insensitive. Operands: `PUSH` takes a signed 64-bit integer,
  `PUSH_F64` a float, `PUSH_STR` a double-quoted string (Rust `{:?}` escapes), and
  `LOAD`/`STORE` a slot number `0`–`65535`.
- `CAP_CALL "name" argc` takes the capability name and the argument count (0–255).
- The assembler records `main` (or, failing that, the first `.func`) as the entry
  point and builds a function table. A file with no `.func` at all is a single
  anonymous routine starting at offset 0.

```casm
.func main
    PUSH 40
    PUSH 2
    ADD
    CAP_CALL "io.print" 1
    HALT
```

<!-- check: output -->
```text
42
```

`crush-run` does not infer permissions from a `.casm` file: pass the capabilities
the program uses with `--cap` (e.g. `crush-run run prog.casm --cap io.print`).

## The CVM1 binary

`crushc x.crush -o x.cvm1` writes this layout (all multi-byte integers
big-endian):

```
 offset  size   field
      0     4   magic            "CVM1"
      4     1   version          2   (versions 1 and 2 are accepted)
      5     2   manifest_len
      7     n   manifest         JSON: {"runtime", "permissions", "name"?, "functions"?, "entry"?}
            2   n_consts
            …   consts           n_consts × ( 2-byte length + UTF-8 bytes )
            4   code_len
            …   code             flat bytecode
```

The constant pool holds every string the code names: `PUSH_STR` literals, capability
names and function names. A capability name or a string is limited to 65 535 bytes
and the pool to 65 536 entries because indices are 16-bit. The `functions` table in
the manifest maps each function name to its byte offset in `code`; `entry` names the
function the VM starts in.

Each instruction is one opcode byte followed by a fixed-size operand:

| Operand | Size | Used by |
|---|---|---|
| none | 0 | most opcodes |
| `i64` | 8 | `PUSH`, `PUSH_BOOL` |
| `f64` | 8 | `PUSH_F64` |
| const index | 2 | `PUSH_STR`, `CALL`, `GET_FIELD`, `SET_FIELD`, `CAST`, `EXEC_LANG`, the `AI_*`/`DOM_*` opcodes |
| slot | 2 | `LOAD`, `STORE` |
| count | 2 | `NEW_ARRAY`, `NEW_TUPLE`, `NEW_LIST`, `NEW_VECTOR`, `NEW_SET`, `PICK`, `ROLL`, `SPAWN` |
| code offset | 4 | `JMP`, `JZ`, `JNZ`, `ENTER_TRY` (byte offset into `code`) |
| capability | 3 | `CAP_CALL`: 2-byte const index of the name + 1-byte argc |

Jumps in the binary are **byte offsets**, unlike the IR's instruction indices; the
assembler converts labels for you.

You can turn a binary back into text with `crush_lang_sdk::disassemble`; it prints
`.func` lines and synthesises `L<offset>:` labels for jump targets.

## Metadata and source maps

The IR keeps `meta.line`/`meta.col` on each instruction, and `casm::debug_info`
defines `DebugInfo`/`SourceLocation` for mapping a runtime failure back to the
source (`format_runtime_error_with_location`). The CVM1 binary carries none of it:
`Program::source_map` (line → code offset) exists only on a freshly assembled
program, for debuggers, and is not serialized.

## See also

- [Instruction Reference](instructions.md)
- [Serialization](serialization.md) — file extensions and version checks
- [CAST](../cast/README.md) — the layer above
