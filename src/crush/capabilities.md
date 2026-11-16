# Capability System

> Verified against crush-ast `7f3fef31` (main, 2026-11-16).

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
| `--net` | `net.http_get`, `net.http_post`, `net.http_put`, `net.http_delete`, `net.http_request` (**HTTP only**) |
| `--tcp` | raw TCP **client** sockets: `tcp.connect`, `tcp.tls_wrap`, and `tcp.send`, `tcp.recv`, `tcp.close`, `tcp.ping` on the connections you hold; see [Raw sockets](#raw-sockets-tcp) |
| `--tcp-listen` | raw TCP **server** sockets: `tcp.listen`, `tcp.accept`, and the same `send`/`recv`/`close`/`ping`; does not allow `tcp.connect` |
| `--ui` | `ui.*`, only with `crush gui run`; see [Windows](gui.md) |
| `--process` | `process.exec` |
| `--crypto` | `crypto.sha256`, `crypto.random` |
| `--db PATH` | `db.query`, `db.execute` on that SQLite file |
| `--graphics` | `graphics.canvas/rect/circle/text/to_svg` |
| `--bus` | `message_bus.publish/subscribe/recv` |
| `--task` | `task.start/stop/list` |
| `--akg` | `akg.write/read/search` |
| `--polyglot` | `@python { }`, `@javascript { }`, `@bash { }` blocks — see [Polyglot](polyglot.md) |

`crush-run caps` prints the list for your build. Some groups (`--db`, `--graphics`,
`--gpu`) are Cargo features of `crush-lang-sdk` that a default build leaves out;
the standard library, the HTTP client (`net.*`, since 0.9.0) and the raw sockets
(`tcp.*`) are default features, which only compiles them in: a program that uses
them is still refused until you pass the flag.

The old HTTP names `http.get`, `http.post`, `http.put`, `http.delete` and
`http.request` are refused by name, with the replacement. This run is refused
before anything executes, with or without `--net`:

<!-- check: runfail was renamed to net.http_get -->
```crush
let r = http.get("http://example.com/")
print(r)
```

```text
[capabilities] block.crush needs capabilities this run does not grant; nothing was run:
  http.get was renamed to net.http_get (grant it with --net)
```

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
let r = process.exec("echo", "hi")
print(r.exit_code)
print(str.trim(r.stdout))
```

<!-- check: output -->
```text
null
true
0
hi
```

- `env.get(name)` → string, or `null` if unset.
- `time.now()` Unix seconds; `time.now_ms()`; `time.now_iso()`; `time.sleep(ms)`
  (bounded by the wall-clock budget, `--max-wall-ms`).
- `process.exec(cmd, args)` — exactly **two** arguments (the command and one
  argument string) — returns a map `{exit_code, stdout, stderr}` (crush-ast
  CRUSH-242; before 0.11 it was a JSON string). A command that cannot start is not
  an error: `exit_code` is `-1` and `stderr` says why.
- `net.http_get(url)` / `net.http_post(url, body)` — response body as a string;
  size capped by `--net-max-response-bytes` (default 1 MiB). Each `net.*` verb takes
  an optional last argument `{timeout_ms: N}`; a request that takes longer fails
  with a catchable error (`… timed out after N ms`). `net.http_request(method, url,
  body, headers)` returns `{status, reason, headers, body}`, with the response
  header names lower-cased (crush-ast #509).

<!-- check: skip needs a local HTTP server -->
```crush
let r = net.http_request("GET", "http://127.0.0.1:47125/hi.txt", "", {})
print(r.status)
print(r.headers["content-type"])
try {
    print(net.http_get("http://127.0.0.1:47126/", {timeout_ms: 300}))
} catch e {
    print(e)
}
```

```text
200
text/plain
error(net.http_get: net.http_get http://127.0.0.1:47126/: timed out after 300 ms)
```

(Run by hand at the pinned commit, with `python3 -m http.server 47125` serving a
`hi.txt` and a listener on port 47126 that accepts and never answers.)
- `crypto.sha256(data)`, `crypto.random(n)` (base64, `n ≤ 4096`).

### Raw sockets (`tcp.*`)

Since 0.9.0 a program can open TCP connections directly. `--net` is HTTP only and
does **not** grant these; the socket flags are separate, and the server flag is a
stronger grant than the client flag because it makes the program reachable from
other hosts:

| Flag | Lets the program |
|---|---|
| `--tcp` | `tcp.connect(uri)` outbound; `tcp.tls_wrap(conn)` upgrades a connection to TLS |
| `--tcp-listen` | `tcp.listen(uri)` and `tcp.accept(listener)`; it does not allow `tcp.connect` |
| either | `tcp.send(conn, text)`, `tcp.recv(conn)`, `tcp.close(conn)`, `tcp.ping(conn)` on a connection id it already holds |

A URI is `tcp://IP:PORT` with a literal IP address (no host names). `tcp.listen`
and `tcp.connect` return an integer id; `tcp.accept` blocks until a client
connects. `tcp.send` takes text (or bytes) and returns the byte count. `tcp.recv`
returns what one read delivered, at most 16 KiB, as text; an incomplete UTF-8
character at the end is held back and returned by the next call, so a message can
arrive over several calls: loop until you have all of it (a delimiter, a length, or
`""`, which `tcp.recv` returns only at end of stream). `tcp.recv` and `tcp.accept`
take an optional `{timeout_ms: N}`; a timeout is a catchable error, and a timed-out
`tcp.recv` loses nothing (crush-ast #512). This program is both ends of a conversation, so it needs both
flags (the connect is queued by the kernel before `accept` takes it):

<!-- check: flags --tcp --tcp-listen -->
```crush
let srv = tcp.listen("tcp://127.0.0.1:47123")
let c = tcp.connect("tcp://127.0.0.1:47123")
let s = tcp.accept(srv)
tcp.send(c, "ping")
print(tcp.recv(s))
tcp.send(s, "pong")
print(tcp.recv(c))
tcp.close(c)
tcp.close(s)
```

<!-- check: output -->
```text
ping
pong
```

A `tcp.recv` that times out can be caught, and the data that arrives later is read
by the next call:

<!-- check: flags --tcp --tcp-listen -->
```crush
let srv = tcp.listen("tcp://127.0.0.1:47124")
let c = tcp.connect("tcp://127.0.0.1:47124")
let s = tcp.accept(srv)
try {
    print(tcp.recv(s, {timeout_ms: 100}))
} catch e {
    print("caught: " + e)
}
tcp.send(c, "late")
print(tcp.recv(s))
tcp.close(c)
print(tcp.recv(s) == "")
tcp.close(s)
```

<!-- check: output -->
```text
caught: error(tcp.recv: tcp.recv: timed out after 100 ms)
late
true
```

(The capability name appears twice in that message; it is crush-ast's text as it
stands.)

Granting only `--tcp` is refused, naming what is missing:

```text
[capabilities] tcp.crush needs capabilities this run does not grant; nothing was run:
  --tcp-listen: tcp.accept, tcp.listen
```

A host capability that fails (missing file, refused connection, path escape)
raises `[runtime] <name>: <reason>`, for example `[runtime] fs.read: fs.read
missing.txt: No such file or directory (os error 2)`. Inside
[`try`/`catch`](control_flow.md#what-catch-catches) it is caught like any other
fault; outside one it ends the program.

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

<!-- check: error -->
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
| instructions | 1,000,000 | `--max-steps N`, or `--max-steps unlimited` |
| stack slots | 4,096 | `--max-stack` |
| output bytes | 1 MiB | `--max-output` |
| call depth | 256 | `--max-call-depth` |
| wall-clock time for the whole run | 30,000 ms | `--max-wall-ms N`, or `--max-wall-ms unlimited` for a long-lived program such as a server (crush-ast #510) |

The wall-clock budget covers the whole run, computation included, so lifting the
step limit does not make a runaway loop run forever:

<!-- check: runfail wall-clock quota exceeded (200ms) -->
<!-- check: flags --max-steps unlimited --max-wall-ms 200 -->
```crush
let i = 0
while true { i = i + 1 }
```

A blocking capability such as `time.sleep` gets what is left of the budget.
`--max-wall-ms 0` is a zero budget, not "no limit": the run stops at the first
clock check (the VM looks at the clock every 1,024 instructions) or the first
blocking call, so only a very short program still finishes.

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
and [CASM structure](../casm/structure.md). For assembly text (`.cvms`) run with `crush-run`,
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
