# Import Styles

> **Not yet implemented.** Every form of `import` parses, but **none of them load
> anything** — the compiler lowers each to a capability that the runtime does not
> provide. The only import form that runs is `use @lang`, which only declares
> that a polyglot block will use a module. This is crush-ast **CRUSH-110** (open):
> today there is no way to share code between files.

| Form | Parses | Runs |
|------|:------:|------|
| `import io` / `import fs as files` / `import net { a, b }` | yes | fails: `unknown capability: module.load` |
| `use @mcp "url" { tools } as alias` | yes | fails: `unknown capability: mcp.connect` |
| `use @cap "cap.path" { names } as alias` | yes | fails: `unknown capability: cap.acquire` |
| `import @git "url" as alias`, `import @http "url" as alias` | yes | fails: `unknown capability: external.load` |
| `use @lang python "math" as math` | yes | runs; see below |

Each failing form is checked below, so this page will say so the day one starts
working:

<!-- check: nyi CRUSH-110 -->
```crush
import fs as files
print("loaded")
```

<!-- check: nyi CRUSH-110 -->
```crush
use @mcp "https://api.github.com" { "issues.list", "repos.get" } as github
print("loaded")
```

<!-- check: nyi CRUSH-110 -->
```crush
import @http "https://example.com/data.json" as data
print("loaded")
```

## `use @lang`

`use @lang <language> "<module>" as <alias>` declares a module for a polyglot
block. It is accepted and runs, but the alias is not wired to the block's
variables — the block still has to `import` the module itself:

<!-- check: flags --polyglot -->
```crush
use @lang python "math" as math

@python {
import math
v = math.factorial(5)
}
print(v)
```

<!-- check: output -->
```text
120
```

## Sharing code today

Put helper functions in the same file, or do the work in a polyglot block. The
only cross-file mechanism that exists is outside the language: run several
programs and pass data through files or the host.
