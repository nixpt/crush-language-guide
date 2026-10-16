# Crush Overview

> Verified against crush-ast `cb655f3` (2026-10-16).

**Crush** is a small, capability-based scripting language with polyglot blocks,
and the toolchain around it: a parser, a compiler to bytecode, a sandboxed VM,
and an intermediate representation (CAST) that other languages can be translated
into. It is **alpha software** — this guide documents what runs today and says so
when something doesn't.

## What Crush is

- **A language.** `let`, `fn`, `if`/`while`/`for`, `match`, `try`/`catch`,
  arrays and objects, closures and function values, structs with `impl` methods
  and `trait`s, green tasks, a pipeline operator. Dynamically typed at run time with
  optional compile-time type hints. See [Syntax](syntax.md).
- **Capability-gated.** A program can't print files, open sockets or start
  processes unless the host turns the matching capability on. Capability calls
  are ordinary dotted calls — `fs.read("x")`, `io.print("y")`. See
  [Capability System](capabilities.md).
- **Polyglot.** `@python -> out { }`, `@javascript { }` and `@bash { }` blocks
  run other languages and exchange variables with Crush. They currently run as
  ordinary subprocesses **outside** the capability model unless you build the
  optional sandbox. See [Polyglot Programming](polyglot.md).
- **A pipeline.** Source becomes CAST (an AST in JSON), then CASM (bytecode), then
  runs on a VM (`crush-vm`), with a faster VM, a JIT and ahead-of-time backends
  also in the repository ([Engines, AOT and Walkers](engines.md)). Walkers
  translate Python, JavaScript, Rust and other languages into the same CAST.

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
impl Point {
    fn distance_sq(self) { return self.x * self.x + self.y * self.y }
}

let points = [Point { x: 3, y: 4 }, Point { x: 1, y: 1 }]
let far = |p| p.distance_sq() > 10
let i = 0
while i < len(points) {
    let p = points[i]
    if far(p) {
        print("far: " + p.distance_sq())
    }
    i = i + 1
}
```

<!-- check: output -->
```text
far: 25
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
| Core language (functions, loops, `try`/`catch`, `match`) | works |
| Closures and function values | works on the VM; AOT refuses them by name |
| Structs, `impl`, `trait`, `@kind`, struct patterns | works on the VM; AOT refuses method calls by name |
| `spawn` / `yield` / `await`, `parallel_map` | works on the VM |
| `import` (multi-file programs) | not yet: CRUSH-110 |
| Capabilities, `@capabilities`, the standard library | works; the standard library is on by default |
| Polyglot: Python, JavaScript (declared `->` outputs), Bash | works (host authority by default); `@bash` sees no Crush variables today (#255) |
| Polyglot sandbox | opt-in build, verified on Linux with `bwrap` |
| CAST / CASM formats | documented in their own sections |

## Next Steps

- **[Syntax & Grammar](syntax.md)**
- **[Types](types.md)**
- **[Closures](closures.md)** and **[Structs, Methods and Kinds](structs.md)**
- **[Capability System](capabilities.md)**
- **[Polyglot Programming](polyglot.md)**
