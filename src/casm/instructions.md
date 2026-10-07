# Instruction Set Reference

Every instruction has two spellings: the **JSON name** used in the CASM IR
(`"op": "push_int"`) and the **CVM1 mnemonic** used in the text assembly and the
binary (`PUSH`). The tables below give both, the operand, and the stack effect.
Behaviour was checked against the crush-ast `v0.3.9` VM; the examples at the end of
each section are run by this guide's checker.

## Reading stack effects

`a b → c` means: pop `b` (the **top**), pop `a`, push `c`. The rightmost value is
always the top of the stack. `…` is "whatever was below".

Operands in the text assembly follow the mnemonic: `PUSH 42`, `LOAD 3`,
`CAP_CALL "io.print" 1`. In the IR they are named fields next to `op`.

> **Two instruction sets.** The IR (`casm::OpCode`) is wider than the VM: it has
> names the VM bytecode does not (`break`, `continue`, `await` with a handle,
> `call_host`, `import_var`) and the VM bytecode has mnemonics the IR lowering never
> emits (`ROT`, `PICK`, `CAST`, the `MATH_*` family). [The last
> section](#what-lowers-to-cvm1) lists exactly which IR ops reach the VM.

## Stack

| JSON `op` | CVM1 | Operand | Stack effect | Notes |
|---|---|---|---|---|
| `push_int` | `PUSH` | `value` (i64) | `→ int` | |
| `push_float` | `PUSH_F64` | `value` (f64) | `→ float` | |
| `push_str` | `PUSH_STR` | `value` (string) | `→ str` | text form: quoted string |
| `push_bool` | `PUSH_BOOL` | `value` (bool; `1`/`0` in text) | `→ bool` | |
| `push_null` | `PUSH_NULL` | — | `→ null` | |
| `pop` | `POP` | — | `a →` | |
| `dup` | `DUP` | — | `a → a a` | |
| `swap` | `SWAP` | — | `a b → b a` | |
| `rot` | `ROT` | — | `a b c → b a c` | as observed on `v0.3.9`; **not** Forth's `ROT` |
| `pick` | `PICK n` | `n` | `… → … v` | copy the item `n` below the top (`PICK 2` copies the third) |
| `roll` | `ROLL n` | `n` | `… → … v` | *move* the item `n` below the top to the top |
| — | `NOP` | — | — | text/binary only |

```casm
.func main
    PUSH 1
    PUSH 2
    PUSH 3
    ROLL 2          ; stack is now 2 3 1
    CAP_CALL "io.print" 1
    CAP_CALL "io.print" 1
    CAP_CALL "io.print" 1
    HALT
```

<!-- check: output -->
```text
1
3
2
```

## Variables

| JSON `op` | CVM1 | Operand | Stack effect | Notes |
|---|---|---|---|---|
| `load` | `LOAD slot` | `name` | `→ v` | push the variable |
| `store` | `STORE slot` | `name` | `v →` | pop into the variable |
| `export_var` | — | `name` | — | IR only; lowers to `NOP` (the value stays on the stack) |
| `import_var` | — | `name` | — | IR only; **not lowered** |

In the IR a variable is a name; in CVM1 it is a numeric **slot** (0–65535) local to
the current call frame. Frames do not share slots: a callee cannot see its caller's
variables.

## Arithmetic and comparison

All binary operators pop `b` then `a` and push `a OP b`.

| JSON `op` | CVM1 | Effect | Notes |
|---|---|---|---|
| `add` `sub` `mul` | `ADD` `SUB` `MUL` | `a b → a∘b` | `ADD` also concatenates strings |
| `div` | `DIV` | `a b → a/b` | integer division on two ints (`7/2 = 3`), float otherwise |
| `mod` | `MOD` | `a b → a%b` | |
| `neg` | `NEG` | `a → -a` | |
| `eq` `ne` | `EQ` `NE` | `a b → bool` | |
| `lt` `gt` `le` `ge` | `LT` `GT` `LE` `GE` | `a b → bool` | |
| `and` `or` | `AND` `OR` | `a b → bool` | **eager** — both operands are already evaluated. The `&&` / `\|\|` operators of Crush compile to jumps, not to these |
| `not` | `NOT` | `a → bool` | logical not |
| `bit_and` `bit_or` `bit_xor` | `BITAND` `BITOR` `BITXOR` | `a b → a∘b` | |
| `bit_not` | `BITNOT` | `a → ~a` | |
| `shl` `shr` | `SHL` `SHR` | `a b → a<<b` / `a>>b` | |

```casm
.func main
    PUSH 10
    PUSH 3
    SUB                 ; 10 - 3
    CAP_CALL "io.print" 1
    PUSH 7
    PUSH 2
    DIV                 ; integer division
    CAP_CALL "io.print" 1
    PUSH 12
    PUSH 10
    BITAND
    CAP_CALL "io.print" 1
    PUSH 1
    PUSH 4
    SHL
    CAP_CALL "io.print" 1
    HALT
```

<!-- check: output -->
```text
7
3
8
16
```

## Control flow

| JSON `op` | CVM1 | Operand | Stack effect | Notes |
|---|---|---|---|---|
| `jmp` | `JMP label` | `target` | — | unconditional |
| `jmp_if_not` | `JZ label` | `target` | `cond →` | jump if `cond` is **falsy** |
| `jmp_if` | `JNZ label` | `target` | `cond →` | jump if `cond` is truthy |
| `call` | `CALL name` | `function`, `argc` | `args… → [result]` | see below |
| `ret` | `RET` | — | `[v] →` | return to the caller |
| `halt` | `HALT` | — | — | stop the whole program |
| `enter_try` | `ENTER_TRY label` | `target` | — | push an exception handler |
| `exit_try` | `EXIT_TRY` | — | — | pop it again (normal exit of the `try` body) |
| `throw` | `THROW` | — | `v →` | unwind to the nearest handler, which receives `v` on its stack |
| `break` `continue` | — | — | — | in the IR enum only; the compiler lowers loops to `jmp`s and never emits these |

Jump operands are **instruction indices** in the IR and **byte offsets** in the
binary; the text assembler takes label names. A value is *falsy* if it is `false`,
`null`, `0`, `0.0`, the empty string or an empty array; everything else (including
the string `"0"`) is truthy.

**Calling convention.** The caller pushes the arguments **last first**, then
`CALL`s. The callee's body begins with one `STORE` per parameter, in declaration
order, which pops the first argument first. `RET` returns to the caller; a function
that produces a value leaves it on the stack for `RET`. Crush functions always end
with `PUSH_NULL` / `RET` if they have no explicit `return`.

```casm
.func main
    PUSH 5              ; counter
    STORE 0
loop:
    LOAD 0
    JZ done             ; stop when the counter reaches 0
    LOAD 0
    CAP_CALL "io.print" 1
    LOAD 0
    PUSH 1
    SUB
    STORE 0
    JMP loop
done:
    PUSH 4
    CALL double
    CAP_CALL "io.print" 1
    HALT
.func double
    STORE 0
    LOAD 0
    PUSH 2
    MUL
    RET
```

<!-- check: output -->
```text
5
4
3
2
1
8
```

**Exceptions.** `ENTER_TRY handler` records where to resume; `THROW` pops a value,
unwinds, and jumps to `handler` with that value on top of the stack.

```casm
.func main
    ENTER_TRY handler
    PUSH_STR "boom"
    THROW
    EXIT_TRY            ; not reached
    JMP end
handler:
    CAP_CALL "io.print" 1   ; prints the thrown value
end:
    HALT
```

<!-- check: output -->
```text
boom
```

## Collections and objects

| JSON `op` | CVM1 | Operand | Stack effect | Notes |
|---|---|---|---|---|
| `new_array` | `NEW_ARRAY n` | `size` | `v₁…vₙ → array` | pops `n` values. **IR quirk:** lowering ignores `size` and emits `NEW_ARRAY 0` — build arrays with `new_array` + `array_push`, as the compiler does |
| `array_push` / `arr_push` | `ARR_PUSH` | — | `array v → array` | |
| `array_pop` / `arr_pop` | `ARR_POP` | — | `array → array v` | |
| `index` / `arr_get` | `ARR_GET` | — | `array i → v` | also indexes objects/strings |
| `arr_set` | `ARR_SET` | — | `array i v → array` | |
| `len` / `arr_len` | `ARR_LEN` | — | `array → n` | works on strings too |
| `make_range` | `MAKE_RANGE` | — | `start end → range` | `1..4` yields 1, 2, 3 |
| `new_tuple` `new_list` `new_vector` `new_set` | `NEW_TUPLE n` etc. | `size` | `v₁…vₙ → coll` | plus `TUPLE_PUSH` `LIST_PUSH` `VECTOR_PUSH` `SET_PUSH` |
| `new_obj` | `NEW_OBJ` | — | `→ obj` | empty object |
| `new_struct` | `NEW_OBJ` | `name` | `→ obj` | the struct name is dropped on lowering |
| `set_field` | `SET_FIELD "f"` | `name` or `field` | `obj v → obj` | |
| `get_field` | `GET_FIELD "f"` | `name` or `field` | `obj → v` | |

```casm
.func main
    PUSH 10
    PUSH 20
    PUSH 30
    NEW_ARRAY 3
    DUP
    ARR_LEN
    CAP_CALL "io.print" 1       ; 3
    PUSH 1
    ARR_GET
    CAP_CALL "io.print" 1       ; 20
    NEW_OBJ
    PUSH 5
    SET_FIELD "x"
    GET_FIELD "x"
    CAP_CALL "io.print" 1       ; 5
    HALT
```

<!-- check: output -->
```text
3
20
5
```

## Strings, math, types

String operations pop their operands in the order shown and push the result.

| JSON `op` | CVM1 | Stack effect |
|---|---|---|
| `str_contains` | `STR_CONTAINS` | `s pattern → bool` |
| `str_split` | `STR_SPLIT` | `s delim → array` |
| `str_replace` | `STR_REPLACE` | `s old new → s` |
| `str_join` | `STR_JOIN` | `array delim → s` |
| `str_starts_with` `str_ends_with` | `STR_STARTS_WITH` `STR_ENDS_WITH` | `s prefix → bool` |
| `str_to_upper` `str_to_lower` `str_trim` | `STR_TO_UPPER` `STR_TO_LOWER` `STR_TRIM` | `s → s` |
| `math_pow` | `MATH_POW` | `base exp → float` |
| `math_sqrt` `math_abs` `math_round` `math_floor` `math_ceil` | `MATH_SQRT` … | `x → float` |
| `type_of` | `TYPEOF` | `v → str` — `"int"`, `"float"`, `"str"`, `"bool"`, `"null"`, `"array"`, `"map"` (an object), `"tuple"`, … |
| `cast` | `CAST "t"` | `v → v'` — `"int"`, `"float"`, `"string"` |
| — | `VEC_ADD` `VEC_DOT` `MAT_MUL` | vector/matrix helpers, CVM1 only |

```casm
.func main
    PUSH_STR "aXb"
    PUSH_STR "X"
    PUSH_STR "-"
    STR_REPLACE
    CAP_CALL "io.print" 1       ; a-b
    PUSH 2
    PUSH 10
    MATH_POW
    CAP_CALL "io.print" 1       ; 1024.0
    PUSH_STR "12"
    CAST "int"
    PUSH 1
    ADD
    CAP_CALL "io.print" 1       ; 13
    HALT
```

<!-- check: output -->
```text
a-b
1024.0
13
```

(The Crush-level equivalents of these live in the `--stdlib` capabilities —
`str.*`, `math.*`, `conv.*` — and compile to `CAP_CALL`s, not to these opcodes. See
the [standard library](../crush/stdlib.md).)

## Capabilities

| JSON `op` | CVM1 | Operand | Stack effect |
|---|---|---|---|
| `cap_call` | `CAP_CALL "name" argc` | `name`, `argc` | `a₁…aₙ → [result]` |
| `call_host` | — | `capsule`, `ic_id`, `method`, `argc` | IR only, **not lowered** |
| `call_interface` | — | `handle`, `method`, `argc` | IR only, **not lowered** |

`CAP_CALL` pops `argc` arguments (the first argument was pushed first) and invokes
the named host capability. Whether it then pushes a result depends on the
capability: `io.print` returns nothing, `str.len` returns a number. The compiler
knows this and drops the `pop` it would otherwise emit after a statement-position
call. If the capability is not registered by the host the VM stops with `unknown
capability: NAME`; if it is registered but missing from the manifest, with
`capability not declared in manifest: NAME`. See the
[capability chapter](../crush/capabilities.md).

## Polyglot, concurrency, AI and DOM

| JSON `op` | CVM1 | Notes |
|---|---|---|
| `exec_lang` | `EXEC_LANG "json"` | run a `@python { }` / `@javascript { }` / `@bash { }` block; the operand is a JSON string with `lang`, `code`, `var_count` and the marshalling lists. Needs the matching `polyglot.<lang>` capability — see [Polyglot](../crush/polyglot.md) |
| `spawn` `yield` `await` | `SPAWN n` `YIELD` `AWAIT` | dispatched to the `concurrency_native.spawn/yield/await` gates; **stubs** — nothing is scheduled |
| `ai_query` … (13 names) | `AI_QUERY` … (10 opcodes) | **stubs**, see [AI-Native CAST](../cast/ai-native.md#what-actually-runs) |
| `dom_query` `dom_mutate` `dom_event_listener` | `DOM_QUERY` … | **stubs**: lowered to `NOP`; the `dom_native.*` gates exist only for hand-written CVM1 |

## What lowers to CVM1

`crush_lang_sdk::compile::casm_to_vm` is the bridge from the JSON IR to a runnable
program. It handles exactly these IR operations:

| | |
|---|---|
| **Lowered faithfully** | `push_int` `push_float` `push_str` `push_bool` `push_null` `pop` `dup` `swap` `load` `store` `add` `sub` `mul` `div` `mod` `neg` `eq` `ne` `lt` `gt` `le` `ge` `and` `or` `not` `call` `cap_call` `ret` `halt` `jmp` `jmp_if` `jmp_if_not` `enter_try` `exit_try` `throw` `array_push` `array_pop` `len` `index` `arr_get` `arr_set` `make_range` `str_contains` `str_split` `str_replace` `str_join` `new_obj` `get_field` `set_field` `exec_lang` `spawn` `yield` `await` |
| **Lowered with a loss** | `new_array` (size ignored — always empty), `new_struct` (→ `NEW_OBJ`, name dropped), `export_var` (→ `NOP`), `dom_*` and all `ai_*` including `ai_capability_discovery`, `ai_adaptation_request`, `ai_semantic_switch` (→ `NOP`) |
| **Rejected** | everything else the `casm` crate defines — `arr_push` `arr_pop` `arr_len` `bit_*` `shl` `shr` `rot` `pick` `roll` `type_of` `cast` `math_*` `str_starts_with` `str_ends_with` `str_to_*` `str_trim` `new_tuple` `new_list` `new_vector` `new_set` `*_push` `import_var` `call_host` `call_interface` `break` `continue` — fail with `Unsupported CVM1 opcode: NAME at FUNCTION:INDEX` |

So for hand-written programs the **text assembly is the more capable form**: it
reaches `ROT`, `PICK`, `CAST`, `MATH_*`, the bit operations, tuples and sets that
the IR route refuses. For programs *compiled from Crush*, the compiler stays inside
the "lowered faithfully" set.

<!-- check: casm-json -->
<!-- check: runfail Unsupported CVM1 opcode: shl -->
```json
{
  "version": "1.0",
  "functions": { "main": { "body": [
    {"op": "push_int", "value": 1},
    {"op": "shl"},
    {"op": "cap_call", "name": "io.print", "argc": 1},
    {"op": "halt"}
  ] } },
  "manifest": { "permissions": ["io.print"] }
}
```

(The block above is expected to fail: `shl` is in the IR but not lowered.)
