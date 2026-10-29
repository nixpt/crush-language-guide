# Quick Reference

Cheat sheets for the toolchain, the Crush language and CASM. Every code block that
can run is run by the guide's checker against crush-ast `b1791d8e`. Details live in
the chapters linked from each heading.

## Command line ([Getting Started](../getting-started.md))

| Command | Does |
|---|---|
| `crush run FILE [flags]` | run a `.crush`, `.casm` (text) or `.cvm1` file |
| `crush build FILE.crush` | compile to `.cvm1` |
| `crush-run run FILE [flags]` | same as `crush run`; all the capability flags live here |
| `crush-run caps [FILE]` | list the capabilities of your build, or what FILE needs (runs nothing) |
| `crushc FILE.crush -o OUT.cvm1` | compile; `--emit casm\|ast\|types` prints a layer; `-C` only checks |
| `crush-compile FILE.casm -o OUT.cvm1 --cap NAME` | assemble CASM text |
| `crush repl` / `crush-repl` | interactive REPL (`.help`, `.quit`) |
| `crush doctor` | which polyglot interpreters are on `PATH` |
| `crush-aotc run FILE.crush` | ahead-of-time compile via rustc (`--backend gcc`) and run |
| `crush-walk-run FILE.py` | walk a Python/JS/Rust/… file to CAST and run it |

Capability flags (everything is **off** unless you pass it, except the standard
library, which `--no-stdlib` removes): `--fs` `--fs-root DIR` `--env` `--time`
`--net` `--process` `--crypto` `--db PATH` `--graphics` `--bus` `--task` `--akg`
`--polyglot` `--cap NAME`. A program that needs an ungranted capability is refused
before it runs. Quotas:
`--max-steps` (default 1,000,000), `--max-stack` (4,096), `--max-output` (1 MiB),
`--max-call-depth` (256).

## Language ([Syntax](../crush/syntax.md))

### Variables and functions

```crush
let x = 42
let name: String = "Alice"

fn add(a: Int, b: Int) -> Int {
    return a + b
}

fn greet(who) {
    print("Hello, " + who)
}

greet(name)
print(add(x, 1))
```

<!-- check: output -->
```text
Hello, Alice
43
```

- Semicolons are optional. Comments are `//` and `#`. Strings use `"…"` or `'…'`.
- A function returns a value only with `return`; falling off the end yields `null`.
- `print(x)` takes exactly one argument; `io.print(a, b, …)` takes any number.
- No `let mut`, no `T?` types, no working `import` (CRUSH-110).

### Closures ([Closures](../crush/closures.md))

```crush
fn make_counter() {
    let c = 0
    return || {
        c = c + 1
        return c
    }
}
let next = make_counter()
next()
print(next())
let sq = |x| x * x
print(5 |> sq)
```

<!-- check: output -->
```text
2
25
```

### Control flow ([Control Flow](../crush/control_flow.md))

```crush
let n = 3
if n > 5 {
    print("big")
} else if n > 1 {
    print("medium")
} else {
    print("small")
}

let i = 0
while i < 2 {
    i = i + 1
}

for k in 0..3 {
    print(k)
}

for item in ["a", "b"] {
    print(item)
}
```

<!-- check: output -->
```text
medium
0
1
2
a
b
```

`0..3` excludes the end, `0..=3` includes it. `for` also walks a string's
characters and a map's keys. `break` and `continue` work in `while` and `for`.
`match v { 1 => "one", P { x: a } => a, _ => "other" }` matches literals,
bindings and struct patterns; `return match …` returns its value.

### Operators ([Operators](../crush/operators.md))

`+ - * / %` · `== != < > <= >=` · `&& || !` or `and or not` (short-circuit) · unary
`-` · pipeline `|>` · ranges `a..b`, `a..=b`. There is no `**`, `//`, `+=`, bitwise
operator or ternary. `Int` overflow and division by zero are run-time errors.

### Errors

```crush
try {
    throw "disk full"
} catch e {
    print("caught: " + e)
}
```

<!-- check: output -->
```text
caught: disk full
```

### Structs and objects ([Types](../crush/types.md))

```crush
struct Point { x: Int, y: Int }
impl Point {
    fn sum(self) { return self.x + self.y }
}
let p = Point { x: 3, y: 4 }
let o = {"name": "crush"}
o["lang"] = "en"
print(p.sum())
print(o.name + "/" + o["lang"])
```

<!-- check: output -->
```text
7
crush/en
```

Structs are sealed (no undeclared fields), references by default
(`@kind(semantics: value(copy))` for values), and `==` compares fields. See
[Structs, Methods and Kinds](../crush/structs.md).

### Capabilities ([Capabilities](../crush/capabilities.md))

Capability calls are dotted and have **no `@`**. They exist only if you enabled
them:

<!-- check: flags --fs -->
```crush
if fs.exists("notes.txt") {
    print(fs.read("notes.txt"))
} else {
    print("no notes")
}
```

<!-- check: output -->
```text
no notes
```

```crush
io.print("a", "b", 3)
print(str.len("héllo"))
```

<!-- check: output -->
```text
ab3
6
```

### Polyglot blocks ([Polyglot](../crush/polyglot.md))

`@python -> out { }`, `@javascript -> out { }` and `@bash { }` run as host
subprocesses, only with `--polyglot`, and with the host's full authority (no sandbox
by default). Names a block reads are passed in; the names after `->` come back.
Without the flag the program is refused:

<!-- check: runfail --polyglot -->
```crush
@python {
    print("hello from python")
}
```

## Types ([Types](../crush/types.md))

| Type | Example | Notes |
|---|---|---|
| `Int` | `42`, `0x2A`, `0b101` | 64-bit, checked overflow |
| `Float` | `3.14` | no exponent form |
| `String` | `"hello"`, `'hello'` | UTF-8; `len` counts bytes |
| `Bool` | `true` | |
| `Null` | `null` | |
| array | `[1, 2, 3]` | |
| object | `{"key": "value"}` | insertion-ordered |
| struct | `struct P { x, y }` | one line; `P { x: 1, y: 2 }` |
| function | `\|x\| x + 1`, `fn` names | values; closures capture by reference |

Annotations (`: Int`, `-> Int`) are checked at compile time and are optional.

## Capabilities at a glance

| Always on | `io.print` `io.read` `str.concat` `str.len` `conv.chr` `conv.ord` |
|---|---|
| Standard library (default) | `str.*` `math.*` `conv.*` `collections.*` `json.*` `path.*` `regex.*` `sys.args` … |
| `--fs` | `fs.read` `fs.write` `fs.exists` `fs.list` `fs.mkdir` … |
| `--env` | `env.get` `env.all` `env.home_dir` |
| `--time` | `time.now` `time.now_ms` `time.now_iso` `time.elapsed` `time.sleep` |
| `--net` | `net.http_get` `net.http_post` |
| `--process` | `process.exec` |
| `--crypto` | `crypto.sha256` `crypto.random` |
| `--db PATH` | `db.query` `db.execute` |
| `--polyglot` | `@python` `@javascript` `@bash` |

## CASM text assembly ([CASM](../casm/index.md))

```casm
.func main
    PUSH 40
    PUSH 2
    ADD
    CAP_CALL "io.print" 1
    HALT
```

<!-- check: output -->
```text
42
```

| Group | Mnemonics |
|---|---|
| Stack | `PUSH n` `PUSH_F64 x` `PUSH_STR "s"` `PUSH_BOOL 0\|1` `PUSH_NULL` `POP` `DUP` `SWAP` `ROT` `PICK n` `ROLL n` |
| Variables | `LOAD slot` `STORE slot` |
| Arithmetic | `ADD` `SUB` `MUL` `DIV` `MOD` `NEG` |
| Compare / logic | `EQ` `NE` `LT` `GT` `LE` `GE` `AND` `OR` `NOT` |
| Bits | `BITAND` `BITOR` `BITXOR` `BITNOT` `SHL` `SHR` |
| Control | `JMP label` `JZ label` `JNZ label` `CALL name` `RET` `HALT` `ENTER_TRY label` `EXIT_TRY` `THROW` |
| Capabilities | `CAP_CALL "name" argc` |
| Collections | `NEW_ARRAY n` `ARR_GET` `ARR_SET` `ARR_LEN` `ARR_PUSH` `ARR_POP` `NEW_OBJ` `GET_FIELD "f"` `SET_FIELD "f"` |
| Strings / math | `STR_CONTAINS` `STR_SPLIT` `STR_REPLACE` `STR_JOIN` `STR_TRIM` `STR_TO_UPPER` `MATH_POW` `MATH_SQRT` … |

Stack effects and the JSON-IR names are in the
[Instruction Reference](../casm/instructions.md). Remember: arguments are pushed
**first argument first** (`PUSH_STR "a"`, `PUSH_STR "b"`, `CAP_CALL "io.print" 2`
prints `ab`), and a `.casm` file needs `--cap` for every capability it calls.
