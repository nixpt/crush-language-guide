# Debugging

> Verified against crush-ast `bad81048` (v0.9.0, 2026-10-31).

`crush debug FILE` (the same program as `crush-debug FILE`) runs a program under a
debugger: breakpoints by source line, single-stepping, watchpoints on a variable, and
printing values. It reads commands from standard input, so it works at a terminal and
in a pipe. It is in the prebuilt tarball and in `cargo install crush-lang-sdk`.

## Debugging is a grant

Like every other authority in Crush, looking inside a running program is switched on
by a flag, and **nothing is granted by default**:

| Flag | Lets the debugger |
|---|---|
| `--step` | run the program and `break`, `step`, `next`, `finish`, `continue`, `watch` |
| `--inspect` | (needs `--step`) show variable values in full |
| `--inspect=redacted` | (needs `--step`) show a value's type and a per-session hash instead, so you can tell whether two values are equal without seeing them |
| `--break FILE:LINE` | set a breakpoint before the first command (repeatable; `LINE` alone works) |

The program's own capabilities are granted with the same flags as `crush run`
(`--fs`, `--net`, `--polyglot`, …). Without `--step`, every command that would run the
program is refused, and without `--inspect` values show as `<hidden>`:

```text
$ printf 'break 3\ncontinue\nquit\n' | crush debug d.crush
cru-s-debugger> refused: `break` needs the `debug.step` grant (pass --step)
cru-s-debugger> refused: `continue` needs the `debug.step` grant (pass --step)
```

## A session

Take this program, saved as `d.crush`:

```crush
let total = 0
for i in 0..3 {
    total = total + i
}
print(total)
```

<!-- check: output -->
```text
3
```

Stop on line 3 and look at the variables. The commands are typed
after the prompt (shown here as a script piped in):

```text
$ printf 'break 3\ncontinue\nprint total\nlocals\nquit\n' | crush debug d.crush --step --inspect
cru-s-debugger> breakpoint #0 set at d.crush:3
cru-s-debugger> hit breakpoint #0 at d.crush:3 in main
     3 |     total = total + i
cru-s-debugger> total = 0
cru-s-debugger> total (slot 0) = 0
i (slot 1) = 0
__end_0 (slot 2) = 3
cru-s-debugger> bye.
```

The `__end_0` slot is the compiler's copy of the loop bound; it shows that the debugger
reports the real locals of the compiled function.

With `--inspect=redacted` the same `print total` gives a type and a hash:

```text
cru-s-debugger> total = <int #95e76d5b42ff8213>
```

## Commands

| Command | Does |
|---|---|
| `break FILE:LINE` or `break LINE` | set a breakpoint (`delete ID` removes it, `list` shows them) |
| `step` / `s` | one instruction, or one source line; enters calls |
| `next` / `n` | step over: run a call to completion |
| `stepi` / `nexti` | the same, always by instruction |
| `finish` / `fin` | step out: run until this function returns |
| `continue` / `c` | run until a breakpoint, a watchpoint, or the end |
| `watch NAME` | stop when that local changes (`unwatch ID` removes it) |
| `print NAME` or `p NAME` | print a local, or a field with `NAME.field` |
| `locals` / `vars` | print every assigned local of the current frame |
| `status` / `info` | show the VM state |
| `quit` / `q` | leave |

## For editors and agents: `--message-format json`

With `--message-format json` there is no prompt and prose: each event the debugger
reports is one JSON object per line on standard output. Stopping at the same
breakpoint produces:

```json
{"event":"started","file":"d.crush","visibility":"Full"}
{"command":"break 3","event":"message","text":"breakpoint #0 set at d.crush:3"}
{"event":"stopped","file":"d.crush","frames":[{"depth":1,"file":"d.crush","function":"main","ip":48,"line":3,"locals":[{"name":"total","slot":0,"value":{"text":"0","type":"int"}},{"name":"i","slot":1,"value":{"text":"0","type":"int"}},{"name":"__end_0","slot":2,"value":{"text":"3","type":"int"}}]}],"function":"main","line":3,"reason":{"id":0,"kind":"breakpoint"},"source":"    total = total + i"}
{"command":"print total","event":"message","text":"total = 0"}
```

so a tool can follow the program without parsing the text form.
