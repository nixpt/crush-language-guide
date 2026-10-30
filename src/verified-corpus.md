# The Verified Corpus

Besides the examples on its pages, this guide keeps a **corpus of small, standalone
Crush programs** in [`examples/verified/`](https://github.com/nixpt/crush-language-guide/tree/main/examples/verified),
one behaviour per program, each stored next to the exact output it produces. It is
the evidence behind the chapters: every claim about the language was first
observed by running one of these programs.

> Verified against crush-ast `c1cc21fb` (the commit in the repository's
> `CRUSH_AST_COMMIT` file). 123 programs.

| Area | Programs | Covers |
|---|---:|---|
| `basics/` | 11 | literals, `print` vs `io.print`, semicolons, one-line expressions, comments, return values, scoping, annotations, Nepali keywords |
| `operators/` | 10 | arithmetic, comparison, `and`/`or`/`not`, short-circuit, string `+`, `\|>`, overflow, division by zero |
| `strings/` | 6 | indexing, `str.*`, `conv.chr`/`ord`, escapes; string methods and slices that don't exist |
| `collections/` | 11 | arrays, `array.pop`, maps (insertion order, subscripts, iteration), `collections.*`, `json.*` |
| `control-flow/` | 9 | `if`, `while`/`break`/`continue`, ranges, `match` as expression and statement |
| `functions/` | 5 | definitions, arity checks, no defaults, top-level visibility, the call-depth quota |
| `closures/` | 11 | lambdas, function values, capture by reference, counters, loop capture, recursion |
| `structs/` | 11 | literals, sealing, equality, `impl`, traits, value semantics, C3, bound methods, constructors |
| `match/` | 3 | struct patterns, and their compile errors |
| `errors/` | 6 | `try`/`catch`/`throw`, rethrow, what `catch` can't catch, `result.*` |
| `modules/` | 2 | `import` (refused), `export` |
| `capabilities/` | 9 | refusal before running, `--fs` and `--fs-root`, `@capabilities`, `io.read`, `sys.args`, `math.random` |
| `polyglot/` | 15 | `--polyglot`, `-> outputs`, JavaScript, chaining, `use @lang`, isolation, errors, bash |
| `concurrency/` | 7 | `spawn`/`yield`/`await`, `async fn`, `parallel_map` and its rules |
| `annotations/` | 3 | manifest annotations, `@wip`, `@capabilities` |
| `ai-native/` | 2 | the refused `semantic_switch`, AI expressions not in source |
| `casm/` | 2 | running CASM text with `--cap` |

## The files

For each program `NAME`:

| File | Meaning |
|---|---|
| `NAME.crush` / `NAME.casm` | the program; its first comment lines say what it shows |
| `NAME.out` | its exact standard output |
| `NAME.err` | present when the program must **fail**: every line of it must appear in the error output |
| `NAME.flags` | the `crush-run` flags it needs (`--polyglot`, `--fs --fs-root .`, …) |
| `NAME.stdin` | what it reads from standard input (otherwise it reads end-of-file) |
| `NAME.needs` | host programs it needs (`python3`, `node`); skipped, not failed, without them |

Programs whose first line says **PITFALL** show behaviour that is wrong today and
link the crush-ast issue: when the issue is fixed, the program's expected output
changes and the corpus fails, which is the signal to update the guide.

| Pitfall | Issue |
|---|---|
| `polyglot/bash`: a `@bash` block sees no Crush variables | [#255](https://github.com/nixpt/crush-ast/issues/255) |
| `polyglot/header-comment-pitfall`: `//` on a block header → `Undefined variable` | [#266](https://github.com/nixpt/crush-ast/issues/266) |

## Running it

```sh
# crush-ast at the pinned commit, with buckets beside it
git clone https://github.com/nixpt/crush-ast && git -C crush-ast checkout "$(cat CRUSH_AST_COMMIT)"
git clone https://github.com/nixpt/buckets
(cd crush-ast && cargo build -p crush-lang-sdk)

scripts/verify-examples --bin-dir crush-ast/target/debug        # the corpus
scripts/check-examples.py --bin-dir crush-ast/target/debug \
    --crush-ast crush-ast                                         # every block on the pages
```

`verify-examples` runs each program in a fresh temporary directory with
`crush-run run <flags> --max-steps 50000000` and a 60-second timeout, and prints
a diff for any output that changed. `--bless` rewrites the `.out` files from a run;
read the new output before committing it. The repository's CI runs both scripts
against the pinned crush-ast commit on every pull request.
