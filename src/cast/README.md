# CAST — the Crush AST

**CAST** is the JSON abstract syntax tree that sits between source languages and
[CASM](../casm/index.md). The Crush parser produces it, the polyglot *walkers*
produce it from other languages, and an AI agent can write it directly (see
[AI-Native CAST](ai-native.md)). The compiler (`crush_frontend`) turns it into CASM.

```
 Crush source ──parse──┐
 Python/JS/… ──walker──┼──▶ CAST (JSON) ──compile──▶ CASM IR ──▶ CVM1 ──▶ VM
 an agent's JSON ──────┘
```

This page is the schema reference. It is derived from `crates/crush-cast/src/lib.rs`
in crush-ast (`v0.3.9`); the examples are accepted by `crush_cast::validate_json`,
compiled and run by this guide's checker.

## Document structure

```json
{
  "cast_version": "0.1.0",
  "entry": "main",
  "lang": null,
  "functions": {
    "main": { "params": [], "body": [ /* statements */ ], "meta": {} }
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `cast_version` | string | yes | format version; see [Serialization](#serialization) |
| `entry` | string | yes | name of the function to run first |
| `lang` | string or null | yes (may be `null`) | language that produced the tree (`"crush"`, `"python"`, …) |
| `functions` | object | yes | function name → function |
| `ai_meta` | object | no | program-level AI metadata — see [AI-Native CAST](ai-native.md) |
| `manifest` | object | no | the `@module` navigation manifest (purpose, exports, invariants) used by `crush-index` |
| `exhaustive_sites`, `wip`, `temporaries`, `decisions` | | no | compiler-populated tooling nodes (`@wip`, `@temporary`, `@decision` blocks) |

A **function** is:

| Field | Type | Required | Description |
|---|---|---|---|
| `params` | array of `[name, type]` pairs | yes | `[["n", "Int"]]`; use `"Any"` for untyped |
| `body` | array of statements | yes | |
| `meta` | object | **yes** | free-form (`{}` is fine). Forgetting it is the most common validation error |
| `is_async` | bool | no | tooling hint |
| `annotations` | object | no | `@errors`/`@reads`/`@writes`/`@covers` annotations |

There is no top-level `imports` or `structs` table: imports and struct definitions
are *statements* (`Import`, `StructDef`).

## A complete program

<!-- check: cast-json -->
```json
{
  "cast_version": "0.1.0",
  "entry": "main",
  "lang": null,
  "functions": {
    "square": {
      "params": [["n", "Int"]],
      "body": [
        { "type": "Return",
          "value": { "type": "BinaryOp", "operator": "*",
                     "left":  { "type": "Var", "name": "n" },
                     "right": { "type": "Var", "name": "n" } } }
      ],
      "meta": {}
    },
    "main": {
      "params": [],
      "body": [
        { "type": "VarDecl", "name": "total", "value": { "type": "IntLiteral", "value": 0 }, "type_hint": "Int" },
        { "type": "For", "variable": "i",
          "iterable": { "type": "ArrayLiteral", "elements": [
              { "type": "IntLiteral", "value": 1 },
              { "type": "IntLiteral", "value": 2 },
              { "type": "IntLiteral", "value": 3 } ] },
          "body": [
            { "type": "Assign", "target": "total",
              "value": { "type": "BinaryOp", "operator": "+",
                         "left":  { "type": "Var", "name": "total" },
                         "right": { "type": "Call", "function": "square",
                                    "args": [ { "type": "Var", "name": "i" } ] } } }
          ] },
        { "type": "If",
          "condition": { "type": "BinaryOp", "operator": ">",
                         "left": { "type": "Var", "name": "total" },
                         "right": { "type": "IntLiteral", "value": 10 } },
          "then_body": [
            { "type": "ExprStmt", "expr": { "type": "CapabilityCall", "name": "io.print",
                "args": [ { "type": "StringLiteral", "value": "sum of squares: " },
                          { "type": "Var", "name": "total" } ], "meta": {} } }
          ],
          "else_body": null }
      ],
      "meta": {}
    }
  }
}
```

<!-- check: output -->
```text
sum of squares: 14
```

Every node is an object with a `"type"` tag. `meta` is optional on almost every
node (it defaults to `{}`), with one exception: **`CapabilityCall` requires its
`meta`**. The Crush parser fills `meta` with `line` and `col`.

## Statements

| `type` | Fields | Notes |
|---|---|---|
| `VarDecl` | `name`, `value`, `type_hint` | declare a variable (`type_hint` defaults to `"Any"`) |
| `Assign` | `target` (a name), `value` | |
| `SetField` | `target` (expression), `field`, `value` | `p.x = 3` |
| `Export` | `name`, `value` | publish a variable to the host / polyglot caller |
| `ExprStmt` | `expr` | expression evaluated for effect; its value is dropped |
| `If` | `condition`, `then_body`, `else_body` | `else_body` is `null` or a statement list |
| `While` | `condition`, `body` | |
| `For` | `variable`, `iterable`, `body` | |
| `Return` | `value` (nullable) | |
| `Break`, `Continue` | — | |
| `TryCatch` | `body`, `error_var`, `handler` | |
| `Throw` | `value` | |
| `FunctionDef` | `name`, `params`, `body` | nested function definition |
| `StructDef` | `name`, `fields` | `fields` is `[[name, type], …]` |
| `LangBlock` | `lang`, `code`, `variables`, `imports`, `deps` | a polyglot `@lang { }` block; `variables` are marshalled in, `meta.polyglot_output` names the variable marshalled out |
| `Import` | `import` | an `ImportStatement` — parsed, but **not executed**: see below |
| `DomMutate`, `DomEventListener` | | DOM nodes; compile to `NOP` today |
| `AI` | `ai_type`, … | AI statements — see [AI-Native CAST](ai-native.md) |

`Import`, in particular, is accepted by the schema in six flavours (`CrushModule`,
`PolyglotModule`, `MCPImport`, `Capability`, `External`, `SecureEnv`), but at run
time an import lowers to an unregistered `module.load` capability and fails — Crush
imports are not implemented yet (CRUSH-110).

## Expressions

| `type` | Fields |
|---|---|
| `IntLiteral`, `FloatLiteral`, `StringLiteral`, `BoolLiteral` | `value` |
| `NullLiteral` | — |
| `Var` | `name` |
| `BinaryOp` | `operator`, `left`, `right` — operators as the language spells them: `+ - * / % == != < > <= >= && \|\|` |
| `UnaryOp` | `operator` (`-`, `!`), `operand` |
| `Call` | `function` (a name), `args` — a call to a user function |
| `CapabilityCall` | `name` (`"io.print"`), `args`, **`meta` (required)** |
| `ArrayLiteral`, `TupleLiteral`, `ListLiteral`, `VectorLiteral`, `SetLiteral` | `elements` |
| `ObjectLiteral` | `properties`: `[[key, expression], …]` |
| `Index` | `target`, `index` |
| `GetField` | `target`, `field` |
| `NewStruct` | `name` |
| `Range` | `start`, `end` |
| `Match` | `expression`, `arms` (`{pattern, body}` pairs) |
| `Pipeline` | `segments` — `a \|> b \|> c` |
| `Spawn`, `Await`, `Yield` | task / async forms (stubs, see [CASM](../casm/instructions.md#polyglot-concurrency-ai-and-dom)) |
| `Lambda` | `params`, `body` — the node exists, but the Crush parser cannot produce it: lambdas are not implemented (CRUSH-75) |
| `VectorMath` | `operator`, `args` |
| `DomQuery` | `query_type`, `selector` |
| `AI` | `ai_type`, … — see [AI-Native CAST](ai-native.md) |

Note the naming: it is `GetField` (not `FieldAccess`), `ArrayLiteral` (there is no
`MapLiteral` — use `ObjectLiteral`) and `Var` (not `Identifier`).

### Patterns (for `Match`)

| `type` | Fields |
|---|---|
| `Literal` | `value` (an expression) |
| `Identifier` | `name` (binds the value) |
| `Struct` | `name`, `fields`: `[[field, pattern], …]` |
| `Wildcard` | — |

```json
{ "type": "Match",
  "expression": { "type": "Var", "name": "n" },
  "arms": [
    { "pattern": { "type": "Literal", "value": { "type": "IntLiteral", "value": 6 } },
      "body": [ { "type": "ExprStmt", "expr": { "type": "StringLiteral", "value": "six" } } ] },
    { "pattern": { "type": "Wildcard" },
      "body": [ { "type": "ExprStmt", "expr": { "type": "StringLiteral", "value": "other" } } ] }
  ] }
```

## Types

Type positions (`type_hint`, parameter and field types) hold a `CastType`. It is
serialized the usual serde way: a bare string for the simple types,
`{"Variant": payload}` for the others.

| JSON | Meaning |
|---|---|
| `"Int"`, `"Float"`, `"F32"`, `"BigInt"`, `"Complex"`, `"String"`, `"Bool"`, `"Null"` | scalars |
| `"Any"` | dynamic (the default) |
| `{"Array": "Int"}`, `{"List": …}`, `{"Vector": …}`, `{"Set": …}`, `{"Map": …}`, `{"Tensor": …}` | homogeneous collections of the inner type |
| `{"Tuple": ["Int", "String"]}` | fixed-length sequence |
| `{"Struct": "Point"}`, `{"TypeRef": "Point"}` | named types |
| `{"Lambda": {"params": […], "returns": …}}` | function types |

Types are **hints**: the compiler records them but the VM is dynamically typed.

<!-- check: cast-json -->
```json
{
  "cast_version": "0.1.0", "entry": "main", "lang": null,
  "functions": { "main": { "params": [], "meta": {}, "body": [
    { "type": "VarDecl", "name": "xs", "type_hint": { "Array": "Int" },
      "value": { "type": "ArrayLiteral", "elements": [ { "type": "IntLiteral", "value": 7 } ] } },
    { "type": "ExprStmt", "expr": { "type": "CapabilityCall", "name": "io.print", "meta": {},
      "args": [ { "type": "Index", "target": { "type": "Var", "name": "xs" },
                  "index": { "type": "IntLiteral", "value": 0 } } ] } }
  ] } }
}
```

<!-- check: output -->
```text
7
```

## Metadata

`meta` on a node is an open JSON object. The Crush parser writes `line` and `col`
(1-based); walkers add their own keys. `crush_frontend` copies `line`/`col` onto the
CASM instructions it emits, which is how a runtime error gets pointed at a source
line. Nothing in `meta` changes what a program does, with one exception the
compiler reads: `LangBlock.meta.polyglot_output` (the variable to marshal back).

## Validation

`crush_cast::validate_json(&str)` checks a document against the schema and returns
errors **with a JSON path and a hint** for the mistakes agents make most often. Only
the first error is reported, because serde stops at the first one.

<!-- check: cast-json -->
<!-- check: runfail unknown variant `Print` -->
```json
{ "cast_version": "0.1.0", "entry": "main", "functions": { "main": {
    "params": [], "meta": {},
    "body": [ { "type": "Print", "value": { "type": "StringLiteral", "value": "hi" } } ] } } }
```

The error for that document is `functions.main.body[0].type: unknown variant
`Print`, expected one of `VarDecl`, `Assign`, …`, with the hint *"Statement type
'Print' doesn't exist. Use ExprStmt with CapabilityCall(\"print\") instead"*. Other
built-in hints cover `Identifier`/`Literal` expressions, a missing `Function.meta`,
`prompt` instead of `query` in an AI query, and an object where a
`DelegationStrategy` string belongs.

Validation is structural. It does not check that a called function exists or that a
capability name is real; the compiler and the VM do.

## Serialization

`crush_cast::Program` can be written and read as JSON (the canonical form) or as
CBOR:

| Extension | Codec |
|---|---|
| `.cast.json`, anything else | JSON (pretty-printed) |
| `.castb`, `.cbor` | CBOR (`cbor4ii`), no header or magic |

`Program::deserialize` / `load` check `cast_version` and refuse a different **major**
than `CAST_VERSION` (`"0.1"`): `version mismatch at cast boundary: expected 0.1,
found …`. The corpus in `examples/cast/` uses `"0.1"` / `"0.1.0"`.

> **Known inconsistency (crush-ast `v0.3.9`).** The Crush front end stamps the trees
> it produces `cast_version: "1.0.0"`, which the versioned loader then rejects — so a
> CAST dump from the compiler cannot be re-loaded with `Program::load`, though
> `serde_json` and `validate_json` accept it. When you write CAST by hand or from an
> agent, use `"0.1.0"`.

<!-- check: cast-load-fails version mismatch at cast boundary: expected 0.1, found 1.0.0 -->
<!-- check: cast-json -->
```json
{ "cast_version": "1.0.0", "entry": "main", "lang": null,
  "functions": { "main": { "params": [], "body": [], "meta": {} } } }
```

## From CAST to CASM

`crush_frontend::compile_cast(&program)` (or `compile_cast_owned`) walks the tree and
emits [CASM IR](../casm/structure.md). The control-flow statements lower to jumps:

- `If` → condition, `jmp_if_not` over the then-branch, `jmp` over the else-branch.
- `While` → test at the top, `jmp_if_not` to the exit, `jmp` back.
- `For` over an array → an index loop (`len`/`index`), as shown in
  [CASM Examples](../casm/examples.md#9-what-the-compiler-writes).
- `TryCatch` → `enter_try`, the body, `exit_try`, `jmp` past the handler; the handler
  starts by storing the thrown value into `error_var`.
- `CapabilityCall` → arguments in order, then `cap_call name argc` (a `pop` follows
  when the call is a statement and the capability returns a value).
- `Call` → arguments **last first**, then `call function argc`.
