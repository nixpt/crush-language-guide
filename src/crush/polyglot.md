# Polyglot Programming

> Verified against crush-ast `d04bc60a` (2026-10-29), with Python 3.14, Node 26 and
> bash 5.3 on the host.

A Crush program can embed code from other languages with `@language { ... }`
blocks. This chapter describes what actually happens when you run one today —
which languages work, how values cross the boundary, how errors and timeouts
behave, and, importantly, **how much isolation you do and don't get**.

> **Status: alpha, and the security story is the part to read carefully.** By
> default a polyglot block is an ordinary subprocess running with *your* user's
> authority. An optional bubblewrap sandbox exists but is **off by default** and
> not enabled by any command-line flag. See [Sandbox and authority](#sandbox-and-authority).

## The model in one paragraph

A block's source text is handed to a real interpreter — `python3 -c`, `node -e`,
or `bash -c` — as a **child process**. Crush marshals some variables in, runs the
interpreter, captures its standard output, and (for Python and JavaScript)
marshals back the variables the block **declares** with `-> names`. There is no embedded WebAssembly runtime, no
WASI capability bridge, and no in-process interpreter.

## Languages

| Block | Runs | Aliases |
|---|---|---|
| `@python { }` | `python3 -c` | `@python3`, `@py` |
| `@javascript { }` | `node -e` | `@js`, `@node`, `@es6`, `@ecmascript` |
| `@bash { }` | `bash -c` | `@sh` |

The interpreter must be on `PATH`; `crush doctor` checks which ones it finds. Any
other tag (`@rust`, `@go`, `@c`, …) parses, but the program is refused before it
runs (`not available in this host: polyglot.rust`).

<!-- check: runfail not available in this host: polyglot.rust -->
<!-- check: flags --polyglot -->
```crush
@rust {
    fn main() {}
}
```

(crush-ast also ships **walkers** for Rust, Go, C, Zig, Wasm and others. A walker
translates a *source file* into CAST for compilation — it is a separate
mechanism, driven by the `crush-walker` tool, and is not what an `@lang { }`
block does.)

## Enabling polyglot execution

Polyglot is **off by default**, because running another interpreter is full
ambient authority. Turn it on per run:

```sh
crush run --polyglot program.crush        # same flag on crush-run
```

Without it the program is refused before anything runs (`--polyglot:
polyglot.python`):

<!-- check: runfail polyglot.python -->
```crush
@python {
print("hi")
}
```

An embedding host enables it explicitly with
`HostCapsBuilder::polyglot(&["python", "javascript", "bash"])`; each language is
gated by its own capability name (`polyglot.python`, `polyglot.javascript`,
`polyglot.bash`).

## Output

Whatever the block writes to standard output appears in the program's output, in
order. Two details to know: the block's output is **trimmed** (so it carries no
trailing newline), and anything written to standard error is discarded when the
block succeeds.

<!-- check: flags --polyglot -->
```crush
print("one")
@python {
print("two")
}
print("three")
```

<!-- check: output -->
```text
one
twothree
```

If you want the following output on a new line, end the block's output with an
explicit blank line (`print()`), or print from Crush.

## Passing values in and out

### Python and JavaScript

For `@python` and `@javascript` blocks:

- **In (automatic):** every name the block *reads* that is a Crush variable
  already in scope (a `let`, a parameter, a loop variable, or an earlier block's
  output) is injected as a variable of that name, with its type preserved.
- **Out (declared):** the names after `->` in the block header are marshaled back
  and become (or assign) Crush variables at that line. Nothing else leaves the
  block. Use `-> name` for one and `-> (a, b)` for several.

<!-- check: flags --polyglot -->
```crush
let count = 10
let base = 5
@python -> total {
tmp = base * 3
total = tmp * 2
}
print(total)
print(count)
```

<!-- check: output -->
```text
30
10
```

Here `base` goes in, `total` comes out, and `tmp` stays inside the block (using it
afterwards is a compile error, `Undefined variable`). JavaScript works the same
way; values travel as JSON:

<!-- check: flags --polyglot -->
```crush
let n = 5
let tags = ["a", "b"]
@javascript -> out {
const out = [n * 2, tags.length, tags.join("+")]
}
print(out)
```

<!-- check: output -->
```text
[10, 2, a+b]
```

Several outputs:

<!-- check: flags --polyglot -->
```crush
let xs = [2, 4, 4, 4, 5, 5, 7, 9]
@python -> (mean, spread) {
mean = sum(xs) / len(xs)
spread = max(xs) - min(xs)
}
print(mean)
print(spread)
```

<!-- check: output -->
```text
5.0
7
```

Listing a name the block never binds is a compile error; a name bound only on
some paths is a run-time error naming it (`output variable 'r' was not bound by
the block`), never a silent `null`:

<!-- check: error -->
```crush
@python -> missing {
x = 1
}
print(missing)
```

```text
[compile] @python block declares output `missing` but never binds it; add `missing = …` at the block's top level, or drop it from `->`
```

Everything after the opening `{` is the guest's source, including the rest of
the header line, so a Crush `//` comment there is Python code. With an output list
that syntax error is currently reported as `[compile] Undefined variable: m`
(crush-ast [#266](https://github.com/nixpt/crush-ast/issues/266)). Put comments
above the block, or use the guest's own comment syntax inside it.

**Blocks without `->` (being phased out).** A block with no output list still
exports its *last top-level assignment*, as in earlier releases, but the compiler
now warns on standard error, and warns again if that overwrites an existing Crush
variable. The next release drops the implicit export, so declare your outputs:

```text
warning: @python block exports `count` implicitly; add `-> count` to declare it
warning: @python block overwrites the existing Crush variable `count`; declare `-> count` to make the overwrite explicit
```

Values travel as JSON, so the shareable types are exactly these:

| Crush | Python | JavaScript |
|---|---|---|
| Int, Float | `int`, `float` | `number` |
| String | `str` | `string` |
| Bool | `bool` | `boolean` |
| Null | `None` | `null` |
| Array | `list` | `Array` |
| Object | `dict` | `Object` |

<!-- check: flags --polyglot -->
```crush
let n = 5
let tags = ["a", "b"]
let cfg = {"k": 1}
@python -> out {
out = [n * 2, len(tags), cfg["k"], None, True]
}
print(out)
```

<!-- check: output -->
```text
[10, 2, 1, null, true]
```

An output variable that can't be serialised to JSON (a class instance, an open
file, a function) fails the block with a clear error rather than being dropped:

<!-- check: runfail cannot marshal output variable(s) obj -->
<!-- check: flags --polyglot -->
```crush
@python -> obj {
class C:
    pass
obj = C()
}
print(1)
```

Blocks compose through Crush variables, across languages:

<!-- check: flags --polyglot -->
```crush
let x = 1
@python -> y {
y = x + 1
}
@javascript -> z {
const z = y * 10
}
@python -> w {
w = z + 1
}
print(w)
```

<!-- check: output -->
```text
21
```

Blocks inside functions and loops see the enclosing scope:

<!-- check: flags --polyglot -->
```crush
let total = 0
for i in 0..3 {
    @python -> sq {
sq = i * i
    }
    total = total + sq
}
print(total)
```

<!-- check: output -->
```text
5
```

Python and JavaScript state does **not** persist between blocks: each block is a
fresh interpreter, and only the declared outputs carry over. You cannot define a
function in one block and call it from Crush or from another block.

<!-- check: flags --polyglot -->
```crush
@python -> a {
a = 1
hidden = 2
}
@python -> r {
r = "hidden" in globals()
}
print(a)
print(r)
```

<!-- check: output -->
```text
1
false
```

### Imports for blocks: `use @lang`

`use @lang python "module"` (optionally `as alias`) writes the import into every
later `@python` block, so each block doesn't have to repeat it. Each block is
still its own process:

<!-- check: flags --polyglot -->
```crush
use @lang python "math"
use @lang python "json" as j
@python -> (val, text) {
val = math.factorial(5)
text = j.dumps({"a": 1})
}
print(val)
print(text)
```

<!-- check: output -->
```text
120
{"a": 1}
```

### Bash

`@bash` blocks have no value marshaling: only their printed output comes back,
and `->` on a `@bash` block is a compile error (`` `->` output lists are not
supported for @bash: it has no value marshaling ``).

> **Known bug ([crush-ast #255](https://github.com/nixpt/crush-ast/issues/255)).**
> Earlier releases passed the function's top-level `let`s to a `@bash` block as
> environment variables. Since explicit outputs landed (CRUSH-270) a `@bash` block
> receives **no** Crush variables, and `$name` silently expands to the empty
> string:

<!-- check: flags --polyglot -->
```crush
let name = "crush"
@bash {
echo "hello [$name]"
}
```

<!-- check: output -->
```text
hello []
```

Until that is fixed, compute the value in a `@python` block and print it, or
write it to a file the `@bash` block reads. Bash inherits the host environment
(`$HOME`, `$PATH`, …) in the default, unsandboxed lane.

## Errors

If the interpreter exits non-zero, the program stops with a
`LangRuntimeError`. The message is the guest's own stderr, prefixed with the
**Crush source line of the block**, so a Python traceback is attributed to the
right place in your `.crush` file:

<!-- check: runfail at .crush line 3 -->
<!-- check: flags --polyglot -->
```crush
print("a")
print("b")
@python {
raise ValueError("x")
}
```

```text
[runtime] @python block raised a runtime error: (at .crush line 3) Traceback (most recent call last):
  File "<string>", line 2, in <module>
    raise ValueError("x")
ValueError: x
```

A guest failure is **not** catchable with Crush `try`/`catch`
([Control Flow](control_flow.md#what-catch-does-not-catch)). Handle expected
failures inside the block (`try:` / `except:` in Python) and return a value that
says what happened. Failures to *start* a sandboxed block — package resolution,
missing `bwrap` — are reported separately as `sandbox setup failed`, so a
provisioning problem is never mistaken for a bug in your code.

## Timeouts

Every block runs under a **wall-clock limit of 30 seconds** (`Quotas::max_wall_time_ms`,
default `30_000`). At the deadline the interpreter's whole process group is killed
and the program ends with:

```text
[runtime] 'polyglot.python' exceeded its 30000ms wall-clock quota and was killed
```

(crush-ast CRUSH-19.) The limit is a field of `Quotas`, so it is configurable
when you embed the VM; `crush-run` doesn't expose a flag for it. In the sandboxed
lane the limit also covers package provisioning. The instruction quota
(`--max-steps`) does not apply to time spent inside a guest.

## Sandbox and authority

**Default (no sandbox).** A polyglot block is a plain child process of the Crush
runtime and inherits its environment, working directory, user and network. It is
**not** subject to the capability flags in [Capability System](capabilities.md):
`--fs-root` does not confine it, and withholding `--net` or `--process` does not
stop a block from opening sockets or running commands. This was verified: with
only `--polyglot`, a `@python` block reads `/etc/hostname`, and a `@bash` block
runs `id` and `cat`.

<!-- check: flags --polyglot -->
```crush
@python {
host = open("/etc/hostname").read().strip()
}
print(len(host) > 0)
```

<!-- check: output -->
```text
true
```

Only use `--polyglot` on programs you trust, in an environment you are prepared
to lose.

**Sandboxed lane (opt-in at build time).** crush-ast can instead provision the
language runtime with [`buckets`](https://github.com/nixpt/buckets) and run the
block under `bwrap` (bubblewrap) — CRUSH-20, with registry dependencies added in
CRUSH-66. It is gated behind the `sandboxed-polyglot` Cargo feature of `crush-vm`,
which is **off by default** and **not re-exported as a `crush-lang-sdk` feature**
(so there is no `--features` shortcut and no CLI flag). You enable it by building
the workspace with `--features crush-vm/sandboxed-polyglot`. It needs `bwrap`
installed and, on first use, network access to download the runtime.

What that lane does (verified against crush-ast `4e9c388`):

| | Default | Sandboxed |
|---|---|---|
| interpreter | host's `python3` / `node` / `bash` | pinned `python@3.11`, `node@20`, `bash@5` from buckets |
| host files (`/etc/hostname`) | readable | not visible (`FileNotFoundError`) |
| network | inherited | **blocked** (`allow_network: false`) |
| working directory | inherited | bound **read-write** |
| `@lang[deps]` | ignored | resolved and bound read-only |

Dependencies go in square brackets after the language tag. Registry specs are
prefixed `pypi:` or `npm:`; bare names are buckets package aliases. A bare
`numpy` is **not** assumed to mean PyPI.

<!-- check: skip needs a crush-vm build with sandboxed-polyglot (see text) -->
```crush
@python[pypi:six] -> v {
import six
v = six.__version__
}
print(v)
```

```text
1.17.0
```

The first run prints buckets' progress lines (`resolved python.org@^3.11 → …`) to
standard error while it downloads. In a default build the `[...]` part still
parses, but the dependencies are **silently ignored**: `import six` then works
only if the host's own Python happens to have `six`, and an unresolvable
`[pypi:nothing_here_xyz]` is not reported at all. An unknown package fails with
`@python block sandbox setup failed: Failed to resolve version for 'pypi:…'`.

Even the sandboxed lane is a first cut: the working directory is writable, memory
is not limited, and only `python`, `javascript` and `bash` are wired up.

## Limitations summary

- Languages: Python, JavaScript (Node), Bash. Nothing else executes.
- Value passing is JSON-only, Python/JS only, and outputs are declared with `->`.
- No shared interpreter state or cross-block function calls.
- Guest errors and timeouts abort the program; they can't be caught from Crush.
- Default execution is **unsandboxed**; the sandbox is a build-time opt-in.

## Next Steps

- **[Capability System](capabilities.md)**: what the flags do and don't confine
- **[Standard Library](stdlib.md)**
- **[CAST Specification](../cast/index.md)**
