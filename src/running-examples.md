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
- **Not available:** polyglot blocks (`@python`, `@javascript`, `@bash`: there is no
  host process to run them in), the filesystem, network, environment, clock,
  processes and cryptography.
- **Every run starts fresh.** Examples do not share variables, even on the same
  page. To build on one example in the next, open the chapter as a notebook (see
  [Chapters as Notebooks](notebooks.md)).
- **Limits.** One million VM instructions per run, a bounded call depth, and 8
  seconds of running time; a runaway loop is stopped, not your tab. Both cover the
  whole run, however many lines it reads, and time spent waiting for you to type
  does not count.
- **Errors keep earlier output.** When a run fails, what the program printed
  before the error is shown above it, as `crush-run` prints it.

Ungranted capabilities are *refused*, not ignored: that is the
[capability system](crush/capabilities.md) working, and the page says so.

Without JavaScript the guide is a plain book: the code blocks are all there, just
without the buttons.
