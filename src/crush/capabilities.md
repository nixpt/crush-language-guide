# Capability System

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

`io.read` reads from standard input:

<!-- check: stdin Ada -->
<!-- check: compile -->
```crush
let name = io.read()
io.print("Hello, " + name)
```

## Enabling more capabilities

With the CLI, each *group* of capabilities is switched on by a flag on
`crush-run run` (or `crush run`). Anything not switched on is simply **not
registered**, and calling it fails at run time with `unknown capability`:

| Flag | Capabilities enabled |
|---|---|
| `--stdlib` | `str.*`, `math.*`, `conv.*`, `collections.*`, `json.*`, `path.*`, `regex.*`, `bytes.*`, `buffer.*`, `binary.*`, `result.*`, `time.format/parse`, `env.os/arch`, `system.*` — pure computation, see [Standard Library](stdlib.md) |
| `--fs` | `fs.read`, `fs.write`, `fs.exists`, `fs.list`, `text.head/tail/wc/cut/grep` |
| `--env` | `env.get` |
| `--time` | `time.now`, `time.now_ms`, `time.now_iso`, `time.elapsed`, `time.sleep` |
| `--net` | `net.http_get`, `net.http_post` |
| `--process` | `process.exec` |
| `--crypto` | `crypto.sha256`, `crypto.random` |
| `--db PATH` | `db.query`, `db.execute` on that SQLite file |
| `--graphics` | `graphics.canvas/rect/circle/text/to_svg` |
| `--bus` | `message_bus.publish/subscribe/recv` |
| `--task` | `task.start/stop/list` |
| `--akg` | `akg.write/read/search` |
| `--polyglot` | `@python { }`, `@javascript { }`, `@bash { }` blocks — see [Polyglot](polyglot.md) |

`crush-run caps` prints the list for your build. Some groups (`--stdlib`,
`--net`, `--db`, `--graphics`) are Cargo features of `crush-lang-sdk`; if your binary was
built without one, its flag prints `warning: --… requires the '…' feature (not
enabled in this build)` and the group stays absent. Note that **`stdlib` is off by
default** (crush-ast CRUSH-113); build with `--features stdlib`.

Without the flag, the call fails:

<!-- check: runfail unknown capability: fs.read -->
```crush
print(fs.read("data.txt"))
```

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
| `fs.write` | `path, data` | nothing — **see the note below** |

> **Known bug — `fs.write`.** It declares no return value, and the compiler emits
> a `pop` after a call used as a statement, so any program that calls it ends with
> `[runtime] stack underflow` (the write itself may still happen). Treat `fs.write`
> as not usable from `.crush` source until this is fixed. Capabilities that
> return nothing share the problem; `io.print` and `time.sleep` are unaffected.

<!-- check: nyi GAP-VOID-CAP-STATEMENT -->
<!-- check: flags --fs -->
```crush
fs.write("out.txt", "hello")
print(fs.read("out.txt"))
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

Output is buffered: if a program fails at run time, anything it printed before
the failure is **not** shown.

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
exist in the runtime: `io.eprint`, `fs.delete`, `sys.exec`, `sys.env`, `sys.args`,
`sys.exit`, `net.get`, `net.post`, `net.http`, `type.of`, `console.print`,
`array.length`, `map.keys`, `map.has_key`, and `module.load` (what `import`
lowers to — crush-ast **CRUSH-110**). Use the replacements above
(`env.get`, `net.http_get`, `conv.type_of`, `len`, …).

## Next Steps

- **[Standard Library](stdlib.md)**
- **[Polyglot Programming](polyglot.md)**
