# Examples

Runnable Crush programs. Every program and every output block on these pages is
executed against crush-ast `3ae0b4a` by `scripts/check-examples.py`, so what you
read is what happens. Pages also record where a
language feature is *not yet implemented*, with the crush-ast ticket.

| Example | Pattern | Flags to run it |
|---------|---------|-----------------|
| [Fibonacci & Functions](fibonacci.md) | Recursion, typed signatures | — |
| [Arrays & Loops](arrays-loops.md) | Arrays, `for`, `break`/`continue`, FizzBuzz | — |
| [Exception Handling](exceptions.md) | `try`/`catch`/`throw` | — |
| [Structs (and Concurrency)](concurrency-structs.md) | Structs with methods; `spawn`/`await` | — |
| [Lambdas & Pipes](lambdas.md) | `\|>` pipelines, lambdas, closures | — |
| [Import Styles](imports.md) | Every import form, and why none loads yet | — |
| [System Info Report](sysinfo.md) | `env.*`, `time.*` capabilities | `--env --time` |
| [Build Pipeline](build-pipeline.md) | `process.exec`, fail-fast steps | `--process` |
| [Polyglot Pipeline](async-dom.md) | Python + JavaScript + Bash in one program | `--polyglot` |
| [Showcase: awesome-crush](awesome-crush.md) | Games, interpreters and an agent tool written by LLMs | varies |

The [verified corpus](../verified-corpus.md) has 120+ more, one small program per
behaviour, each with its exact output.

Run any of them with `crush run [flags] file.crush` (see
[Getting Started](../getting-started.md)).
