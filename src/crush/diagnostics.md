# Errors and Diagnostics

> Verified against crush-ast `bad81048` (v0.9.0, 2026-10-31).

This page is about how the tools *report* a problem; the language's own
`try`/`catch`/`throw` is in [Control Flow](control_flow.md#errors-try--catch--throw).
Since 0.9.0 `crush`, `crushc` and `crush-run` report problems with one JSON schema,
and a semantic error points at the line and column it is on.

## Text (the default)

A mistake the compiler can see is reported before anything runs:

<!-- check: error -->
```crush
let x = 1
print(y)
```

```text
[compile] Undefined variable: y
```

Syntax errors say where the parser gave up:

```text
[compile] Parse errors: Unexpected token at line 1, column 12: unexpected token in expression: newline
```

## JSON: `--message-format json`

Add `--message-format json` to `crush run`, `crush-run run`, `crushc` or `crush build`
and every error is one
JSON object on its own line, for an editor, a language-server bridge or an agent
that should not have to parse prose. Running the program above:

```sh
crush-run run e.crush --message-format json
```

```json
{"code":"E-TP01","level":"error","file":"e.crush","line":2,"col":7,"message":"Undefined variable: y","hint":null}
```

`crushc -C e.crush --message-format json` prints the identical record: there is one
schema, with seven fields in this order:

| Field | Meaning |
|---|---|
| `code` | a stable code: `E-TP01` (a semantic / type error), `E-PP01` (a parse error), `E-RT05` (a run-time error: here division by zero), `E-CAPS` (a capability the run does not grant) |
| `level` | `error`, or `note` for a non-fatal remark |
| `file` | the file as you named it |
| `line`, `col` | 1-based position, or `null` when the problem has none (a run-time error, a refused capability) |
| `message` | the same text the default output shows |
| `hint` | a suggestion, or `null` |

A syntax error carries its position the same way:

```json
{"code":"E-PP01","level":"error","file":"s.crush","line":1,"col":12,"message":"unexpected token in expression: newline","hint":null}
```

and a refused run says what it lacks:

```json
{"code":"E-CAPS","level":"error","file":"h.crush","line":null,"col":null,"message":"needs capabilities this run does not grant; nothing was run: http.get","hint":"no grant in this build provides them"}
```

Wrong arity is caught at compile time, with the call's position:

```json
{"code":"E-TP01","level":"error","file":"ar.crush","line":2,"col":1,"message":"Function 'f' expects 1 arguments, found 2","hint":null}
```

The stream has one record per error and nothing else on standard output, so
`... --message-format json | jq` is safe. The program's own `print` output is
separate, and the `[steps=…]` summary is on standard error as ever.

## Where to go next

- [Debugging](debugging.md): stop at a line and look at the variables.
- [Capability System](capabilities.md): what `E-CAPS` refusals mean and which flag fixes each.
