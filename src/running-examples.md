# Running the Examples

Most code blocks in this guide can be run right on the page. Each Crush example
carries one of four markings, worked out when the book is built from the same
checks that keep the guide's code honest (nothing is labelled by hand):

| Marking | What you get |
|---|---|
| **Run** · **Edit** · **Playground ↗** | The example runs in your browser. Run shows its output under the block and, where the guide prints the expected output, whether yours *matches the guide's output*. Edit turns the block into an editor (Ctrl+Enter runs it); Reset puts the original back. Playground opens it on [crushlang.org/playground](https://crushlang.org/playground/). |
| **expected to fail** | The example is *meant* to fail: a compile error, a refused capability, or a feature that is not implemented yet. Run demonstrates the failure and says whether it *fails as the guide says*. |
| **needs the host** | The example uses something the browser cannot give it; the label says what (a `@python` block, `fs.read`, a standard-library module, standard input). Run it with `crush-run` and the flags shown on the page; see [Getting Started](getting-started.md). |
| **not runnable** | A fragment or a program that needs special setup; the label says which. |

## What runs in the browser

The Run button uses **crush-web**, the WebAssembly build of the Crush VM that also
powers the [playground](https://crushlang.org/playground/). It is the same compiler
and VM as `crush-run`, with a different set of grants:

- **Granted:** `print` / `io.print`, and the VM's built-in string helpers
  (`str.len`, `str.concat`, `str.contains`, `str.split`, `str.join`, `str.replace`,
  `conv.chr`, `conv.ord`).
- **Not available:** polyglot blocks (`@python`, `@javascript`, `@bash`: there is no
  host process to run them in), the filesystem, network, environment, clock and
  processes, the standard-library modules (`math.*`, `conv.to_int`, `json.*`, …),
  and standard input (`io.read` returns `""`).
- **Every run starts fresh.** Examples do not share variables, even on the same
  page. To build on one example in the next, open the chapter as a notebook (see
  [Chapters as Notebooks](notebooks.md)).
- **Limits.** One million VM instructions per run, a bounded call depth, and an
  8-second wall-clock limit; a runaway loop is stopped, not your tab.
  Output printed before a run-time error is not shown.

Ungranted capabilities are *refused*, not ignored: that is the
[capability system](crush/capabilities.md) working, and the page says so.

Without JavaScript the guide is a plain book: the code blocks are all there, just
without the buttons.
