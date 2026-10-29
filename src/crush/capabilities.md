# Capability System

> Verified against crush-ast `b1791d8e` (2026-10-29).

Crush programs can't touch the outside world directly. Every interaction with the
host — printing, reading a file, making an HTTP request, spawning a process,
running another language — is a **capability call**, and a capability only exists
if the host that is running the program has explicitly turned it on. There is no
ambient authority.

> **Status: alpha.** The model below is real and enforced, but the set of
> capabilities is small and the permission granularity is coarse (on/off per
> group, with a directory root for the filesystem). Read
> [What is not enforced](#what-is-not-enforced) before relying on it for
> isolation.

## Calling a capability

A capability call looks like an ordinary dotted function call — **no `@` prefix**:

```crush
io.print("Hello, ", "Crush")
let upper = str.concat("a", "b")
print(upper)
```

<!-- check: output -->
```text
Hello, Crush
ab
```

`io.print(a, b, ...)` takes any number of arguments, joins them with no
separator, and appends a newline. The built-in `print(x)` takes exactly one.
(The `@` sigil exists in Crush, but it introduces polyglot blocks and
annotations, never capability calls — see [Syntax](syntax.md#language-blocks).)

## Always available

These work with no flags:

| Capability | Description |
|---|---|
| `io.print(...)` | print to stdout |
| `io.read()` | read one line from stdin (empty string at EOF) |
| `str.concat(...)`, `str.len(s)` | concatenate / byte length |
| `conv.chr(n)`, `conv.ord(s)` | codepoint ↔ one-character string |

```crush
print(conv.chr(65))
print(conv.ord("A"))
print(str.len("héllo"))
```

<!-- check: output -->
```text
A
65
6
```

`io.read` reads a line from standard input. On this page, Run asks you for each
line; type `Ada` to get the output below:

<!-- check: stdin Ada -->
```crush
let name = io.read()
io.print("Hello, " + name)
```

<!-- check: output -->
```text
Hello, Ada
```

## Enabling more capabilities

With the CLI, each *group* of capabilities is switched on by a flag on
`crush-run run` (or `crush run`). Anything not switched on is simply **not
registered**. Before running anything, `crush-run` works out every capability the
compiled program can reach and refuses the whole run if one isn't granted, listing
the flag that would grant each:

| Flag | Capabilities enabled |
|---|---|
| (none: on by default) | the standard library: `str.*`, `math.*`, `conv.*`, `collections.*`, `json.*`, `path.*`, `regex.*`, `bytes.*`, `buffer.*`, `binary.*`, `result.*`, `time.format/parse`, `env.os/arch`, `system.*`, plus `sys.args()` / `sys.exit(code)`; pure computation, see [Standard Library](stdlib.md). `--no-stdlib` removes it |
| `--fs` | `fs.read`, `fs.write`, `fs.exists`, `fs.list`, `fs.ls/cat/pwd/cd/mkdir/rm/cp/mv/touch/find`, `text.head/tail/wc/cut/grep` |
| `--env` | `env.get`, `env.all`, `env.home_dir` |
| `--time` | `time.now`, `time.now_ms`, `time.now_iso`, `time.elapsed`, `time.sleep`, `async.sleep` |
| `--net` | `net.http_get`, `net.http_post`, `net.http_put`, `net.http_delete`, `net.http_request` |
| `--process` | `process.exec` |
| `--crypto` | `crypto.sha256`, `crypto.random` |
| `--db PATH` | `db.query`, `db.execute` on that SQLite file |
| `--graphics` | `graphics.canvas/rect/circle/text/to_svg` |
| `--bus` | `message_bus.publish/subscribe/recv` |
| `--task` | `task.start/stop/list` |
| `--akg` | `akg.write/read/search` |
| `--polyglot` | `@python { }`, `@javascript { }`, `@bash { }` blocks — see [Polyglot](polyglot.md) |

`crush-run caps` prints the list for your build. Some groups (`--net`, `--db`,
`--graphics`, `--gpu`) are Cargo features of `crush-lang-sdk` that a default build
leaves out; the standard library is a default feature.

Without the flag, nothing runs, not even the first line:

<!-- check: runfail fs.read -->
```crush
print("first line")
print(fs.read("data.txt"))
```

```text
[capabilities] block.crush needs capabilities this run does not grant; nothing was run:
  --fs: fs.read
```

`crush-run caps FILE` answers the same question without running: what the
program can use, and which flag grants each.

With it, and with the filesystem confined to a directory:

<!-- check: runfail path escapes sandbox root -->
<!-- check: flags --fs -->
```crush
print(fs.read("../outside.txt"))
```

Filesystem paths must be relative and resolve **inside** `--fs-root` (default `.`):
absolute paths and `..` escapes are rejected. This is the one place the permission
has a scope.

### Filesystem

<!-- check: flags --fs -->
```crush
print(fs.exists("missing.txt"))
```

<!-- check: output -->
```text
0
```

| Capability | Arguments | Returns |
|---|---|---|
| `fs.read` | `path` | file contents (string) |
| `fs.exists` | `path` | `1` / `0` |
| `fs.list` | `dir` | array of names |
| `fs.write` | `path, data` | nothing |
| `fs.mkdir` | `path` | nothing |

<!-- check: flags --fs -->
```crush
fs.write("out.txt", "hello")
print(fs.read("out.txt"))
fs.mkdir("sub")
fs.write("sub/a.txt", "a")
print(fs.list("sub"))
```

<!-- check: output -->
```text
hello
[a.txt]
```

### Environment, time, processes, network

<!-- check: flags --env --time --process -->
```crush
print(env.get("CRUSH_GUIDE_DEMO_UNSET"))
print(time.now() > 0)
print(process.exec("echo", "hi"))
```

<!-- check: output -->
```text
null
true
{"exit_code":0,"stderr":"","stdout":"hi\n"}
```

- `env.get(name)` → string, or `null` if unset.
- `time.now()` Unix seconds; `time.now_ms()`; `time.now_iso()`; `time.sleep(ms)`
  (bounded by the wall-clock quota).
- `process.exec(cmd, args)` — exactly **two** arguments (the command and one
  argument string) — returns a JSON string with `exit_code`, `stdout`, `stderr`.
- `net.http_get(url)` / `net.http_post(url, body)` — response body as a string;
  size capped by `--net-max-response-bytes` (default 1 MiB).
- `crypto.sha256(data)`, `crypto.random(n)` (base64, `n ≤ 4096`).

A host capability that fails (missing file, refused connection, path escape)
aborts the program with `[runtime] unknown capability: <name>: <reason>` — the
"unknown capability" wording is misleading there, and the error is not
catchable by [`try`/`catch`](control_flow.md#what-catch-does-not-catch).

## Declaring what a program uses: `@capabilities`

A program can say up front which capabilities it may use beyond the ambient,
effect-free built-ins (`io.print`, `str.*`, arrays, the standard library):

<!-- check: flags --time -->
```crush
@capabilities [time.now_ms]
let t = time.now_ms()
print(t > 0)
```

<!-- check: output -->
```text
true
```

Entries can be exact names (`fs.cat`), families (`fs`, `fs.*`) or scoped names
(`fs.read:/var/log`). Using anything else is a compile error, so a reviewer only
has to read that one line to know what the program can touch:

<!-- check: runfail not declared in @capabilities: env.get -->
```crush
@capabilities [time.now_ms]
print(env.get("HOME"))
```

```text
[compile] the program uses a capability not declared in @capabilities: env.get
  add it to @capabilities, or stop using it
```

The declaration limits what the program *may* use; the run's flags still decide
what it *gets*. `crush-run caps prog.crush` prints both:

```text
prog.crush
  declares: time.now_ms
  needs these grants to run:
    --time: time.now_ms
  also uses (ambient): io.print
```

A program without `@capabilities` compiles as before.

> **Known bug ([crush-ast #258](https://github.com/nixpt/crush-ast/issues/258)).**
> The check runs when `crush-run run` / `crush run` compiles a `.crush` file. `crushc`
> and `crush build` don't apply it yet, and the `.cvm1` they write drops the
> declaration, so review the source, not just the bytecode. (The
[awesome-crush](https://github.com/nixpt/awesome-crush) `agents/log-triage`
entry walks through this with an agent-written tool.)

## Resource limits

Separately from capabilities, the VM enforces **quotas**; exceeding one ends the
program with a `[runtime]` error:

| Quota | Default | CLI flag |
|---|---|---|
| instructions | 1,000,000 | `--max-steps` |
| stack slots | 4,096 | `--max-stack` |
| output bytes | 1 MiB | `--max-output` |
| call depth | 256 | `--max-call-depth` |
| wall-clock per polyglot subprocess | 30,000 ms | (set via `Quotas::max_wall_time_ms` when embedding) |

Output printed before a run-time failure is kept: the program's earlier lines
appear, then the `[runtime]` error on standard error.

## Embedding: declaring permissions

When you embed the VM from Rust you choose the capability set yourself
(`crush_lang_sdk::HostCaps`, `Runtime`, `ProgramBuilder`), and a CASM program
names the capabilities it is allowed to call in its manifest — a list of names:

```json
{
  "version": "1.0",
  "manifest": { "permissions": ["io.print"] },
  "functions": { "main": { "params": [], "locals": [], "body": [] } }
}
```

A capability call whose name is not both **registered** by the host and **listed**
in the program's permissions is refused. See [Getting Started](../getting-started.md)
and [CASM structure](../casm/structure.md). For `.casm` text run with `crush-run`,
`--cap NAME` adds names to that list.

There is no path or URL scoping in the manifest (`"fs.read": ["./data"]` is not a
thing): scoping today is the host's job — e.g. `--fs-root`.

## What is not enforced

Be honest with yourself about the isolation you actually get:

- **Polyglot blocks run outside this capability model.** With `--polyglot`,
  `@python { }` / `@javascript { }` / `@bash { }` blocks run as ordinary
  subprocesses with the **host process's authority**: a Python block can read any
  file the user can. The `fs`/`net`/`process` flags above do not constrain it. An
  optional build-time sandbox (bubblewrap, via `buckets`) exists but is **off by
  default** — see [Polyglot](polyglot.md#sandbox-and-authority).
- Quotas bound instructions and (for polyglot) wall-clock time, not memory.
- `process.exec` runs any command the user can run; only enable it for programs
  you trust.

## Not implemented

The following capabilities appeared in earlier revisions of this guide but do not
exist in the runtime: `io.eprint`, `fs.delete`, `sys.exec`, `sys.env`,
`net.get`, `net.post`, `net.http`, `type.of`, `console.print`,
`array.length`, `map.keys`, `map.has_key`, and `module.load` (what `import`
lowers to — crush-ast **CRUSH-110**). Use the replacements above
(`fs.rm`, `env.get`, `net.http_get`, `conv.type_of`, `len`, …). `sys.args()` and
`sys.exit(code)` do exist now (ambient).

## Next Steps

- **[Standard Library](stdlib.md)**
- **[Polyglot Programming](polyglot.md)**
