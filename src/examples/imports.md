# Import Styles

> Source: `crates/core/crush-lang/walkers/tree-sitter-crush/test_imports.crush`

Crush has several import forms. Standard modules use `import`; external resources
and capabilities use `use @`.

```crush
// Standard module import
import io;
import fs as files;                    // aliased
import net { http_get, http_post };    // selective

// MCP server — wire a remote API as typed capabilities
use @mcp "https://api.github.com" { "issues.list", "repos.get" } as github;

// Capability import — grant specific cap handles under an alias
use @cap "fs.read" { "fs.read", "fs.list" } as reader;

// Polyglot import — pull a symbol from a language module
use @lang python "sys" { "version", "path" } as pysys;

// External resources
import @git "https://github.com/nixpt/exosphere.git" as exo;
import @http "https://example.com/data.json" as data;

fn main() {
    io.print("Imports working!");
}
```

## Form Reference

| Form | Purpose |
|------|---------|
| `import module` | Crush stdlib module (`io`, `fs`, `net`, `sys`, `math`, `time`, ...) |
| `import module as alias` | Module with alias |
| `import module { a, b }` | Selective import — only named symbols |
| `use @mcp "url" { tools } as alias` | Wire an MCP server as capabilities |
| `use @cap "cap.path" { names } as alias` | Import specific capability handles |
| `use @lang python "module" { symbols }` | Import a polyglot language module |
| `import @git "url" as alias` | Bind a git repository as a resource |
| `import @http "url" as alias` | Bind an HTTP resource |

All `use @...` forms are enforced by the capability system: the runtime only grants
the declared access; anything undeclared is denied at execution time.
