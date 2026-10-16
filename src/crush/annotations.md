# Annotations

> Verified against crush-ast `3ae0b4a` (2026-10-16).

An annotation is an `@name` form written before a declaration (or at the top of
a file). Three kinds exist:

| Annotation | Effect |
|---|---|
| `@capabilities [ ... ]` | **enforced**: the program may use only these capabilities (plus the ambient ones). See [Capability System](capabilities.md#declaring-what-a-program-uses-capabilities). |
| `@kind( ... )` | **semantics**: chooses the object model of the `struct` that follows. See [Structs, Methods and Kinds](structs.md#kind-choosing-object-semantics). |
| `@module`, `@decision`, `@invariant`, `@wip`, `@temporary`, `@errors` | **metadata**: recorded in the program's CAST for tools and agents; they do not change what the program does. |

(`@python { ... }` and the other `@lang` blocks look similar but are code, not
annotations: see [Polyglot Programming](polyglot.md).)

## Manifest annotations

These describe a module and its decisions in a form an agent can query instead
of parsing comments. Each takes a `{ key: value }` body; `@decision` and
`@invariant` also take a name string.

```crush
@module {
    purpose: "Show the manifest annotations"
    exports: [area]
}

@decision "ints-not-floats" {
    chose: "integer sides"
    over: ["float sides"]
    because: "exact output in the docs"
    revisit-if: ["we need fractional sizes"]
}

@invariant "area-non-negative" {
    description: "area never returns a negative number"
    applies_to: [area]
}

@errors {
    Overflow: rare
}
fn area(w, h) {
    return w * h
}

@temporary {
    reason: "demo"
    expires-when: "never"
    added: "2026-10-16"
}
fn helper() { return 1 }

print(area(3, 4))
print(helper())
```

<!-- check: output -->
```text
12
1
```

| Annotation | Fields |
|---|---|
| `@module` | `purpose`, `exports`, `invariants`, `related` |
| `@decision "name"` | `chose`, `over`, `because`, `revisit-if` |
| `@invariant "name"` | `description`, `applies_to`, `check` |
| `@wip` | `intent`, `done`, `todo`, `unresolved` |
| `@temporary` | `reason`, `expires-when`, `added` |
| `@errors` | `Variant: likely` / `possible` / `rare` |

`@wip` marks unfinished work on the next declaration:

```crush
@wip {
    intent: "parse the config"
    done: ["read the file"]
    todo: ["validate keys"]
    unresolved: []
}
fn parse() { return "partial" }
print(parse())
```

<!-- check: output -->
```text
partial
```

Hyphenated keys such as `revisit-if` and `expires-when` parse (an old `crushc`
hang on `revisit-if`, crush-ast #38, is fixed). An `@invariant`'s `check` is
stored, not executed. (`crushc --invariant-runtime` emits calls to an
`invariant.evaluate` capability at the top of each targeted function, but
`crush-run` does not provide one, so such a program is refused: `not available in
this host: invariant.evaluate`.)

## The AI-native statements

CAST has AI nodes (queries, tool chains, agent delegation, goals, …) for programs
that agents emit as JSON; they are described in [AI-Native CAST](../cast/ai-native.md).
They are **not** Crush source functions: `ai_semantic_match(...)` in a `.crush`
file is just an undefined name.

<!-- check: error -->
```crush
let m = ai_semantic_match("refund", "billing", 0.8)
print(m)
```

```text
[compile] Undefined function: ai_semantic_match
```

The one AI statement with Crush syntax, `semantic_switch`, parses but is refused
at compile time, because it would have compiled to a silent no-op (crush-ast
CRUSH-265):

<!-- check: runfail `semantic_switch` isn't supported yet (CRUSH-265) -->
```crush
fn route(text) {
    semantic_switch text {
        case "billing question":
            return "billing"
        fallback:
            return "human"
    }
}
print(route("refund please"))
```

```text
[compile] `semantic_switch` isn't supported yet (CRUSH-265): it would compile to a no-op
```

## Next Steps

- **[Capability System](capabilities.md)**
- **[AI-Native CAST](../cast/ai-native.md)**
