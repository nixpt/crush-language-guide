# Crush Overview

**Crush** is a small, capability-based scripting language with polyglot blocks,
and the toolchain around it: a parser, a compiler to bytecode, a sandboxed VM,
and an intermediate representation (CAST) that other languages can be translated
into. It is **alpha software** — this guide documents what runs today and says so
when something doesn't.

## What Crush is

- **A language.** `let`, `fn`, `if`/`while`/`for`, structs, `match`, `try`/`catch`,
  arrays and objects, a pipeline operator. Dynamically typed at run time with
  optional compile-time type hints. See [Syntax](syntax.md).
- **Capability-gated.** A program can't print files, open sockets or start
  processes unless the host turns the matching capability on. Capability calls
  are ordinary dotted calls — `fs.read("x")`, `io.print("y")`. See
  [Capability System](capabilities.md).
- **Polyglot.** `@python { }`, `@javascript { }` and `@bash { }` blocks run
  other languages and exchange variables with Crush. They currently run as
  ordinary subprocesses **outside** the capability model unless you build the
  optional sandbox. See [Polyglot Programming](polyglot.md).
- **A pipeline.** Source becomes CAST (an AST in JSON), then CASM (bytecode), then
  runs on a VM (`crush-vm`), with a faster VM, a JIT and ahead-of-time backends
  also in the repository.

## Hello, Crush

```crush
print("Hello, Crush!")
```

<!-- check: output -->
```text
Hello, Crush!
```

Run it with the toolchain built from [crush-ast](https://github.com/nixpt/crush-ast)
(see [Getting Started](../getting-started.md)):

```sh
crush run hello.crush
```

## A taste

```crush
struct Point { x: Int, y: Int }

fn distance_sq(p) {
    return p.x * p.x + p.y * p.y
}

let p = new Point()
p.x = 3
p.y = 4
print(distance_sq(p))
```

<!-- check: output -->
```text
25
```

## Security model, in short

1. **Deny by default.** Every capability group (`--fs`, `--net`, `--process`,
   `--polyglot`, …) is off until you enable it on the command line (or register
   it, when embedding).
2. **Quotas.** Instruction count, stack depth, output size, call depth and
   wall-clock time for polyglot blocks are bounded.
3. **Honest limits.** Polyglot blocks run with the host's authority in the default
   build; the bubblewrap sandbox is opt-in at build time. The
   [capability chapter](capabilities.md#what-is-not-enforced) lists what is *not*
   enforced.

## Where things stand

| Area | Status |
|---|---|
| Core language (functions, loops, structs, `try`/`catch`, `match` expressions) | works |
| Lambdas and closures, `import`, `spawn`/`async`/`await` | not yet — see the chapters for ticket links |
| Capabilities and `--stdlib` | works; small |
| Polyglot: Python, JavaScript, Bash | works (host authority by default) |
| Polyglot sandbox | opt-in build, verified on Linux with `bwrap` |
| CAST / CASM formats | documented in their own sections |

## Next Steps

- **[Syntax & Grammar](syntax.md)**
- **[Types](types.md)**
- **[Capability System](capabilities.md)**
- **[Polyglot Programming](polyglot.md)**
