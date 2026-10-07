# Examples

Runnable Crush programs. Every program and every output block on these pages is
executed against the real toolchain by `scripts/check-examples.py` (CI re-runs it
on every change), so what you read is what happens. Pages also record where a
language feature is *not yet implemented*, with the crush-ast ticket.

| Example | Pattern | Flags to run it |
|---------|---------|-----------------|
| [Fibonacci & Functions](fibonacci.md) | Recursion, typed signatures | — |
| [Arrays & Loops](arrays-loops.md) | Arrays, `for`, `break`/`continue`, FizzBuzz | — |
| [Exception Handling](exceptions.md) | `try`/`catch`/`throw` | — |
| [Structs (and Concurrency)](concurrency-structs.md) | Structs; `spawn` is not yet implemented | — |
| [Lambdas & Pipes](lambdas.md) | `\|>` pipelines; lambdas are not yet implemented | — |
| [Import Styles](imports.md) | Every import form, and why none loads yet | — |
| [System Info Report](sysinfo.md) | `env.*`, `time.*` capabilities | `--stdlib --env --time` |
| [Build Pipeline](build-pipeline.md) | `process.exec`, fail-fast steps | `--stdlib --process` |
| [Polyglot Pipeline](async-dom.md) | Python + JavaScript + Bash in one program | `--polyglot` |

Run any of them with `crush run [flags] file.crush` (see
[Getting Started](../getting-started.md)).
