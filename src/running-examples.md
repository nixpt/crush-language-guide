# Running the Examples

Most code blocks in this guide can be run right on the page. Each Crush example
carries one of four markings, worked out when the book is built from the same
checks that keep the guide's code honest (nothing is labelled by hand):

| Marking | What you get |
|---|---|
| **Run** · **Edit** · **Playground ↗** | The example runs in your browser. Run shows its output under the block and, where the guide prints the expected output, whether yours *matches the guide's output*. Edit turns the block into an editor (Ctrl+Enter runs it); Reset puts the original back. Playground opens it on [crushlang.org/playground](https://crushlang.org/playground/). |
| **expected to fail** | The example is *meant* to fail: a compile error, a refused capability, or a feature that is not implemented yet. Run demonstrates the failure and says whether it *fails as the guide says*. |
| **needs the host** | The example uses something the browser cannot give it; the label says what (a `@bash` block, `fs.read`, an `@python` block that reads files). Run it with `crush-run` and the flags shown on the page; see [Getting Started](getting-started.md). |
| **not runnable** | A fragment or a program that needs special setup; the label says which. |

An example whose `crush-run` flags the browser can honour carries a **grants**
label saying what its runs are granted, and nothing else is: **@javascript** and
**@python** (`--polyglot` with only `@javascript` / `@python` blocks), **the
clock** (`--time`), **the environment** (`--env`) or **the filesystem** (`--fs`).
Edited code keeps the example's grants.

## What runs in the browser

The Run button uses **crush-web**, the WebAssembly build of the Crush VM that also
powers the [playground](https://crushlang.org/playground/). It is the same compiler
and VM as `crush-run` (the book's copy is built from crush-ast `d04bc60a`, the commit this guide is
verified against), and it grants the same way:

- **Always granted:** what `crush run` grants with no flags: `print` /
  `io.print`, the whole standard library (`str.*`, `math.*`, `conv.*`,
  `collections.*`, `json.*`, `regex.*`, …), and `sys.args()` (empty).
- **Standard input.** When a program calls `io.read`, an input line opens under
  the block: Enter sends one line, **End input** (or Ctrl+D) ends the input, and
  every later `io.read` returns `""`, as at the end of a file. Where the guide
  shows the input it ran an example with, the input line suggests it, and the
  output is compared with the guide's only when you typed that input.
- **Granted per example** (the **grants** label): `@javascript` blocks (below);
  the clock, `time.*`, read from your browser (`time.now_iso` has millisecond
  precision; `time.sleep` waits and counts as running time); and the environment,
  `env.*`, which in a browser is empty: `env.get` returns `null` and `env.all()`
  is `{}`, as under `env -i crush-run --env`.
- **Never available:** `@python` and `@bash` blocks, the filesystem, the
  network, processes and cryptography. An example that prints facts about the
  machine (`env.os()`, `env.arch()`) is labelled as needing the host too: in a
  browser they describe the browser (`wasm32`), so its output could not match
  the page.
- **Refused before running.** Like `crush-run`, the runtime works out every
  capability a program can reach and, if one is not granted, refuses the whole
  run before anything prints, naming the `crush-run` flag that would grant it.
- **Every run starts fresh.** Examples do not share variables, even on the same
  page. To build on one example in the next, open the chapter as a notebook (see
  [Chapters as Notebooks](notebooks.md)).
- **Limits.** One million VM instructions per run, a bounded call depth, and 8
  seconds of running time; a runaway loop is stopped, not your tab. Both cover the
  whole run, however many lines it reads, and time spent waiting for you to type
  does not count.
- **Errors keep earlier output.** When a run fails, what the program printed
  before the error is shown above it, as `crush-run` prints it. Errors read
  `compile error: …` / `runtime error: …` where `crush-run` prints `[compile] …` /
  `[runtime] …`; the messages are the same.

## `@javascript` blocks

Natively, `crush-run --polyglot` runs a `@javascript` block with `node -e`. In the
browser, a block granted `polyglot.javascript` runs in JavaScript inside the same
isolated worker as the VM, and behaves like that `node -e` run:

- Crush variables go in and `->` outputs come back as JSON, as natively; every
  block starts with a fresh scope, and globals it creates are removed afterwards.
- It runs as node runs a script: top-level `await`, promises, `async` functions,
  `queueMicrotask` and timers (`setTimeout`, `setInterval`, `setImmediate`) all
  work, and the block finishes when nothing is left to run, in node's order. An
  uncaught exception (also in a timer or a promise), an unhandled rejection, or
  `process.exit` / `process.exitCode` with a non-zero status fails it, as it makes
  node exit non-zero.
- What it prints with `console.log` (and `info`/`debug`/`dir`/`group`/`count`,
  `process.stdout.write`) is its output, formatted by node's own `util.inspect`
  and `util.format` (`Map(1) { 'a' => 1 }`, class instances, long arrays in
  columns, ...), so it reads exactly as node prints it; `require('util')` is that
  module. `console.error`/`warn`/`assert` go to its error output, which is shown
  if the block fails. `process.env` holds its inputs.
- Where only node can answer, the block is **refused**, never approximated: node
  modules other than `util`, the network (`fetch`, `XMLHttpRequest`,
  `WebSocket`), the process's own details (`process.argv`, `platform`,
  `nextTick`, ...), and printing a Promise or a timer object (node shows their
  internals). Run such a program with `crush-run --polyglot`.
- The block runs with no authority: the worker sits in a sandboxed frame with an
  opaque origin and a content security policy that allows no network, so the
  block has no access to this page, its cookies or storage, or the network.
- A block that never finishes is stopped with the run at the time limit; what the
  run printed before the stop is lost with the stopped runtime.

## `@python` blocks

Natively, `crush-run --polyglot` runs a `@python` block with `python3 -c`. In the
browser, a block granted `polyglot.python` runs in [Pyodide](https://pyodide.org)
314.0.7, which is CPython 3.14 (the Python this guide's examples were checked
with) compiled to WebAssembly, inside the same isolated worker as the VM, and
behaves like that `python3 -c` run:

- **Downloaded on first use.** The first time you run a `@python` example on a
  page, the page downloads Pyodide from its CDN (about 6.3 MB compressed) and
  checks every file against the sha256 the guide pins
  ([`play/pyodide.json`](play/pyodide.json)) before using it. Pages without a
  `@python` run never download it, and a page loads it once however many examples
  you run.
- Crush variables go in and `->` outputs come back as JSON, as natively. Every
  block starts in a fresh `__main__`; modules it imports and changes it makes to
  `os.environ` are undone afterwards.
- What it prints is its output; standard input is empty (natively it is
  `/dev/null`, so `input()` raises `EOFError`). A block that raises fails the run
  with the traceback `python3` prints, at the block's `.crush` line.
- Where only the host can answer, the block is **refused**, never answered
  differently: opening files and `os` file and directory calls, running processes
  (`subprocess`, `os.system`, ...) and the network (`socket`, `urllib.request`,
  `http.client`, ...). Pyodide's own bridges to JavaScript (`import js`,
  `import pyodide`) do not exist, as in `python3`. Packages (`pypi:`) need the
  host. Run such a program with `crush-run --polyglot`.
- The block has the same lack of authority as a `@javascript` block, and a block
  that never finishes is stopped at the time limit the same way; the next
  `@python` run loads Python again from the downloaded files.

## The filesystem

Natively, `crush-run --fs` works on real files under `--fs-root`, and the guide's
`--fs` examples are checked in an empty one. In the browser, a run granted the
filesystem gets an **empty directory of its own, in memory**, which disappears
when the run ends. The `fs.*` and `text.*` capabilities are the same code as
natively, over that directory instead of the disk. They give the same results
and the same errors (`No such file or directory (os error 2)`), and they keep
the same sandbox: a path that leaves the directory, with `..` or as an absolute
path, is refused. Nothing is saved between runs, and nothing on your computer is
reachable.

## Why not `@bash`, processes or the network

- **`@bash`** has no browser equivalent, and `crush-run` never sandboxes it either.
- **Processes** (`process.exec`) run programs on the host, and **the network**
  (`net.*`) reaches the host's network; a browser page has neither to give.


Ungranted capabilities are *refused*, not ignored: that is the
[capability system](crush/capabilities.md) working, and the page says so.

Without JavaScript the guide is a plain book: the code blocks are all there, just
without the buttons.
