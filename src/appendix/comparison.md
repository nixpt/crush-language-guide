# Language Comparisons

How Crush relates to the languages people usually compare it with. Crush is **alpha**:
the language is small, the standard library is a set of host capabilities, and several
features in its design (lambdas, imports, an executing AI layer) are not implemented
yet. The comparisons below are about what is real today.

## What Crush is for

- **Running untrusted or semi-trusted scripts with explicit authority.** A program can
  only do what the host switched on (`--fs`, `--net`, `--process`, …); everything else
  is simply not registered. See [Capabilities](../crush/capabilities.md).
- **Embedding.** The VM is a Rust library (`crush-lang-sdk`) with quotas for steps,
  stack, output and call depth, so a host can bound what a script costs.
- **One front door for several languages.** `@python`, `@javascript` and `@bash`
  blocks run inside a Crush program, with values marshalled in and out. They are host
  subprocesses, so they are gated by `--polyglot` and carry the host's full authority
  unless you use the opt-in sandbox lane. See [Polyglot](../crush/polyglot.md).

It is **not** a general-purpose replacement for Python or JavaScript: there is no
package ecosystem, no lambdas, no working `import`, and a small standard library.

## Crush vs Python

| | Crush | Python |
|---|---|---|
| Typing | dynamic; annotations (`x: Int`) are optional and checked at compile time | dynamic; hints are not enforced |
| Ambient authority | none — files, network, processes need a capability flag | everything the OS user can do |
| Execution | compiled to CVM1 bytecode, run by a Rust VM with quotas | compiled to bytecode, run by CPython |
| Functions | `fn`, named only (no lambdas yet) | `def`, `lambda` |
| Ecosystem | tiny; reach Python through `@python { }` | huge |

<!-- check: output -->
```crush
fn greet(name) {
    print("Hello, " + name + "!")
}

greet("Alice")
```

```text
Hello, Alice!
```

In Python that is `def greet(name): print(f"Hello, {name}!")` — no string
interpolation in Crush, so concatenate with `+`.

## Crush vs JavaScript

| | Crush | JavaScript |
|---|---|---|
| Authority | capability-gated | Node has full OS access; browsers are sandboxed by the platform |
| Functions | `fn`, no closures or lambdas yet | first-class, closures |
| Async | `async`/`await`/`spawn` are parsed but not scheduled — treat them as unimplemented | native promises and an event loop |
| Syntax | braces, optional semicolons, `let`, double-quoted strings only | similar, single quotes allowed |

## Crush vs Rust

Crush's VM is written in Rust and Crush embeds into Rust programs, but the languages
are opposites in philosophy: Rust is statically typed with ownership; Crush is a
dynamic scripting language whose safety comes from the host (capabilities and quotas)
rather than the type system.

## Crush vs Bash

| | Crush | Bash |
|---|---|---|
| Values | typed (ints, floats, strings, arrays, objects) | strings |
| Running programs | `process.exec` with `--process`, or an `@bash { }` block | native |
| Errors | `try` / `catch`, `throw` | exit codes |
| Authority | capability-gated | everything the user can do |

## Performance

Crush has an interpreter (CVM1), a second interpreter (FastVM, aimed at hot loops),
and — in the repository, not on crates.io — ahead-of-time backends (`crush-aot`,
`crush-aotc`) that translate CASM to Rust or C. The repository's own benchmark
(`docs/benchmarks/BENCHMARKS.md`, one process per iteration) gives these figures
relative to the CVM1 interpreter:

| Tier | `simple` (return 42) | `compute` (14-op arithmetic chain) |
|---|---|---|
| CVM1 interpreter | 1.0× | 1.0× |
| FastVM | 0.09× | 0.5× |
| AOT via rustc | 42× | 130× |
| AOT via gcc | 54× | 317× |
| AOT via clang | 55× | 378× |

Read these with care. The programs are tiny, the AOT compilers constant-fold the
whole `compute` chain into a single value, FastVM loses on tiny programs and is meant
for loops with thousands of iterations, and the scripting-language rows in that
document measure interpreter start-up, not throughput. They show that the AOT path
*can* remove the stack machine's overhead; they are not a claim about how fast real
Crush programs run. The AOT backends also reject programs that use instructions they
do not support.

## When to use Crush

✅ **A good fit:**

- You embed a scripting layer in a Rust application and need to bound and gate what
  scripts can do.
- You want agents or tools to emit programs as validated data ([CAST](../cast/index.md))
  rather than as source text.
- You are experimenting with a capability-first language.

❌ **Look elsewhere when:**

- You need a mature ecosystem, libraries or tooling — use Python or JavaScript.
- You need closures, modules or imports today.
- You need hardened isolation of *foreign-language* code: polyglot blocks run as host
  processes unless you build the optional bubblewrap sandbox lane, which is Linux-only.

## Migrating to Crush

### From Python

1. `def` → `fn`; indentation → braces.
2. `print(a, b)` → `print(x)` takes one argument; use `io.print(a, b)` for several
   (they are joined with no separator).
3. `f"…{x}"` → `"…" + x`.
4. `and`/`or`/`not` → `&&`/`||`/`!`; `range(n)` → `0..n`.
5. Anything that touches files, the network or processes needs the matching
   capability flag.
6. Keep code you cannot port in an `@python { }` block while you migrate.

### From JavaScript

1. `function` → `fn`; `const`/`let` → `let` (there is no `const`).
2. Strings use double quotes only.
3. `console.log(x)` → `print(x)`.
4. No arrow functions yet — name the function.
5. Keep code you cannot port in an `@javascript { }` block.

### From Bash

1. Wrap shell commands in `@bash { }` (needs `--polyglot`) or call
   `process.exec("cmd", "arg")` (needs `--process`).
2. Use Crush for the control flow and data handling around them.
