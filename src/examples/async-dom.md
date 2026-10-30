# Polyglot Pipeline

The same data, handled by the language best suited to each step, with Crush
variables as the glue. This replaces an earlier "Async LLM Dashboard" page whose
`dom.*`, `seahorse` and `async`/`await` calls do not run in the current
toolchain.

Run it with `crush run --polyglot poly.crush` (needs `python3`, `node` and `bash`
on `PATH`; `crush doctor` checks).

> Verified against crush-ast `aa07413` (2026-10-16).

<!-- check: flags --polyglot -->
```crush
// Three languages, one program. Values flow through Crush variables.
let numbers = [3, 1, 4, 1, 5, 9, 2, 6]

@python -> mean {
import statistics
mean = statistics.mean(numbers)
}

@javascript -> spread {
const spread = Math.max(...numbers) - Math.min(...numbers)
}

@python -> line {
line = f"mean={mean} spread={spread}"
}
print(line)

@bash {
echo "bash: $(echo done)"
}
print("")
```

<!-- check: output -->
```text
mean=3.875 spread=8
bash: done
```

**What this shows:**

- `@python -> mean`: the block reads the Crush variable `numbers` (inputs are
  automatic) and declares `mean` as its output, which becomes a Crush variable
- `@javascript -> spread`: the same protocol; `spread` comes back as a number
- the second `@python` block reads both earlier outputs, because they are Crush
  variables now
- `@bash`: only its printed output comes back. It does **not** see Crush
  variables today (crush-ast [#255](https://github.com/nixpt/crush-ast/issues/255)),
  which is why the formatting is done in Python
- block output is trimmed and has no trailing newline, which is why `print("")`
  is used to finish the line
- all three run as ordinary subprocesses with your user's authority — see
  [Polyglot Programming](../crush/polyglot.md#sandbox-and-authority)
