# Engines, AOT and Walkers

> Verified against crush-ast `aa07413` (2026-10-16), with rustc 1.96, gcc, Python
> 3.14 and Node 26 on the host.

One Crush program can run on several engines. crush-ast's rule for them is
**"the VM is exact; every other engine is exact or loud"**: an engine either
produces the VM's output or refuses the program by name. It never silently
produces something else. (Where that rule is broken today, this guide links the
crush-ast issue.)

| Engine | How you reach it | Status |
|---|---|---|
| CVM1 VM (scheduler) | `crush run`, `crush-run run` | the reference: everything in this guide |
| CVM1 portable VM | the browser build (`crush-web`, the guide's Run buttons) | same programs, same output; `parallel_map` runs items one after another |
| AOT via Rust or C | `crush-aotc` (from `cargo build -p crush-aot`) | a subset; refuses the rest by name |
| FastVM, Cranelift JIT | `crush-diff`, embedding | a smaller subset; refuse what they lack |

## Ahead-of-time compilation: `crush-aotc`

`crush-aotc` translates a program to Rust (compiled with `rustc`) or C (`gcc` /
`clang`) and builds a native shared library. `crush-aotc run` compiles and runs it
in one step; after the program's output it prints the entry function's return
value (`null` for a script):

```console
$ cat fib.crush
fn fib(n) {
    if n < 2 { return n }
    return fib(n - 1) + fib(n - 2)
}
let m = {"b": 2, "a": 1}
m["c"] = 3
print(m)
print(fib(20))
let s = "hello"
print(s[1])
$ crush-aotc run fib.crush                  # via rustc
{b: 2, a: 1, c: 3}
6765
e
null
$ crush-aotc run --backend gcc fib.crush    # via gcc
{b: 2, a: 1, c: 3}
6765
e
null
```

Other forms: `crush-aotc compile prog.crush -o prog.so` (a library),
`--emit rust` / `--emit c-source` (print the generated source), `--emit c --cc
clang`.

Run-time errors are the VM's errors (`crush(aot): division by zero`,
`crush(aot): arithmetic overflow`, `` crush(aotc): `P` is sealed: it has no field
`z` (fields: x) ``), and both backends compare maps and arrays by value, like the
VM.

### What AOT refuses

Anything the backends can't compile exactly stops `crush-aotc` with the
instruction it can't handle, before producing a binary. All of these were seen
with both backends:

| Program uses | Refusal |
|---|---|
| a lambda or closure | `` the Rust AOT backend cannot compile: `make_closure` (fn main, instruction 0) `` |
| a method call on a struct (`p.norm2()`) | `` the C AOT backend cannot compile: `call_member` (fn main, instruction 5) `` |
| `spawn` | `` `spawn` (green tasks) isn't supported on the Rust AOT backend yet (#161) `` |
| a `@python` block | `` the Rust AOT backend cannot compile: `exec_lang` (fn main, instruction 5) `` |
| most standard-library capabilities | `the C AOT backend cannot compile: cap_call 'str.to_upper' (fn main, instruction 26)` |

Plain functions, recursion, arrays, maps, strings and sealed structs without
methods do compile.

## Comparing engines: `crush-diff`

`crush-diff FILE...` runs each program on the VM and the other engines and
reports where they disagree. A loud refusal counts as a disagreement in outcome
class, so you can see which engines a program is out of reach for:

```console
$ crush-diff closures/counter.crush structs/impl-methods.crush
✗ closures/counter.crush  DIVERGED
    interpreter vs fastvm OUTCOME CLASS: A_ok=true C=Err("ExecutionError(\"Unknown opcode: load_cell\")")
✗ structs/impl-methods.crush  DIVERGED
    interpreter vs fastvm OUTCOME CLASS: A_ok=true C=Err("ExecutionError(\"Unknown opcode: call_member\")")

2 files · 0 agree (0 with notes) · 2 DIVERGED · 0 don't compile
```

## Walkers: other languages as input

A **walker** translates a source file in another language into CAST, which then
compiles and runs like Crush. This is separate from `@lang` blocks (which run a
real interpreter): walked code runs on the Crush VM, under its capabilities.
`crush-walk-run FILE` walks, compiles and runs a file by its extension
(`.py`, `.js`/`.ts`, `.rs`, `.c`, `.go`, `.zig`, `.sh`, `.dart`, `.wasm`, …);
`crush run` itself only takes `.crush`, `.casm` and `.cvm1`.

Walkers follow the same exact-or-loud rule. A Python program prints exactly what
`python3` prints:

```console
$ cat fact.py
def fact(n):
    return 1 if n <= 1 else n * fact(n - 1)

xs = [fact(i) for i in range(6)]
print(xs)
print({"a": 1, "b": [1, 2]})
$ crush-walk-run fact.py
[1, 1, 2, 6, 24, 120]
{'a': 1, 'b': [1, 2]}
```

and so does JavaScript, against `node`:

```console
$ cat fact.js
function fact(n) { return n <= 1 ? 1 : n * fact(n - 1); }
const xs = [];
for (let i = 1; i <= 3; i++) { xs.push(fact(i)); }
console.log(xs);
console.log(7 / 2, "done");
$ crush-walk-run fact.js
[ 1, 2, 6 ]
3.5 done
```

Constructs a walker can't translate exactly are refused at walk time, with the
source position:

```console
$ crush-walk-run map.js        # const xs = [1,2,3].map(x => fact(x));
Error: javascript@CAST: calling a method on anything but a plain name (`a.b.m()`, `"s".m()`, `f().m()`) is not supported by the JS walker yet
```

The Rust walker is the strictest: it only accepts what it can prove has Rust's
exact semantics (integer widths, `Debug` formatting), so expect refusals such as
`unsupported Rust Debug at 7:30: call argument needs a proven compatible Rust
type (CRUSH-xps-9)`. Simple code works:

```console
$ cat squares.rs
fn main() {
    let mut total = 0;
    for i in 1..=4 {
        total += i * i;
    }
    println!("sum of squares: {}", total);
}
$ crush-walk-run squares.rs
sum of squares: 30
```

## Next Steps

- **[Polyglot Programming](polyglot.md)**: running real interpreters instead
- **[CAST](../cast/index.md)**: what walkers produce
