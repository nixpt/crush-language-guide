# Import Styles

> Verified against crush-ast `d04bc60a` (2026-10-29).

> **Not yet implemented.** Every form of `import` parses, but **none of them load
> anything** — the compiler lowers each to a capability that the runtime does not
> provide, so the program is refused before it runs. The only import form that
> works is `use @lang`, which declares a module for polyglot blocks. This is
> crush-ast **CRUSH-110** (open): today there is no way to share code between files.

| Form | Parses | Runs |
|------|:------:|------|
| `import io` / `import fs as files` / `import net { a, b }` | yes | refused: `not available in this host: module.load` |
| `use @mcp "url" { tools } as alias` | yes | refused: `not available in this host: mcp.connect, mcp.get_tool` |
| `use @cap "cap.path" { names } as alias` | yes | refused: `not available in this host: cap.acquire` |
| `import @git "url" as alias`, `import @http "url" as alias` | yes | refused: `not available in this host: external.load` |
| `use @lang python "math" [as m]` | yes | runs; see below |

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

`use @lang <language> "<module>" [as <alias>]` writes the import into every later
block of that language, under the module's own name and the alias:

<!-- check: flags --polyglot -->
```crush
use @lang python "math" as m

@python -> v {
v = m.factorial(5) + math.factorial(3)
}
print(v)
```

<!-- check: output -->
```text
126
```

## Sharing code today

Put helper functions in the same file, or do the work in a polyglot block. The
only cross-file mechanism that exists is outside the language: run several
programs and pass data through files or the host.
