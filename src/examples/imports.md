# Import Styles

> Verified against crush-ast `7f3fef31` (main, 2026-11-16).

Crush has one import that loads Crush code, `import a.b`, resolved **at compile
time** from `.crush` files (crush-ast CRUSH-110), and a few other forms. This page
lists each with what it does at the pinned commit. The rules for modules, packages
and `pub` are in [Modules, Packages and Visibility](../crush/modules.md).

| Form | What happens |
|------|------|
| `import util.strings`, `import util.strings as s`, `import util.strings { twice }` | loads `util/strings.crush` at compile time; see [Modules](../crush/modules.md) |
| `import io`, `import fs as files` (no such file) | compile error: `` `import fs`: module not found — no fs.crush in any of: … `` |
| `import @http "url" as x`, `import @git "url" as x`, `import @file "path" as x` | compile error: `is not supported yet: no Crush host can load an external resource` |
| `use @mcp "url" { tools } as alias` | compile error: `is not supported yet: no Crush host implements MCP client connections` |
| `use @cap "cap.path" { "names" } as alias` | compiles, refused before running: `not available in this host: cap.acquire` |
| `use @lang python "math" [as m]` | runs; see below |

The capabilities are not modules: `fs.read(...)` is available to a program run with
`--fs` without any import, and `import fs` looks for a file named `fs.crush`.

<!-- check: error -->
```crush
import fs as files
print("loaded")
```

<!-- check: error -->
```crush
use @mcp "https://api.github.com" { "issues.list", "repos.get" } as github
print("loaded")
```

<!-- check: error -->
```crush
import @http "https://example.com/data.json" as data
print("loaded")
```

<!-- check: runfail not available in this host: cap.acquire -->
```crush
use @cap "fs.read" { "read" } as r
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

## Sharing code between files

Put shared functions in a module and import it:

<!-- check: compile -->
```crush
// util/strings.crush
fn shout(s) { return str.to_upper(s) + "!" }
fn twice(s) { return s + s }
```

<!-- check: skip multi-file program: examples/verified/modules/import-forms -->
```crush
import util.strings as s
print(s.shout("hi"))
```

```text
HI!
```

Run it from the directory that holds both files (`crush run main.crush`), or point
`-L` / `CRUSH_PATH` at the directory that holds `util/`.
