# Chapters as Notebooks

Every chapter with Crush examples is also published as a
[crush-notebook](https://github.com/nixpt/crush-notebook) (a `.crush-nb` file):
the chapter's prose becomes Markdown cells, each Crush example a cell you can
run, edit and extend. Use the **Open as a notebook** link under a chapter's
title, or pick one from the list below.

The notebooks are generated from the guide each time the book is built, so they
always match the pages. Each example cell keeps what the guide knows about it in
its metadata: the page and line it came from, its marking (`runnable`,
`expected-failure`, `needs-host`) as a tag, and the output or error the page
shows (`meta.extra.guide`). The notebooks ship without outputs: running them is
up to you.

## Open a notebook on your machine

A `.crush-nb` file is plain JSON. To run one you need the notebook kernel; to
read one as a page, the renderer. Both are on crates.io:

```sh
cargo install --locked crush-notebook-kernel crush-notebook-render
```

**Run it with the kernel.** `crush-notebook-kernel` is an
[MCP](https://modelcontextprotocol.io) server over stdio, so any MCP client (an
editor, an agent harness) can open a notebook, run its cells, read the session's
variables and add cells of its own. Register it with your client:

```json
{
  "mcpServers": {
    "crush-notebook": { "command": "crush-notebook-kernel" }
  }
}
```

and call `notebook_open` with the file's path, then `notebook_eval_all` (or
`notebook_eval_cell` for one cell) and `notebook_list_vars`. Or drive it by hand:

```sh
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"notebook_open","arguments":{"path":"types.crush-nb"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"notebook_eval_all","arguments":{}}}' \
  | crush-notebook-kernel
```

The kernel saves each cell's result back into the file, so work on a copy if you
want to keep the original.

**Read it as a page.** `crush-notebook-render types.crush-nb` writes
`types.html` next to it: one self-contained page (no external assets) with the
cells and, if you have run the notebook, their outputs.

The kernel's other tools, the agent workflow (`@wip` cell claims, delegation)
and the cell kinds it does not run yet are described in the
[crush-notebook README](https://github.com/nixpt/crush-notebook#readme).

## What runs where

|  | Run button on the page | Notebook kernel | `crush-run` |
|---|---|---|---|
| Where it runs | your browser (crush-web, WebAssembly) | your machine | your machine |
| Granted | `print` and the VM's built-in string helpers | the same, plus `cson.parse` | whatever its flags grant (`--fs`, `--polyglot`, `--stdlib`, …) |
| Polyglot, filesystem, network, stdlib modules | refused | refused | with the matching flag |
| Between examples | every run starts fresh | cells share a session | one program per file |

So the examples marked **needs the host** are refused in the notebook too: the
kernel grants what `crush run` grants with no flags. Run those with `crush-run`
and the flags their page shows (see [Getting Started](getting-started.md)).

In a notebook, cells share a session: a cell's top-level `let`s, functions and
structs are visible to the cells after it, which makes a notebook a good place to
build on an example. The examples that are *meant* to fail (`expected-failure`)
are the one exception: each is wrapped in its own `fn main() { … }`, so a
variable an earlier cell left behind cannot hide the error the example is there
to show. Because of that wrapper, the line and column numbers in their compile
errors differ from the page's.

Every notebook is run through the kernel in the guide's CI: each runnable cell
has to finish and print what the page shows, each expected failure has to fail,
and each host-only cell has to be refused.

## The notebooks

<!-- notebooks: list -->
