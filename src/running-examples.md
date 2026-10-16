# Running the Examples

Most code blocks in this guide can be run right on the page. Each Crush example
carries one of four markings, worked out when the book is built from the same
checks that keep the guide's code honest (nothing is labelled by hand):

| Marking | What you get |
|---|---|
| **Run** · **Edit** · **Playground ↗** | The example runs in your browser. Run shows its output under the block and, where the guide prints the expected output, whether yours *matches the guide's output*. Edit turns the block into an editor (Ctrl+Enter runs it); Reset puts the original back. Playground opens it on [crushlang.org/playground](https://crushlang.org/playground/). |
| **expected to fail** | The example is *meant* to fail: a compile error, a refused capability, or a feature that is not implemented yet. Run demonstrates the failure and says whether it *fails as the guide says*. |
| **needs the host** | The example uses something the browser cannot give it; the label says what (a `@python` block, `fs.read`, the clock). Run it with `crush-run` and the flags shown on the page; see [Getting Started](getting-started.md). |
| **not runnable** | A fragment or a program that needs special setup; the label says which. |

An example the guide runs with `--polyglot` and only `@javascript` blocks also
carries **grants @javascript**: its runs are granted `polyglot.javascript`, and only
those runs (see [`@javascript` blocks](#javascript-blocks) below).

## What runs in the browser

The Run button uses **crush-web**, the WebAssembly build of the Crush VM that also
powers the [playground](https://crushlang.org/playground/). It is the same compiler
and VM as `crush-run` (the book's copy is built from crush-ast `cb655f3`, the commit
this guide is verified against), with a different set of grants:

- **Granted:** what `crush run` grants with no flags: `print` / `io.print`, the
  whole standard library (`str.*`, `math.*`, `conv.*`, `collections.*`, `json.*`,
  `regex.*`, …), and `sys.args()` (empty).
- **Standard input.** When a program calls `io.read`, an input line opens under
  the block: Enter sends one line, **End input** (or Ctrl+D) ends the input, and
  every later `io.read` returns `""`, as at the end of a file. Where the guide
  shows the input it ran an example with, the input line suggests it, and the
  output is compared with the guide's only when you typed that input.
- **`@javascript` blocks, when granted** (below).
- **Not available:** `@python` and `@bash` blocks (there is no interpreter for
  them in a browser), the filesystem, network, environment, clock, processes and
  cryptography.
- **Every run starts fresh.** Examples do not share variables, even on the same
  page. To build on one example in the next, open the chapter as a notebook (see
  [Chapters as Notebooks](notebooks.md)).
- **Limits.** One million VM instructions per run, a bounded call depth, and 8
  seconds of running time; a runaway loop is stopped, not your tab. Both cover the
  whole run, however many lines it reads, and time spent waiting for you to type
  does not count.
- **Errors keep earlier output.** When a run fails, what the program printed
  before the error is shown above it, as `crush-run` prints it.

## `@javascript` blocks

Natively, `crush-run --polyglot` runs a `@javascript` block with `node -e`. In the
browser, a block granted `polyglot.javascript` runs in JavaScript inside the same
isolated worker as the VM, and behaves like that `node -e` run:

- Crush variables go in and `->` outputs come back as JSON, as natively; every
  block starts with a fresh scope, and globals it creates are removed afterwards.
- What it prints with `console.log` (and `console.info`/`debug`,
  `process.stdout.write`) is its output, formatted as node formats it;
  `console.error`/`warn` go to its error output, which is shown if the block
  fails. `process.env` holds its inputs and `process.exit` works.
- Where the browser cannot reproduce node exactly, the block is **refused**, never
  approximated: `require` and other `process.*` properties, anything asynchronous
  (timers, promises, `async`/`await`, `fetch`), and logging values node formats
  specially (class instances, `Map`/`Set`, functions, arrays of more than six
  items, which node lays out in columns). Turn such a value into a string or JSON
  first, or run the program with `crush-run`.
- The block runs with no authority: the worker sits in a sandboxed frame with an
  opaque origin and a content security policy that allows no network, so the
  block has no access to this page, its cookies or storage, or the network.
- A block that never finishes is stopped with the run at the time limit; what the
  run printed before the stop is lost with the stopped runtime.

`@python` and `@bash` blocks stay refused: the page never grants them.

Ungranted capabilities are *refused*, not ignored: that is the
[capability system](crush/capabilities.md) working, and the page says so.

Without JavaScript the guide is a plain book: the code blocks are all there, just
without the buttons.
